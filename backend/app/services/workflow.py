"""Idempotent incident-workflow preparation after analysis completes."""

from __future__ import annotations

import logging
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import AnalysisStatus, IncidentStatus, ReviewDecision, ReviewStatus, Severity
from app.core.errors import AppError
from app.database.base import utc_now
from app.models.activity import ActivityEvent
from app.models.analysis_review import AnalysisReview
from app.models.incident import Incident
from app.models.incident_analysis import IncidentAnalysis
from app.models.notification import OperatorNotification
from app.models.procedure_policy import ProcedureRetrieval, ResponsePlan
from app.models.video import VideoAsset
from app.schemas.common import APIModel
from app.services import procedures as procedure_service

logger = logging.getLogger(__name__)


class WorkflowStatusRead(APIModel):
    analysis_id: str
    analysis_code: str
    video_id: str | None = None
    video_code: str | None = None
    camera_id: str | None = None
    camera_name: str | None = None
    location: str | None = None
    incident_id: str | None = None
    incident_code: str | None = None
    notification_id: str | None = None
    notification_code: str | None = None
    retrieval_id: str | None = None
    retrieval_code: str | None = None
    plan_id: str | None = None
    plan_code: str | None = None
    review_decision: str | None = None
    pipeline_status: str
    message: str
    incident_detected: bool | None = None
    severity: str | None = None
    confidence: float | None = None
    incident_type: str | None = None


class OperatorNotificationRead(APIModel):
    id: str
    notification_code: str
    analysis_id: str
    analysis_code: str | None = None
    video_code: str | None = None
    title: str
    incident_type: str | None = None
    camera_id: str | None = None
    camera_name: str | None = None
    location: str
    severity: str | None = None
    confidence: float | None = None
    status: str
    review_status: str
    dismissed: bool
    message: str
    detected_at: str
    created_at: str


def _year_prefix() -> str:
    return str(utc_now().year)


def _next_code(db: Session, model, field_name: str, prefix: str) -> str:
    column = getattr(model, field_name)
    count = db.scalar(select(func.count()).select_from(model).where(column.like(f"{prefix}-%"))) or 0
    return f"{prefix}-{count + 1:04d}"


def _get_analysis(db: Session, identifier: str) -> IncidentAnalysis:
    analysis = db.scalars(
        select(IncidentAnalysis)
        .options(
            selectinload(IncidentAnalysis.video_asset).selectinload(VideoAsset.camera),
            selectinload(IncidentAnalysis.review),
            selectinload(IncidentAnalysis.evidence_items),
        )
        .where(
            (IncidentAnalysis.id == identifier)
            | (IncidentAnalysis.analysis_code == identifier)
        )
    ).first()
    if analysis is None:
        raise AppError("ANALYSIS_NOT_FOUND", "Analysis was not found.", status_code=404)
    return analysis


def ensure_incident_for_analysis(db: Session, analysis: IncidentAnalysis) -> Incident | None:
    """Create or reuse an Incident row tied to this analysis's video/camera."""
    # Prefer an incident already linked via notification for this analysis.
    note = db.scalars(
        select(OperatorNotification).where(OperatorNotification.analysis_id == analysis.id)
    ).first()
    if note and note.incident_id:
        linked = db.get(Incident, note.incident_id)
        if linked is not None:
            return linked

    video = analysis.video_asset
    if video is None:
        return None
    camera_id = video.camera_id
    if not camera_id:
        from app.models.camera import Camera

        preferred = db.get(Camera, "cam-03") or db.scalars(select(Camera).limit(1)).first()
        if preferred is None:
            return None
        camera_id = preferred.id

    severity = analysis.severity or Severity.HIGH.value
    if severity == "none":
        severity = Severity.MEDIUM.value
    incident = Incident(
        id=str(uuid4()),
        incident_code=_next_code(db, Incident, "incident_code", f"INC-{_year_prefix()}"),
        title=(analysis.summary or analysis.incident_type or "Possible safety incident")[:200],
        incident_type=analysis.incident_type or "possible_person_down",
        location=video.location,
        camera_id=camera_id,
        severity=severity if severity in {s.value for s in Severity} else Severity.HIGH.value,
        confidence=float(analysis.confidence or 0.0),
        evidence_summary=(analysis.summary or "Evidence preserved from multimodal analysis.")[:2000],
        detected_at=analysis.completed_at or analysis.created_at or utc_now(),
        status=IncidentStatus.AWAITING_REVIEW.value,
        review_status=ReviewStatus.PENDING.value,
    )
    db.add(incident)
    db.flush()
    return incident


def ensure_notification(db: Session, analysis: IncidentAnalysis) -> OperatorNotification | None:
    if not analysis.incident_detected:
        return None
    existing = db.scalars(
        select(OperatorNotification).where(OperatorNotification.analysis_id == analysis.id)
    ).first()
    if existing is not None:
        return existing

    video = analysis.video_asset
    camera = video.camera if video is not None else None
    incident = ensure_incident_for_analysis(db, analysis)
    title = "Possible person-down event"
    if analysis.incident_type:
        from app.core.incident_types import is_ppe_incident, ppe_item_label

        if is_ppe_incident(analysis.incident_type, analysis.summary):
            title = "Possible PPE noncompliance"
            try:
                import json

                missing = json.loads(analysis.possibly_missing_ppe_json or "[]")
            except Exception:
                missing = []
            if missing:
                labels = ", ".join(ppe_item_label(str(item)) for item in missing)
                note_message = f"{labels.capitalize()} not visible · Review required"
            else:
                note_message = "PPE not visible in evidence · Review required"
        else:
            title = analysis.incident_type.replace("_", " ").capitalize() + " event"
            note_message = "Review required"
    else:
        note_message = "Review required"

    note = OperatorNotification(
        id=str(uuid4()),
        notification_code=_next_code(
            db, OperatorNotification, "notification_code", f"NTF-{_year_prefix()}"
        ),
        analysis_id=analysis.id,
        video_asset_id=video.id if video else None,
        incident_id=incident.id if incident else None,
        title=title,
        incident_type=analysis.incident_type,
        camera_id=camera.id if camera else (video.camera_id if video else None),
        camera_name=camera.name if camera else None,
        location=video.location if video else "Unknown location",
        severity=analysis.severity,
        confidence=analysis.confidence,
        status="unread",
        review_status="pending",
        dismissed=False,
        message=note_message,
        detected_at=analysis.completed_at or utc_now(),
    )
    db.add(note)
    db.add(
        ActivityEvent(
            id=str(uuid4()),
            event_type="operator_alert",
            title=title,
            description=(
                f"{note.camera_name or 'Camera'} · {note.location}. "
                f"Severity {note.severity or 'unknown'} · "
                + (
                    "Configured scenario."
                    if analysis.analysis_mode == "configured_demo" or analysis.confidence is None
                    else (
                        f"confidence {int(round((note.confidence or 0) * (100 if (note.confidence or 0) <= 1 else 1)))}%."
                    )
                )
            ),
            incident_id=incident.id if incident else None,
            status="attention",
            occurred_at=utc_now(),
        )
    )
    db.flush()
    return note


def prepare_response_for_analysis(db: Session, analysis_identifier: str) -> WorkflowStatusRead:
    """Idempotently retrieve SOP + draft plan and ensure operator notification."""
    analysis = _get_analysis(db, analysis_identifier)
    if analysis.status not in {
        AnalysisStatus.COMPLETED.value,
        AnalysisStatus.NEEDS_REVIEW.value,
    }:
        raise AppError(
            "ANALYSIS_NOT_READY",
            "Analysis must complete before response preparation.",
            status_code=409,
        )

    ensure_notification(db, analysis)

    retrieval = db.scalars(
        select(ProcedureRetrieval)
        .where(ProcedureRetrieval.analysis_id == analysis.id)
        .order_by(ProcedureRetrieval.created_at.desc())
    ).first()
    if retrieval is None:
        retrieval_read = procedure_service.retrieve_procedures_for_analysis(
            db,
            analysis.analysis_code,
            user_query=None,
        )
        retrieval = db.scalars(
            select(ProcedureRetrieval).where(
                ProcedureRetrieval.retrieval_code == retrieval_read.retrieval_code
            )
        ).first()

    plan = db.scalars(
        select(ResponsePlan)
        .where(ResponsePlan.analysis_id == analysis.id)
        .order_by(ResponsePlan.created_at.desc())
    ).first()
    if plan is None and retrieval is not None:
        try:
            plan_read = procedure_service.generate_response_plan(
                db,
                analysis.analysis_code,
                retrieval_id=retrieval.id,
            )
            plan = db.scalars(
                select(ResponsePlan).where(ResponsePlan.plan_code == plan_read.plan_code)
            ).first()
        except AppError as exc:
            logger.info("Plan generation deferred: %s", exc.message)

    note = db.scalars(
        select(OperatorNotification).where(OperatorNotification.analysis_id == analysis.id)
    ).first()
    if plan is not None and note is not None and note.incident_id and not plan.incident_id:
        plan.incident_id = note.incident_id

    # Attach the strongest retrieved procedure to the incident for reporting.
    if note is not None and note.incident_id and retrieval is not None:
        incident = db.get(Incident, note.incident_id)
        if incident is not None and not incident.matched_procedure_id:
            from app.core.incident_types import is_person_down_incident, is_ppe_incident
            from app.models.procedure import SafetyProcedure
            from app.models.procedure_policy import ProcedureChunk, ProcedureRetrievalMatch

            ranked_matches = db.scalars(
                select(ProcedureRetrievalMatch)
                .where(ProcedureRetrievalMatch.retrieval_id == retrieval.id)
                .order_by(ProcedureRetrievalMatch.rank.asc())
            ).all()
            prefer_ppe = is_ppe_incident(analysis.incident_type, analysis.summary)
            prefer_fall = is_person_down_incident(analysis.incident_type, analysis.summary)
            selected_procedure_id: str | None = None
            fallback_procedure_id: str | None = None
            for match in ranked_matches:
                chunk = db.get(ProcedureChunk, match.chunk_id)
                if chunk is None:
                    continue
                if fallback_procedure_id is None:
                    fallback_procedure_id = chunk.procedure_id
                procedure = db.get(SafetyProcedure, chunk.procedure_id)
                if procedure is None:
                    continue
                code = procedure.procedure_code.lower()
                if prefer_ppe and "ppe" in code:
                    selected_procedure_id = chunk.procedure_id
                    break
                if prefer_fall and "fall" in code:
                    selected_procedure_id = chunk.procedure_id
                    break
            incident.matched_procedure_id = selected_procedure_id or fallback_procedure_id

    db.commit()
    return get_workflow_status(db, analysis.analysis_code)


def get_workflow_status(db: Session, analysis_identifier: str) -> WorkflowStatusRead:
    analysis = _get_analysis(db, analysis_identifier)
    video = analysis.video_asset
    camera = video.camera if video else None
    note = db.scalars(
        select(OperatorNotification).where(OperatorNotification.analysis_id == analysis.id)
    ).first()
    retrieval = db.scalars(
        select(ProcedureRetrieval)
        .where(ProcedureRetrieval.analysis_id == analysis.id)
        .order_by(ProcedureRetrieval.created_at.desc())
    ).first()
    plan = db.scalars(
        select(ResponsePlan)
        .where(ResponsePlan.analysis_id == analysis.id)
        .order_by(ResponsePlan.created_at.desc())
    ).first()
    review = analysis.review
    decision = review.decision if review else None

    if analysis.status in {AnalysisStatus.QUEUED.value, AnalysisStatus.RUNNING.value}:
        pipeline = "analyzing_evidence"
        message = "Analyzing evidence"
    elif decision == ReviewDecision.REJECTED.value:
        pipeline = "rejected"
        message = "Incident rejected"
    elif decision == ReviewDecision.NEEDS_MORE_INFO.value:
        pipeline = "needs_more_information"
        message = "Needs more information"
    elif plan is not None and decision == ReviewDecision.CONFIRMED.value:
        if plan.execution_status in {"executed", "partially_failed"}:
            pipeline = "report_ready"
            message = "Incident response completed"
        elif plan.approval_status in {"approved", "partially_approved"}:
            pipeline = "ready_for_execution"
            message = "Ready to run approved actions"
        else:
            pipeline = "ready_for_approval"
            message = "Ready for action approval"
    elif plan is not None:
        pipeline = "awaiting_human_review"
        message = "Draft response prepared — awaiting incident confirmation"
    elif retrieval is not None:
        pipeline = "preparing_response_plan"
        message = "Preparing response plan"
    elif analysis.incident_detected:
        pipeline = "preparing_company_procedure"
        message = "Preparing company procedure"
    else:
        pipeline = "completed_no_incident"
        message = "Analysis completed — no incident requiring response"

    incident = None
    if note and note.incident_id:
        incident = db.get(Incident, note.incident_id)

    return WorkflowStatusRead(
        analysis_id=analysis.id,
        analysis_code=analysis.analysis_code,
        video_id=video.id if video else None,
        video_code=video.asset_code if video else None,
        camera_id=camera.id if camera else (video.camera_id if video else None),
        camera_name=camera.name if camera else None,
        location=video.location if video else None,
        incident_id=incident.id if incident else None,
        incident_code=incident.incident_code if incident else None,
        notification_id=note.id if note else None,
        notification_code=note.notification_code if note else None,
        retrieval_id=retrieval.id if retrieval else None,
        retrieval_code=retrieval.retrieval_code if retrieval else None,
        plan_id=plan.id if plan else None,
        plan_code=plan.plan_code if plan else None,
        review_decision=decision,
        pipeline_status=pipeline,
        message=message,
        incident_detected=analysis.incident_detected,
        severity=analysis.severity,
        confidence=analysis.confidence,
        incident_type=analysis.incident_type,
    )


def list_notifications(db: Session, *, include_dismissed: bool = False) -> list[OperatorNotificationRead]:
    query = select(OperatorNotification).options(
        selectinload(OperatorNotification.analysis),
        selectinload(OperatorNotification.video_asset),
    ).order_by(OperatorNotification.created_at.desc())
    if not include_dismissed:
        query = query.where(OperatorNotification.dismissed.is_(False))
    rows = db.scalars(query.limit(50)).all()
    return [_notification_to_read(row) for row in rows]


def _notification_to_read(row: OperatorNotification) -> OperatorNotificationRead:
    analysis = row.analysis
    video = row.video_asset
    conf = row.confidence
    return OperatorNotificationRead(
        id=row.id,
        notification_code=row.notification_code,
        analysis_id=row.analysis_id,
        analysis_code=analysis.analysis_code if analysis else None,
        video_code=video.asset_code if video else None,
        title=row.title,
        incident_type=row.incident_type,
        camera_id=row.camera_id,
        camera_name=row.camera_name,
        location=row.location,
        severity=row.severity,
        confidence=conf,
        status=row.status,
        review_status=row.review_status,
        dismissed=row.dismissed,
        message=row.message,
        detected_at=row.detected_at.isoformat(),
        created_at=row.created_at.isoformat(),
    )


def dismiss_notification(db: Session, notification_id: str) -> OperatorNotificationRead:
    row = db.scalars(
        select(OperatorNotification)
        .options(
            selectinload(OperatorNotification.analysis),
            selectinload(OperatorNotification.video_asset),
        )
        .where(
            (OperatorNotification.id == notification_id)
            | (OperatorNotification.notification_code == notification_id)
        )
    ).first()
    if row is None:
        raise AppError("NOTIFICATION_NOT_FOUND", "Notification was not found.", status_code=404)
    row.dismissed = True
    row.status = "dismissed"
    db.commit()
    return _notification_to_read(row)


def require_confirmed_analysis(db: Session, plan: ResponsePlan) -> None:
    analysis = db.get(IncidentAnalysis, plan.analysis_id)
    if analysis is None:
        raise AppError("ANALYSIS_NOT_FOUND", "Linked analysis was not found.", status_code=404)
    review = analysis.review
    if review is None or review.decision != ReviewDecision.CONFIRMED.value:
        raise AppError(
            "INCIDENT_NOT_CONFIRMED",
            "Confirm the incident before approving or executing response actions.",
            status_code=409,
        )

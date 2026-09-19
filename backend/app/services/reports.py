"""Incident report generation and PDF download (Stage 6)."""

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.enums import (
    AuditActorType,
    AuditEventType,
    PlanApprovalStatus,
    ReportStatus,
    ResponsePlanStatus,
)
from app.core.errors import AppError
from app.database.base import utc_now
from app.models.execution import ActionExecution, IncidentReport, PlanApproval
from app.models.incident import Incident
from app.models.procedure_policy import PlannedAction, PlanCitation, ProcedureChunk, ResponsePlan
from app.schemas.execution import GenerateReportRequest, IncidentReportRead
from app.services import audit as audit_service
from app.services.audit import list_audit_events


def _loads_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data]


def _year_prefix() -> str:
    return str(utc_now().year)


def _next_report_code(db: Session) -> str:
    count = (
        db.scalar(
            select(func.count())
            .select_from(IncidentReport)
            .where(IncidentReport.report_code.like(f"RPT-{_year_prefix()}-%"))
        )
        or 0
    )
    return f"RPT-{_year_prefix()}-{count + 1:04d}"


def _resolve_incident(db: Session, identifier: str) -> Incident:
    incident = db.scalars(
        select(Incident)
        .options(selectinload(Incident.camera), selectinload(Incident.matched_procedure))
        .where(or_(Incident.id == identifier, Incident.incident_code == identifier))
    ).first()
    if incident is None:
        raise AppError("INCIDENT_NOT_FOUND", "Incident was not found.", status_code=404)
    return incident


def resolve_report_path(stored_filename: str) -> Path:
    cfg = get_settings()
    name = Path(stored_filename).name
    if name != stored_filename or ".." in stored_filename or "/" in stored_filename:
        raise AppError("INVALID_PATH", "Invalid report reference.", status_code=400)
    root = cfg.report_path
    root.mkdir(parents=True, exist_ok=True)
    candidate = (root / name).resolve()
    if not str(candidate).startswith(str(root.resolve())):
        raise AppError("INVALID_PATH", "Invalid report reference.", status_code=400)
    return candidate


def _build_summary(
    db: Session,
    *,
    incident: Incident,
    plan: ResponsePlan | None,
    approval: PlanApproval | None,
    executions: list[ActionExecution],
) -> dict:
    analysis = plan.analysis if plan else None
    citations = []
    actions = []
    if plan:
        for action in plan.actions:
            cites = [
                {
                    "chunk_id": cite.chunk_id,
                    "excerpt": cite.excerpt,
                    "procedure_code": cite.chunk.procedure.procedure_code
                    if cite.chunk and cite.chunk.procedure
                    else None,
                }
                for cite in action.citations
            ]
            citations.extend(cites)
            actions.append(
                {
                    "id": action.id,
                    "title": action.title,
                    "description": action.description,
                    "priority": action.priority,
                    "responsible_role": action.responsible_role,
                    "selection_status": action.selection_status,
                    "citations": cites,
                }
            )
    execution_rows = [
        {
            "execution_code": item.execution_code,
            "action_id": item.action_id,
            "action_title": item.action.title if item.action else None,
            "status": item.status,
            "message": item.message,
            "simulation": item.simulation,
            "external_reference": item.external_reference,
        }
        for item in executions
    ]
    audit = [
        event.model_dump(mode="json")
        for event in list_audit_events(db, incident_id=incident.id, limit=200)
    ]
    procedure = incident.matched_procedure
    return {
        "brand": "SafetyLens",
        "incident_code": incident.incident_code,
        "incident_type": incident.incident_type,
        "title": incident.title,
        "location": incident.location,
        "camera": incident.camera.name if incident.camera else None,
        "detected_at": incident.detected_at.isoformat() if incident.detected_at else None,
        "severity": incident.severity,
        "confidence": incident.confidence,
        "evidence_summary": incident.evidence_summary,
        "analysis": {
            "analysis_code": analysis.analysis_code if analysis else None,
            "summary": analysis.summary if analysis else None,
            "detailed_analysis": analysis.detailed_analysis if analysis else None,
            "severity": analysis.severity if analysis else None,
            "confidence": analysis.confidence if analysis else None,
            "incident_type": analysis.incident_type if analysis else None,
            "analysis_mode": getattr(analysis, "analysis_mode", None) if analysis else None,
            "required_ppe": _loads_json_list(getattr(analysis, "required_ppe_json", None))
            if analysis
            else [],
            "observed_ppe": _loads_json_list(getattr(analysis, "observed_ppe_json", None))
            if analysis
            else [],
            "possibly_missing_ppe": _loads_json_list(
                getattr(analysis, "possibly_missing_ppe_json", None)
            )
            if analysis
            else [],
            "provider_name": analysis.provider_name if analysis else None,
            "is_demo": analysis.is_demo if analysis else None,
        }
        if analysis
        else None,
        "procedure": {
            "procedure_code": procedure.procedure_code if procedure else None,
            "title": procedure.title if procedure else None,
            "version": procedure.version if procedure else None,
        }
        if procedure
        else None,
        "plan": {
            "plan_code": plan.plan_code if plan else None,
            "summary": plan.summary if plan else None,
            "rationale": plan.rationale if plan else None,
            "approval_status": plan.approval_status if plan else None,
            "execution_status": plan.execution_status if plan else None,
        }
        if plan
        else None,
        "approval": {
            "approval_code": approval.approval_code if approval else None,
            "reviewer_name": approval.reviewer_name if approval else None,
            "status": approval.status if approval else None,
            "notes": approval.notes if approval else None,
            "decided_at": approval.decided_at.isoformat() if approval and approval.decided_at else None,
        }
        if approval
        else None,
        "actions": actions,
        "citations": citations,
        "executions": execution_rows,
        "audit_timeline": audit,
        "simulation_disclosure": (
            "All Stage 6 action outcomes in this report are SIMULATED. "
            "No real notifications, emergency services, or external tickets were contacted."
        ),
        "limitations": [
            "Prototype authentication only (demo-reviewer).",
            "Audit trail is application-level append-only, not a compliance ledger.",
            "Sample procedure text is demonstration content, not legal advice.",
        ],
    }


def _render_pdf(summary: dict, report_code: str) -> bytes:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except ImportError as exc:  # pragma: no cover
        raise AppError(
            "DEPENDENCY_MISSING",
            "PDF generation requires the reportlab package.",
            status_code=500,
        ) from exc

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=f"SafetyLens {report_code}")
    styles = getSampleStyleSheet()
    story = []

    def add(text: str, style: str = "Normal") -> None:
        story.append(Paragraph(text.replace("\n", "<br/>"), styles[style]))
        story.append(Spacer(1, 0.08 * inch))

    add("SafetyLens Incident Report", "Title")
    add(f"Report ID: {report_code}", "Heading2")
    add(f"<b>SIMULATION DISCLOSURE:</b> {summary['simulation_disclosure']}")
    add(f"Incident: {summary.get('incident_code')} — {summary.get('title')}", "Heading2")
    add(
        f"Type: {summary.get('incident_type')} | Location: {summary.get('location')} | "
        f"Camera: {summary.get('camera')} | Severity: {summary.get('severity')} | "
        f"Confidence: {summary.get('confidence')}"
    )
    add(f"Detected: {summary.get('detected_at')}")
    add(f"Evidence summary: {summary.get('evidence_summary')}")

    analysis = summary.get("analysis") or {}
    if analysis:
        add("Analysis", "Heading2")
        add(f"Code: {analysis.get('analysis_code')}")
        add(f"Type: {analysis.get('incident_type')}")
        mode = analysis.get("analysis_mode")
        provider = analysis.get("provider_name")
        if mode or provider:
            add(f"Provider: {provider or '—'} | Mode: {mode or '—'}")
        conf = analysis.get("confidence")
        if mode == "configured_demo" or conf is None:
            add("Confidence: Configured scenario" if mode == "configured_demo" else "Confidence: —")
        else:
            add(f"Confidence: {conf}")
        required = analysis.get("required_ppe") or []
        observed = analysis.get("observed_ppe") or []
        missing = analysis.get("possibly_missing_ppe") or []
        if required or observed or missing:
            add(f"Required PPE: {', '.join(required) if required else '—'}")
            add(f"Observed PPE: {', '.join(observed) if observed else 'not clearly visible'}")
            add(
                f"Possibly missing PPE: {', '.join(missing) if missing else '—'}"
            )
        add(f"Summary: {analysis.get('summary')}")
        add(f"Details: {analysis.get('detailed_analysis')}")

    procedure = summary.get("procedure") or {}
    if procedure.get("procedure_code"):
        add("Matched procedure", "Heading2")
        add(
            f"{procedure.get('procedure_code')} — {procedure.get('title')} "
            f"(v{procedure.get('version')})"
        )

    plan = summary.get("plan") or {}
    if plan.get("plan_code"):
        add("Response plan", "Heading2")
        add(f"Plan: {plan.get('plan_code')}")
        add(f"Summary: {plan.get('summary')}")
        add(f"Rationale: {plan.get('rationale')}")
        add(
            f"Approval status: {plan.get('approval_status')} | "
            f"Execution status: {plan.get('execution_status')}"
        )

    approval = summary.get("approval") or {}
    if approval.get("approval_code"):
        add("Human approval", "Heading2")
        add(
            f"{approval.get('status')} by {approval.get('reviewer_name')} "
            f"at {approval.get('decided_at')}"
        )
        if approval.get("notes"):
            add(f"Notes: {approval.get('notes')}")

    add("Actions", "Heading2")
    for action in summary.get("actions") or []:
        add(
            f"• [{action.get('selection_status')}] {action.get('title')} "
            f"({action.get('priority')}) — {action.get('responsible_role')}"
        )
        add(action.get("description") or "")
        for cite in action.get("citations") or []:
            add(f"Citation ({cite.get('procedure_code')}): {cite.get('excerpt')}")

    add("Simulated execution outcomes", "Heading2")
    for item in summary.get("executions") or []:
        add(
            f"• {item.get('execution_code')} [{item.get('status')}] "
            f"{item.get('action_title')}: {item.get('message')}"
        )

    add("Audit timeline", "Heading2")
    for event in summary.get("audit_timeline") or []:
        add(
            f"• {event.get('occurred_at')} | {event.get('event_type')} | "
            f"{event.get('actor_name')} | sim={event.get('simulation')}"
        )

    add("Limitations", "Heading2")
    for item in summary.get("limitations") or []:
        add(f"• {item}")

    add(f"Generated at: {utc_now().isoformat()}")
    doc.build(story)
    return buffer.getvalue()


def _report_to_read(report: IncidentReport) -> IncidentReportRead:
    summary = {}
    try:
        summary = json.loads(report.summary_json or "{}")
    except json.JSONDecodeError:
        summary = {}
    return IncidentReportRead(
        id=report.id,
        report_code=report.report_code,
        incident_id=report.incident_id,
        incident_code=report.incident.incident_code if report.incident else None,
        plan_id=report.plan_id,
        plan_code=report.plan.plan_code if report.plan else None,
        approval_id=report.approval_id,
        status=ReportStatus(report.status),
        simulation=report.simulation,
        title=report.title,
        summary=summary if isinstance(summary, dict) else {},
        incomplete_reason=report.incomplete_reason,
        download_url=f"/api/reports/{report.report_code}/download"
        if report.stored_filename
        else None,
        generated_at=report.generated_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


def generate_incident_report(
    db: Session,
    incident_identifier: str,
    payload: GenerateReportRequest | None = None,
) -> IncidentReportRead:
    request = payload or GenerateReportRequest()
    incident = _resolve_incident(db, incident_identifier)

    plan: ResponsePlan | None = None
    if request.plan_identifier:
        plan = db.scalars(
            select(ResponsePlan)
            .options(
                selectinload(ResponsePlan.actions)
                .selectinload(PlannedAction.citations)
                .selectinload(PlanCitation.chunk)
                .selectinload(ProcedureChunk.procedure),
                selectinload(ResponsePlan.analysis),
                selectinload(ResponsePlan.approvals),
            )
            .where(
                or_(
                    ResponsePlan.id == request.plan_identifier,
                    ResponsePlan.plan_code == request.plan_identifier,
                )
            )
        ).first()
        if plan is None:
            raise AppError("PLAN_NOT_FOUND", "Response plan was not found.", status_code=404)
    else:
        plan = db.scalars(
            select(ResponsePlan)
            .options(
                selectinload(ResponsePlan.actions)
                .selectinload(PlannedAction.citations)
                .selectinload(PlanCitation.chunk)
                .selectinload(ProcedureChunk.procedure),
                selectinload(ResponsePlan.analysis),
                selectinload(ResponsePlan.approvals),
            )
            .where(ResponsePlan.incident_id == incident.id)
            .order_by(ResponsePlan.created_at.desc())
        ).first()

    approval = None
    executions: list[ActionExecution] = []
    if plan:
        if plan.approvals:
            approval = sorted(plan.approvals, key=lambda item: item.created_at, reverse=True)[0]
        executions = list(
            db.scalars(
                select(ActionExecution)
                .options(selectinload(ActionExecution.action))
                .where(ActionExecution.plan_id == plan.id)
                .order_by(ActionExecution.created_at.asc())
            ).all()
        )

    incomplete_reason = None
    status = ReportStatus.COMPLETE
    if plan is None:
        status = ReportStatus.INCOMPLETE
        incomplete_reason = "No linked response plan; report contains incident seed data only."
    elif plan.status != ResponsePlanStatus.COMPLETED.value:
        status = ReportStatus.INCOMPLETE
        incomplete_reason = "Linked plan is not a completed grounded response plan."
    elif approval is None or approval.status not in {
        PlanApprovalStatus.APPROVED.value,
        PlanApprovalStatus.PARTIALLY_APPROVED.value,
        PlanApprovalStatus.REJECTED.value,
    }:
        status = ReportStatus.INCOMPLETE
        incomplete_reason = "Human approval has not been recorded for the linked plan."

    # Reuse latest complete report unless forced or underlying execution changed.
    if not request.force_regenerate:
        existing = db.scalars(
            select(IncidentReport)
            .options(selectinload(IncidentReport.incident), selectinload(IncidentReport.plan))
            .where(
                IncidentReport.incident_id == incident.id,
                IncidentReport.plan_id == (plan.id if plan else None),
                IncidentReport.status == ReportStatus.COMPLETE.value,
            )
            .order_by(IncidentReport.generated_at.desc())
        ).first()
        if existing and plan and existing.approval_id == (approval.id if approval else None):
            # If execution count matches, return existing.
            prior_count = len((json.loads(existing.summary_json).get("executions") or []))
            if prior_count == len(executions):
                return _report_to_read(existing)

    summary = _build_summary(
        db,
        incident=incident,
        plan=plan,
        approval=approval,
        executions=executions,
    )
    report_code = _next_report_code(db)
    pdf_bytes = _render_pdf(summary, report_code)
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    stored = f"{uuid4().hex}.pdf"
    path = resolve_report_path(stored)
    path.write_bytes(pdf_bytes)

    report = IncidentReport(
        id=str(uuid4()),
        report_code=report_code,
        incident_id=incident.id,
        plan_id=plan.id if plan else None,
        approval_id=approval.id if approval else None,
        status=status.value,
        simulation=True,
        title=f"SafetyLens Report — {incident.incident_code}",
        summary_json=json.dumps(summary),
        stored_filename=stored,
        content_sha256=digest,
        incomplete_reason=incomplete_reason,
        generated_at=utc_now(),
    )
    db.add(report)
    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.REPORT_GENERATED,
        actor_type=AuditActorType.SYSTEM,
        actor_name="report-generator",
        correlation_id=approval.correlation_id if approval else report_code,
        incident_id=incident.id,
        analysis_id=plan.analysis_id if plan else None,
        plan_id=plan.id if plan else None,
        metadata={
            "report_code": report_code,
            "status": status.value,
            "simulation": True,
        },
        new_status=status.value,
        simulation=True,
    )
    db.commit()
    loaded = db.scalars(
        select(IncidentReport)
        .options(selectinload(IncidentReport.incident), selectinload(IncidentReport.plan))
        .where(IncidentReport.id == report.id)
    ).one()
    return _report_to_read(loaded)


def list_incident_reports(db: Session, incident_identifier: str) -> list[IncidentReportRead]:
    incident = _resolve_incident(db, incident_identifier)
    rows = db.scalars(
        select(IncidentReport)
        .options(selectinload(IncidentReport.incident), selectinload(IncidentReport.plan))
        .where(IncidentReport.incident_id == incident.id)
        .order_by(IncidentReport.generated_at.desc())
    ).all()
    return [_report_to_read(row) for row in rows]


def get_report(db: Session, report_identifier: str) -> IncidentReportRead:
    report = db.scalars(
        select(IncidentReport)
        .options(selectinload(IncidentReport.incident), selectinload(IncidentReport.plan))
        .where(
            or_(
                IncidentReport.id == report_identifier,
                IncidentReport.report_code == report_identifier,
            )
        )
    ).first()
    if report is None:
        raise AppError("REPORT_NOT_FOUND", "Report was not found.", status_code=404)
    return _report_to_read(report)


def get_report_pdf_bytes(db: Session, report_identifier: str) -> tuple[IncidentReport, bytes]:
    report = db.scalars(
        select(IncidentReport)
        .options(selectinload(IncidentReport.incident))
        .where(
            or_(
                IncidentReport.id == report_identifier,
                IncidentReport.report_code == report_identifier,
            )
        )
    ).first()
    if report is None:
        raise AppError("REPORT_NOT_FOUND", "Report was not found.", status_code=404)
    if not report.stored_filename:
        raise AppError("REPORT_FILE_MISSING", "Report PDF is not available.", status_code=404)
    path = resolve_report_path(report.stored_filename)
    if not path.is_file():
        raise AppError("REPORT_FILE_MISSING", "Report PDF is not available.", status_code=404)
    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.REPORT_DOWNLOADED,
        actor_type=AuditActorType.HUMAN,
        actor_name="demo-reviewer",
        correlation_id=report.report_code,
        incident_id=report.incident_id,
        plan_id=report.plan_id,
        metadata={"report_code": report.report_code},
        simulation=True,
    )
    db.commit()
    return report, path.read_bytes()

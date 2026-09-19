from __future__ import annotations

import json
import logging
from datetime import date
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.enums import (
    ActionPriority,
    AnalysisStatus,
    PlanApprovalStatus,
    PlanExecutionStatus,
    ProcedureSourceFormat,
    ResponsePlanStatus,
    RetrievalMethod,
    RetrievalStatus,
)
from app.core.errors import AppError
from app.database.base import utc_now
from app.models.incident_analysis import IncidentAnalysis
from app.models.procedure import SafetyProcedure
from app.models.procedure_policy import (
    PlanCitation,
    PlannedAction,
    ProcedureChunk,
    ProcedureRetrieval,
    ProcedureRetrievalMatch,
    ResponsePlan,
)
from app.schemas.common import Meta
from app.schemas.procedure import (
    PlannedActionRead,
    PlanCitationRead,
    ProcedureChunkRead,
    ProcedureRead,
    ProcedureRetrievalRead,
    ProcedureUploadResponse,
    ResponsePlanRead,
    RetrievalMatchRead,
)
from app.services import storage
from app.services.planner import get_response_planner
from app.services.procedure_ingest import (
    chunk_procedure_text,
    content_sha256,
    extract_text_from_bytes,
    resolve_procedure_path,
    validate_procedure_upload,
)
from app.services.retrieval import build_query_text, retrieve_chunks

logger = logging.getLogger(__name__)

SOURCE_NAME_DEFAULT = "Redwood Distribution Center Safety Manual"


def parse_procedure_steps(content: str) -> list[str]:
    steps: list[str] = []
    for line in content.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        if cleaned[0].isdigit() and "." in cleaned[:4]:
            _, _, rest = cleaned.partition(".")
            steps.append(rest.strip() or cleaned)
        else:
            steps.append(cleaned)
    return steps


def procedure_to_read(procedure: SafetyProcedure) -> ProcedureRead:
    return ProcedureRead(
        id=procedure.id,
        procedure_code=procedure.procedure_code,
        title=procedure.title,
        category=procedure.category,
        version=procedure.version,
        content=procedure.content,
        source_name=procedure.source_name,
        is_active=procedure.is_active,
        created_at=procedure.created_at,
        updated_at=procedure.updated_at,
        steps=parse_procedure_steps(procedure.content),
        effective_date=procedure.effective_date,
        source_filename=procedure.source_filename,
        source_format=procedure.source_format,
        chunk_count=procedure.chunk_count or 0,
        is_sample=bool(procedure.is_sample),
    )


def list_procedures(
    db: Session,
    *,
    search: str | None = None,
    category: str | None = None,
    active: bool | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ProcedureRead], Meta]:
    query = select(SafetyProcedure)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                SafetyProcedure.title.ilike(pattern),
                SafetyProcedure.procedure_code.ilike(pattern),
                SafetyProcedure.category.ilike(pattern),
            )
        )
    if category:
        query = query.where(SafetyProcedure.category.ilike(f"%{category}%"))
    if active is not None:
        query = query.where(SafetyProcedure.is_active.is_(active))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(SafetyProcedure.title.asc()).limit(limit).offset(offset)
    ).all()
    return [procedure_to_read(row) for row in rows], Meta(
        count=total,
        limit=limit,
        offset=offset,
    )


def _get_procedure_model(db: Session, identifier: str) -> SafetyProcedure:
    procedure = db.scalars(
        select(SafetyProcedure)
        .options(selectinload(SafetyProcedure.chunks))
        .where(
            or_(
                SafetyProcedure.id == identifier,
                SafetyProcedure.procedure_code == identifier,
            )
        )
    ).first()
    if procedure is None:
        raise AppError("NOT_FOUND", "Procedure not found", status_code=404)
    return procedure


def get_procedure(db: Session, identifier: str) -> ProcedureRead:
    return procedure_to_read(_get_procedure_model(db, identifier))


def list_procedure_chunks(db: Session, identifier: str) -> list[ProcedureChunkRead]:
    procedure = _get_procedure_model(db, identifier)
    return [
        ProcedureChunkRead(
            id=chunk.id,
            chunk_code=chunk.chunk_code,
            chunk_order=chunk.chunk_order,
            section_heading=chunk.section_heading,
            page_number=chunk.page_number,
            content=chunk.content,
            procedure_id=procedure.id,
            procedure_code=procedure.procedure_code,
            procedure_title=procedure.title,
            procedure_version=procedure.version,
        )
        for chunk in procedure.chunks
    ]


def replace_procedure_chunks(
    db: Session,
    procedure: SafetyProcedure,
    drafts,
) -> None:
    for existing in list(procedure.chunks):
        db.delete(existing)
    db.flush()
    for draft in drafts:
        db.add(
            ProcedureChunk(
                id=str(uuid4()),
                procedure_id=procedure.id,
                chunk_code=f"{procedure.procedure_code}-C{draft.chunk_order:03d}",
                chunk_order=draft.chunk_order,
                section_heading=draft.section_heading,
                page_number=draft.page_number,
                content=draft.content,
                content_hash=content_sha256(draft.content),
            )
        )
    procedure.chunk_count = len(drafts)


def ensure_chunks_for_procedure(
    db: Session,
    procedure: SafetyProcedure,
    *,
    settings: Settings | None = None,
) -> None:
    if procedure.chunks:
        return
    cfg = settings or get_settings()
    drafts = chunk_procedure_text(
        [(None, procedure.content)],
        max_chars=cfg.procedure_chunk_max_chars,
    )
    replace_procedure_chunks(db, procedure, drafts)


async def upload_procedure(
    db: Session,
    *,
    upload: UploadFile,
    procedure_code: str,
    title: str,
    category: str,
    version: str,
    source_name: str | None = None,
    effective_date: date | None = None,
    is_sample: bool = False,
    settings: Settings | None = None,
) -> ProcedureUploadResponse:
    cfg = settings or get_settings()
    cfg.procedure_path.mkdir(parents=True, exist_ok=True)

    raw = await upload.read()
    safe_name, source_format = validate_procedure_upload(
        filename=upload.filename,
        content_type=upload.content_type,
        size_bytes=len(raw),
        settings=cfg,
    )
    full_text, segments = extract_text_from_bytes(raw, source_format=source_format, settings=cfg)
    digest = content_sha256(full_text)

    code = require_code(procedure_code)
    existing = db.scalars(
        select(SafetyProcedure).where(
            or_(
                SafetyProcedure.procedure_code == code,
                SafetyProcedure.content_hash == digest,
            )
        )
    ).first()
    if existing is not None:
        raise AppError(
            "DUPLICATE_PROCEDURE",
            "A procedure with the same code or identical content already exists.",
            status_code=409,
        )

    drafts = chunk_procedure_text(segments, max_chars=cfg.procedure_chunk_max_chars)
    from pathlib import Path as PathLib

    extension = PathLib(safe_name).suffix.lower() or ".txt"
    stored = storage.generate_stored_filename(extension)
    destination = resolve_procedure_path(stored, cfg)
    destination.write_bytes(raw)

    procedure = SafetyProcedure(
        id=str(uuid4()),
        procedure_code=code,
        title=title.strip(),
        category=category.strip(),
        version=version.strip(),
        content=full_text,
        source_name=(source_name or SOURCE_NAME_DEFAULT).strip(),
        is_active=True,
        effective_date=effective_date,
        source_filename=safe_name,
        source_format=source_format.value,
        content_hash=digest,
        stored_filename=stored,
        chunk_count=len(drafts),
        is_sample=is_sample,
    )
    db.add(procedure)
    db.flush()
    replace_procedure_chunks(db, procedure, drafts)
    db.commit()
    db.refresh(procedure)

    return ProcedureUploadResponse(
        id=procedure.id,
        procedure_code=procedure.procedure_code,
        title=procedure.title,
        version=procedure.version,
        source_format=procedure.source_format or source_format.value,
        source_filename=safe_name,
        chunk_count=procedure.chunk_count,
        is_sample=procedure.is_sample,
        message="Procedure ingested and chunked successfully.",
    )


def require_code(value: str) -> str:
    cleaned = value.strip().upper()
    if not cleaned:
        raise AppError("VALIDATION_ERROR", "procedure_code must not be blank", status_code=422)
    return cleaned


def _year_prefix() -> str:
    return str(utc_now().year)


def _next_code(db: Session, model, field_name: str, prefix: str) -> str:
    column = getattr(model, field_name)
    count = db.scalar(select(func.count()).select_from(model).where(column.like(f"{prefix}-%"))) or 0
    return f"{prefix}-{count + 1:04d}"


def _get_analysis(db: Session, identifier: str) -> IncidentAnalysis:
    analysis = db.scalars(
        select(IncidentAnalysis)
        .options(selectinload(IncidentAnalysis.evidence_items))
        .where(
            or_(
                IncidentAnalysis.id == identifier,
                IncidentAnalysis.analysis_code == identifier,
            )
        )
    ).first()
    if analysis is None:
        raise AppError("ANALYSIS_NOT_FOUND", "Analysis was not found.", status_code=404)
    return analysis


def _require_analysis_for_policy(analysis: IncidentAnalysis) -> None:
    if analysis.status == AnalysisStatus.FAILED.value:
        raise AppError(
            "ANALYSIS_FAILED",
            "Cannot retrieve procedures or generate plans for a failed analysis.",
            status_code=409,
        )
    if analysis.status in {
        AnalysisStatus.QUEUED.value,
        AnalysisStatus.RUNNING.value,
    }:
        raise AppError(
            "ANALYSIS_NOT_READY",
            "Analysis must complete before procedure retrieval or planning.",
            status_code=409,
        )


def _retrieval_to_read(retrieval: ProcedureRetrieval) -> ProcedureRetrievalRead:
    matches: list[RetrievalMatchRead] = []
    for item in retrieval.matches:
        chunk = item.chunk
        procedure = chunk.procedure if chunk is not None else None
        matches.append(
            RetrievalMatchRead(
                procedure_id=procedure.id if procedure else chunk.procedure_id,
                procedure_code=procedure.procedure_code if procedure else "",
                procedure_title=procedure.title if procedure else "",
                procedure_version=procedure.version if procedure else "",
                chunk_id=chunk.id,
                chunk_code=chunk.chunk_code,
                chunk_order=chunk.chunk_order,
                section_heading=chunk.section_heading,
                page_number=chunk.page_number,
                excerpt=chunk.content,
                score=item.score,
                method=item.method,
                rank=item.rank,
            )
        )
    analysis_code = retrieval.analysis.analysis_code if retrieval.analysis else None
    return ProcedureRetrievalRead(
        id=retrieval.id,
        retrieval_code=retrieval.retrieval_code,
        analysis_id=retrieval.analysis_id,
        analysis_code=analysis_code,
        query_text=retrieval.query_text,
        method=RetrievalMethod(retrieval.method),
        status=RetrievalStatus(retrieval.status),
        match_count=retrieval.match_count,
        message=retrieval.message,
        matches=matches,
        created_at=retrieval.created_at,
    )


def retrieve_procedures_for_analysis(
    db: Session,
    analysis_identifier: str,
    *,
    user_query: str | None = None,
    settings: Settings | None = None,
) -> ProcedureRetrievalRead:
    cfg = settings or get_settings()
    analysis = _get_analysis(db, analysis_identifier)
    _require_analysis_for_policy(analysis)

    # Ensure seed/active procedures have chunks for citation.
    for procedure in db.scalars(select(SafetyProcedure).where(SafetyProcedure.is_active.is_(True))).all():
        ensure_chunks_for_procedure(db, procedure, settings=cfg)
    db.commit()

    evidence_descriptions = [item.observation for item in analysis.evidence_items]
    query_text = build_query_text(
        incident_type=analysis.incident_type,
        title=analysis.incident_type,
        summary=analysis.summary,
        severity=analysis.severity,
        location=None,
        evidence_descriptions=evidence_descriptions,
        user_query=user_query,
    )
    ranked = retrieve_chunks(
        db,
        query_text=query_text,
        settings=cfg,
        method=RetrievalMethod.LEXICAL,
    )
    status = RetrievalStatus.COMPLETED if ranked else RetrievalStatus.INSUFFICIENT
    message = (
        None
        if ranked
        else "No procedure chunks scored above the retrieval threshold."
    )
    retrieval = ProcedureRetrieval(
        id=str(uuid4()),
        retrieval_code=_next_code(db, ProcedureRetrieval, "retrieval_code", f"RET-{_year_prefix()}"),
        analysis_id=analysis.id,
        query_text=query_text,
        method=RetrievalMethod.LEXICAL.value,
        status=status.value,
        match_count=len(ranked),
        message=message,
    )
    db.add(retrieval)
    db.flush()
    for rank, item in enumerate(ranked, start=1):
        db.add(
            ProcedureRetrievalMatch(
                id=str(uuid4()),
                retrieval_id=retrieval.id,
                chunk_id=item.chunk.id,
                rank=rank,
                score=item.score,
                method=item.method,
            )
        )
    db.commit()

    loaded = db.scalars(
        select(ProcedureRetrieval)
        .options(
            selectinload(ProcedureRetrieval.analysis),
            selectinload(ProcedureRetrieval.matches)
            .selectinload(ProcedureRetrievalMatch.chunk)
            .selectinload(ProcedureChunk.procedure),
        )
        .where(ProcedureRetrieval.id == retrieval.id)
    ).one()
    return _retrieval_to_read(loaded)


def _plan_to_read(plan: ResponsePlan) -> ResponsePlanRead:
    actions: list[PlannedActionRead] = []
    for action in plan.actions:
        citations = [
            PlanCitationRead(
                id=cite.id,
                chunk_id=cite.chunk_id,
                chunk_code=cite.chunk.chunk_code if cite.chunk else None,
                procedure_code=cite.chunk.procedure.procedure_code if cite.chunk and cite.chunk.procedure else None,
                procedure_title=cite.chunk.procedure.title if cite.chunk and cite.chunk.procedure else None,
                section_heading=cite.chunk.section_heading if cite.chunk else None,
                page_number=cite.chunk.page_number if cite.chunk else None,
                excerpt=cite.excerpt,
            )
            for cite in action.citations
        ]
        actions.append(
            PlannedActionRead(
                id=action.id,
                action_order=action.action_order,
                title=action.title,
                description=action.description,
                priority=ActionPriority(action.priority),
                responsible_role=action.responsible_role,
                requires_human_approval=action.requires_human_approval,
                is_policy_grounded=action.is_policy_grounded,
                selection_status=getattr(action, "selection_status", "recommended") or "recommended",
                citations=citations,
            )
        )
    label = (
        "Demo Planner (simulated)"
        if plan.is_demo
        else f"{plan.provider_name} (real provider)"
    )
    limitations = []
    if plan.limitations_json:
        try:
            limitations = json.loads(plan.limitations_json)
        except json.JSONDecodeError:
            limitations = []
    executed = getattr(plan, "execution_status", "none") in {
        "executed",
        "partially_failed",
        "failed",
        "in_progress",
    }
    return ResponsePlanRead(
        id=plan.id,
        plan_code=plan.plan_code,
        analysis_id=plan.analysis_id,
        analysis_code=plan.analysis.analysis_code if plan.analysis else None,
        retrieval_id=plan.retrieval_id,
        retrieval_code=plan.retrieval.retrieval_code if plan.retrieval else None,
        status=ResponsePlanStatus(plan.status),
        approval_status=PlanApprovalStatus(getattr(plan, "approval_status", "pending") or "pending"),
        execution_status=PlanExecutionStatus(getattr(plan, "execution_status", "none") or "none"),
        incident_id=getattr(plan, "incident_id", None),
        summary=plan.summary,
        rationale=plan.rationale,
        provider_name=plan.provider_name,
        provider_model=plan.provider_model,
        is_demo=plan.is_demo,
        is_simulated=plan.is_simulated,
        provider_label=label,
        limitations=limitations if isinstance(limitations, list) else [],
        error_code=plan.error_code,
        error_message=plan.error_message,
        actions=actions,
        recommendations_executed=executed,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def verify_and_snapshot_citations(
    db: Session,
    *,
    chunk_ids: list[str],
    allowed_chunk_ids: set[str],
) -> list[tuple[ProcedureChunk, str]]:
    verified: list[tuple[ProcedureChunk, str]] = []
    for chunk_id in chunk_ids:
        if chunk_id not in allowed_chunk_ids:
            raise AppError(
                "INVALID_CITATION",
                f"Citation chunk '{chunk_id}' was not part of the retrieved evidence set.",
                status_code=422,
            )
        chunk = db.get(ProcedureChunk, chunk_id)
        if chunk is None:
            raise AppError(
                "INVALID_CITATION",
                f"Citation chunk '{chunk_id}' does not exist.",
                status_code=422,
            )
        # Exact stored text snapshot — never fabricate.
        verified.append((chunk, chunk.content))
    return verified


def generate_response_plan(
    db: Session,
    analysis_identifier: str,
    *,
    retrieval_id: str | None = None,
    settings: Settings | None = None,
) -> ResponsePlanRead:
    cfg = settings or get_settings()
    analysis = _get_analysis(db, analysis_identifier)
    _require_analysis_for_policy(analysis)

    active = db.scalar(
        select(ResponsePlan).where(
            ResponsePlan.analysis_id == analysis.id,
            ResponsePlan.status == ResponsePlanStatus.QUEUED.value,
        )
    )
    if active is not None:
        raise AppError(
            "PLAN_IN_PROGRESS",
            "A response plan is already being generated for this analysis.",
            status_code=409,
        )

    if retrieval_id:
        retrieval = db.scalars(
            select(ProcedureRetrieval)
            .options(
                selectinload(ProcedureRetrieval.matches)
                .selectinload(ProcedureRetrievalMatch.chunk)
                .selectinload(ProcedureChunk.procedure),
            )
            .where(
                or_(
                    ProcedureRetrieval.id == retrieval_id,
                    ProcedureRetrieval.retrieval_code == retrieval_id,
                ),
                ProcedureRetrieval.analysis_id == analysis.id,
            )
        ).first()
        if retrieval is None:
            raise AppError(
                "RETRIEVAL_NOT_FOUND",
                "Retrieval result was not found for this analysis.",
                status_code=404,
            )
    else:
        # Auto-run retrieval when none provided.
        latest = retrieve_procedures_for_analysis(db, analysis.analysis_code, settings=cfg)
        retrieval = db.scalars(
            select(ProcedureRetrieval)
            .options(
                selectinload(ProcedureRetrieval.matches)
                .selectinload(ProcedureRetrievalMatch.chunk)
                .selectinload(ProcedureChunk.procedure),
            )
            .where(ProcedureRetrieval.id == latest.id)
        ).one()

    from app.services.retrieval import RankedChunk

    matches = [
        RankedChunk(
            chunk=item.chunk,
            procedure=item.chunk.procedure,
            score=item.score,
            method=item.method,
        )
        for item in retrieval.matches
        if item.chunk is not None and item.chunk.procedure is not None
    ]
    allowed_ids = {item.chunk.id for item in matches}

    planner = get_response_planner(cfg)
    try:
        draft = planner.generate(analysis=analysis, matches=matches)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Planner failed for analysis %s", analysis.analysis_code)
        plan = ResponsePlan(
            id=str(uuid4()),
            plan_code=_next_code(db, ResponsePlan, "plan_code", f"PLAN-{_year_prefix()}"),
            analysis_id=analysis.id,
            retrieval_id=retrieval.id,
            status=ResponsePlanStatus.FAILED.value,
            summary=None,
            rationale=None,
            provider_name=getattr(planner, "name", "unknown"),
            provider_model=getattr(planner, "model", None),
            is_demo=getattr(planner, "is_demo", True),
            is_simulated=getattr(planner, "is_simulated", True),
            limitations_json=json.dumps(["Planner provider failure"]),
            error_code="PLANNER_FAILED",
            error_message=str(exc),
            approval_status=PlanApprovalStatus.PENDING.value,
            execution_status=PlanExecutionStatus.NONE.value,
        )
        db.add(plan)
        db.commit()
        return get_response_plan(db, plan.plan_code)

    status = (
        ResponsePlanStatus.INSUFFICIENT_POLICY
        if draft.status == "insufficient_policy"
        else ResponsePlanStatus.COMPLETED
    )
    plan = ResponsePlan(
        id=str(uuid4()),
        plan_code=_next_code(db, ResponsePlan, "plan_code", f"PLAN-{_year_prefix()}"),
        analysis_id=analysis.id,
        retrieval_id=retrieval.id,
        status=status.value,
        summary=draft.summary,
        rationale=draft.rationale,
        provider_name=draft.provider_name,
        provider_model=draft.provider_model,
        is_demo=draft.is_demo,
        is_simulated=draft.is_simulated,
        limitations_json=json.dumps(draft.limitations),
        approval_status=PlanApprovalStatus.PENDING.value,
        execution_status=PlanExecutionStatus.NONE.value,
    )
    db.add(plan)
    db.flush()

    for index, action_draft in enumerate(draft.actions, start=1):
        if action_draft.is_policy_grounded:
            if not action_draft.citation_chunk_ids:
                raise AppError(
                    "INVALID_CITATION",
                    f"Policy-grounded action '{action_draft.title}' has no citations.",
                    status_code=422,
                )
            verified = verify_and_snapshot_citations(
                db,
                chunk_ids=action_draft.citation_chunk_ids,
                allowed_chunk_ids=allowed_ids,
            )
        else:
            verified = []

        action = PlannedAction(
            id=str(uuid4()),
            plan_id=plan.id,
            action_order=index,
            title=action_draft.title,
            description=action_draft.description,
            priority=action_draft.priority.value,
            responsible_role=action_draft.responsible_role,
            requires_human_approval=action_draft.requires_human_approval,
            is_policy_grounded=action_draft.is_policy_grounded,
            selection_status="recommended",
        )
        db.add(action)
        db.flush()
        for chunk, excerpt in verified:
            db.add(
                PlanCitation(
                    id=str(uuid4()),
                    action_id=action.id,
                    chunk_id=chunk.id,
                    excerpt=excerpt,
                )
            )

    from app.core.enums import AuditActorType, AuditEventType
    from app.services import audit as audit_service

    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.PLAN_GENERATED,
        actor_type=AuditActorType.SYSTEM,
        actor_name=draft.provider_name,
        correlation_id=plan.plan_code,
        analysis_id=plan.analysis_id,
        plan_id=plan.id,
        metadata={"plan_code": plan.plan_code, "status": plan.status},
        new_status=plan.status,
        simulation=draft.is_simulated,
    )

    db.commit()
    return get_response_plan(db, plan.plan_code)


def get_response_plan(db: Session, identifier: str) -> ResponsePlanRead:
    plan = db.scalars(
        select(ResponsePlan)
        .options(
            selectinload(ResponsePlan.analysis),
            selectinload(ResponsePlan.retrieval),
            selectinload(ResponsePlan.actions)
            .selectinload(PlannedAction.citations)
            .selectinload(PlanCitation.chunk)
            .selectinload(ProcedureChunk.procedure),
        )
        .where(
            or_(
                ResponsePlan.id == identifier,
                ResponsePlan.plan_code == identifier,
            )
        )
    ).first()
    if plan is None:
        raise AppError("PLAN_NOT_FOUND", "Response plan was not found.", status_code=404)
    return _plan_to_read(plan)

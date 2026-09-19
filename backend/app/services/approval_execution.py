"""Human approval and simulated execution for Stage 6 response plans."""

from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import (
    ActionExecutionStatus,
    AuditActorType,
    AuditEventType,
    PlanApprovalStatus,
    PlanExecutionStatus,
    ResponsePlanStatus,
)
from app.core.errors import AppError
from app.database.base import utc_now
from app.models.execution import ActionExecution, PlanApproval
from app.models.incident import Incident
from app.models.procedure_policy import PlannedAction, ResponsePlan
from app.schemas.execution import (
    ActionExecutionRead,
    ExecutePlanResponse,
    PlanApprovalRead,
    PlanApproveRequest,
    PlanRejectRequest,
)
from app.services import audit as audit_service
from app.services.executor import get_action_executor, infer_action_type, target_for_action


def _year_prefix() -> str:
    return str(utc_now().year)


def _next_code(db: Session, model, field_name: str, prefix: str) -> str:
    column = getattr(model, field_name)
    count = db.scalar(select(func.count()).select_from(model).where(column.like(f"{prefix}-%"))) or 0
    return f"{prefix}-{count + 1:04d}"


def _get_plan(db: Session, identifier: str) -> ResponsePlan:
    plan = db.scalars(
        select(ResponsePlan)
        .options(
            selectinload(ResponsePlan.actions).selectinload(PlannedAction.citations),
            selectinload(ResponsePlan.analysis),
            selectinload(ResponsePlan.approvals),
            selectinload(ResponsePlan.incident),
        )
        .where(or_(ResponsePlan.id == identifier, ResponsePlan.plan_code == identifier))
    ).first()
    if plan is None:
        raise AppError("PLAN_NOT_FOUND", "Response plan was not found.", status_code=404)
    return plan


def _resolve_incident(db: Session, identifier: str | None) -> Incident | None:
    if not identifier:
        return None
    incident = db.scalars(
        select(Incident).where(
            or_(Incident.id == identifier, Incident.incident_code == identifier)
        )
    ).first()
    if incident is None:
        raise AppError("INCIDENT_NOT_FOUND", "Incident was not found.", status_code=404)
    return incident


def _default_incident_for_plan(db: Session, plan: ResponsePlan) -> Incident | None:
    if plan.incident_id:
        return db.get(Incident, plan.incident_id)
    # Demo convenience: link fall plans to seeded INC-2026-0042 when present.
    analysis = plan.analysis
    text = f"{analysis.incident_type or ''} {analysis.summary or ''}".lower() if analysis else ""
    if "fall" in text or "person_down" in text or "person-down" in text:
        return db.scalars(
            select(Incident).where(Incident.incident_code == "INC-2026-0042")
        ).first()
    return db.scalars(select(Incident).order_by(Incident.detected_at.desc())).first()


def _latest_approval(plan: ResponsePlan) -> PlanApproval | None:
    if not plan.approvals:
        return None
    return sorted(plan.approvals, key=lambda item: item.created_at, reverse=True)[0]


def _approval_to_read(approval: PlanApproval) -> PlanApprovalRead:
    selected = []
    try:
        selected = json.loads(approval.selected_action_ids_json or "[]")
    except json.JSONDecodeError:
        selected = []
    return PlanApprovalRead(
        id=approval.id,
        approval_code=approval.approval_code,
        plan_id=approval.plan_id,
        plan_code=approval.plan.plan_code if approval.plan else None,
        incident_id=approval.incident_id,
        incident_code=approval.incident.incident_code if approval.incident else None,
        status=PlanApprovalStatus(approval.status),
        reviewer_name=approval.reviewer_name,
        notes=approval.notes,
        rejection_reason=approval.rejection_reason,
        selected_action_ids=selected if isinstance(selected, list) else [],
        correlation_id=approval.correlation_id,
        decided_at=approval.decided_at,
        is_simulated=approval.is_simulated,
        created_at=approval.created_at,
        updated_at=approval.updated_at,
    )


def _execution_to_read(execution: ActionExecution) -> ActionExecutionRead:
    return ActionExecutionRead(
        id=execution.id,
        execution_code=execution.execution_code,
        plan_id=execution.plan_id,
        action_id=execution.action_id,
        action_title=execution.action.title if execution.action else None,
        approval_id=execution.approval_id,
        idempotency_key=execution.idempotency_key,
        action_type=execution.action_type,
        requested_target=execution.requested_target,
        provider=execution.provider,
        simulation=execution.simulation,
        status=ActionExecutionStatus(execution.status),
        message=execution.message,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        failure_code=execution.failure_code,
        failure_reason=execution.failure_reason,
        external_reference=execution.external_reference,
        attempt_number=execution.attempt_number,
        correlation_id=execution.correlation_id,
        created_at=execution.created_at,
        updated_at=execution.updated_at,
    )


def record_plan_viewed(db: Session, plan_identifier: str, *, actor_name: str = "demo-reviewer") -> None:
    plan = _get_plan(db, plan_identifier)
    correlation = f"view-{plan.id}"
    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.PLAN_VIEWED,
        actor_type=AuditActorType.HUMAN,
        actor_name=actor_name,
        correlation_id=correlation,
        incident_id=plan.incident_id,
        analysis_id=plan.analysis_id,
        plan_id=plan.id,
        metadata={"plan_code": plan.plan_code},
        simulation=True,
    )
    db.commit()


def approve_plan(
    db: Session,
    plan_identifier: str,
    payload: PlanApproveRequest,
) -> PlanApprovalRead:
    plan = _get_plan(db, plan_identifier)
    if plan.status != ResponsePlanStatus.COMPLETED.value:
        raise AppError(
            "PLAN_NOT_APPROVABLE",
            "Only completed grounded response plans can be approved.",
            status_code=409,
        )
    if plan.execution_status in {
        PlanExecutionStatus.IN_PROGRESS.value,
        PlanExecutionStatus.EXECUTED.value,
        PlanExecutionStatus.PARTIALLY_FAILED.value,
    }:
        raise AppError(
            "EXECUTION_ALREADY_STARTED",
            "This plan can no longer be re-approved because execution has started.",
            status_code=409,
        )

    latest = _latest_approval(plan)
    if latest and latest.status in {
        PlanApprovalStatus.APPROVED.value,
        PlanApprovalStatus.PARTIALLY_APPROVED.value,
    }:
        raise AppError(
            "ALREADY_APPROVED",
            "This plan already has an active approval. Reject and create a new review cycle if needed.",
            status_code=409,
        )

    action_by_id = {action.id: action for action in plan.actions}
    selected = []
    for action_id in payload.selected_action_ids:
        if action_id not in action_by_id:
            raise AppError(
                "INVALID_ACTION_SELECTION",
                f"Action '{action_id}' does not belong to this plan.",
                status_code=422,
            )
        selected.append(action_id)
    if not selected:
        raise AppError(
            "INVALID_ACTION_SELECTION",
            "At least one action must be selected for approval.",
            status_code=422,
        )

    incident = _resolve_incident(db, payload.incident_identifier) or _default_incident_for_plan(db, plan)
    all_ids = {action.id for action in plan.actions}
    status = (
        PlanApprovalStatus.APPROVED
        if set(selected) == all_ids
        else PlanApprovalStatus.PARTIALLY_APPROVED
    )
    correlation_id = str(uuid4())
    approval = PlanApproval(
        id=str(uuid4()),
        approval_code=_next_code(db, PlanApproval, "approval_code", f"APR-{_year_prefix()}"),
        plan_id=plan.id,
        incident_id=incident.id if incident else None,
        status=status.value,
        reviewer_name=payload.reviewer_name,
        notes=payload.notes,
        selected_action_ids_json=json.dumps(selected),
        correlation_id=correlation_id,
        decided_at=utc_now(),
        is_simulated=True,
    )
    db.add(approval)

    for action in plan.actions:
        action.selection_status = "approved" if action.id in selected else "unselected"

    previous = plan.approval_status
    plan.approval_status = status.value
    if incident:
        plan.incident_id = incident.id

    audit_service.append_audit_event(
        db,
        event_type=(
            AuditEventType.PLAN_APPROVED
            if status == PlanApprovalStatus.APPROVED
            else AuditEventType.PLAN_PARTIALLY_APPROVED
        ),
        actor_type=AuditActorType.HUMAN,
        actor_name=payload.reviewer_name,
        correlation_id=correlation_id,
        incident_id=incident.id if incident else None,
        analysis_id=plan.analysis_id,
        plan_id=plan.id,
        metadata={
            "approval_code": approval.approval_code,
            "selected_action_ids": selected,
            "notes": payload.notes,
        },
        previous_status=previous,
        new_status=status.value,
        simulation=True,
    )
    db.commit()
    return get_plan_approval(db, plan.plan_code)


def reject_plan(
    db: Session,
    plan_identifier: str,
    payload: PlanRejectRequest,
) -> PlanApprovalRead:
    plan = _get_plan(db, plan_identifier)
    if plan.status != ResponsePlanStatus.COMPLETED.value:
        raise AppError(
            "PLAN_NOT_APPROVABLE",
            "Only completed response plans can be rejected.",
            status_code=409,
        )
    if plan.execution_status == PlanExecutionStatus.IN_PROGRESS.value:
        raise AppError(
            "EXECUTION_IN_PROGRESS",
            "Cannot reject a plan while simulated execution is in progress.",
            status_code=409,
        )
    latest = _latest_approval(plan)
    if latest and latest.status in {
        PlanApprovalStatus.APPROVED.value,
        PlanApprovalStatus.PARTIALLY_APPROVED.value,
    } and plan.execution_status not in {
        PlanExecutionStatus.NONE.value,
        PlanExecutionStatus.CANCELLED.value,
    }:
        raise AppError(
            "ALREADY_EXECUTED",
            "Approved plans with execution history cannot be rejected.",
            status_code=409,
        )

    incident = _default_incident_for_plan(db, plan)
    correlation_id = str(uuid4())
    approval = PlanApproval(
        id=str(uuid4()),
        approval_code=_next_code(db, PlanApproval, "approval_code", f"APR-{_year_prefix()}"),
        plan_id=plan.id,
        incident_id=incident.id if incident else None,
        status=PlanApprovalStatus.REJECTED.value,
        reviewer_name=payload.reviewer_name,
        notes=payload.notes,
        rejection_reason=payload.reason,
        selected_action_ids_json="[]",
        correlation_id=correlation_id,
        decided_at=utc_now(),
        is_simulated=True,
    )
    db.add(approval)
    for action in plan.actions:
        action.selection_status = "rejected"
    previous = plan.approval_status
    plan.approval_status = PlanApprovalStatus.REJECTED.value
    if incident:
        plan.incident_id = incident.id

    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.PLAN_REJECTED,
        actor_type=AuditActorType.HUMAN,
        actor_name=payload.reviewer_name,
        correlation_id=correlation_id,
        incident_id=incident.id if incident else None,
        analysis_id=plan.analysis_id,
        plan_id=plan.id,
        metadata={"reason": payload.reason, "notes": payload.notes},
        previous_status=previous,
        new_status=PlanApprovalStatus.REJECTED.value,
        simulation=True,
    )
    db.commit()
    return get_plan_approval(db, plan.plan_code)


def get_plan_approval(db: Session, plan_identifier: str) -> PlanApprovalRead:
    plan = _get_plan(db, plan_identifier)
    latest = _latest_approval(plan)
    if latest is None:
        raise AppError("APPROVAL_NOT_FOUND", "No approval record exists for this plan.", status_code=404)
    # Ensure relationships for read DTO.
    loaded = db.scalars(
        select(PlanApproval)
        .options(selectinload(PlanApproval.plan), selectinload(PlanApproval.incident))
        .where(PlanApproval.id == latest.id)
    ).one()
    return _approval_to_read(loaded)


def execute_plan(
    db: Session,
    plan_identifier: str,
    *,
    fail_action_ids: set[str] | None = None,
) -> ExecutePlanResponse:
    plan = _get_plan(db, plan_identifier)
    if plan.status != ResponsePlanStatus.COMPLETED.value:
        raise AppError(
            "PLAN_NOT_EXECUTABLE",
            "Only completed grounded plans can be executed.",
            status_code=409,
        )
    if plan.approval_status not in {
        PlanApprovalStatus.APPROVED.value,
        PlanApprovalStatus.PARTIALLY_APPROVED.value,
    }:
        raise AppError(
            "APPROVAL_REQUIRED",
            "Human approval is required before simulated execution.",
            status_code=409,
        )

    approval = _latest_approval(plan)
    if approval is None or approval.status not in {
        PlanApprovalStatus.APPROVED.value,
        PlanApprovalStatus.PARTIALLY_APPROVED.value,
    }:
        raise AppError(
            "APPROVAL_REQUIRED",
            "No active approval found for this plan.",
            status_code=409,
        )

    try:
        selected = set(json.loads(approval.selected_action_ids_json or "[]"))
    except json.JSONDecodeError:
        selected = set()

    # Idempotent: return existing executions for this approval if already created.
    existing = db.scalars(
        select(ActionExecution)
        .options(selectinload(ActionExecution.action))
        .where(ActionExecution.approval_id == approval.id)
        .order_by(ActionExecution.created_at.asc())
    ).all()
    if existing:
        return ExecutePlanResponse(
            plan_id=plan.id,
            plan_code=plan.plan_code,
            execution_status=PlanExecutionStatus(plan.execution_status),
            simulation=True,
            correlation_id=approval.correlation_id,
            executions=[_execution_to_read(item) for item in existing],
            message="Existing simulated executions returned (idempotent).",
        )

    if plan.execution_status == PlanExecutionStatus.IN_PROGRESS.value:
        raise AppError(
            "EXECUTION_IN_PROGRESS",
            "Simulated execution is already in progress for this plan.",
            status_code=409,
        )

    previous = plan.execution_status
    plan.execution_status = PlanExecutionStatus.IN_PROGRESS.value
    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.EXECUTION_REQUESTED,
        actor_type=AuditActorType.HUMAN,
        actor_name=approval.reviewer_name,
        correlation_id=approval.correlation_id,
        incident_id=plan.incident_id,
        analysis_id=plan.analysis_id,
        plan_id=plan.id,
        metadata={"approval_code": approval.approval_code, "selected_count": len(selected)},
        previous_status=previous,
        new_status=PlanExecutionStatus.IN_PROGRESS.value,
        simulation=True,
    )
    db.flush()

    executor = get_action_executor(fail_action_ids=fail_action_ids)
    results: list[ActionExecution] = []
    for action in sorted(plan.actions, key=lambda item: item.action_order):
        if action.id not in selected:
            continue
        action_type = infer_action_type(action)
        target = target_for_action(action, action_type)
        idempotency_key = f"{approval.id}:{action.id}"
        execution = ActionExecution(
            id=str(uuid4()),
            execution_code=_next_code(db, ActionExecution, "execution_code", f"EXE-{_year_prefix()}"),
            plan_id=plan.id,
            action_id=action.id,
            approval_id=approval.id,
            idempotency_key=idempotency_key,
            action_type=action_type.value,
            requested_target=target,
            provider=executor.name,
            simulation=True,
            status=ActionExecutionStatus.RUNNING.value,
            message="Simulated execution started.",
            started_at=utc_now(),
            attempt_number=1,
            correlation_id=approval.correlation_id,
        )
        db.add(execution)
        db.flush()
        audit_service.append_audit_event(
            db,
            event_type=AuditEventType.ACTION_STARTED,
            actor_type=AuditActorType.SIMULATOR,
            actor_name=executor.name,
            correlation_id=approval.correlation_id,
            incident_id=plan.incident_id,
            analysis_id=plan.analysis_id,
            plan_id=plan.id,
            execution_id=execution.id,
            metadata={"action_title": action.title, "action_type": action_type.value},
            new_status=ActionExecutionStatus.RUNNING.value,
            simulation=True,
        )

        outcome = executor.execute(action, attempt=1)
        execution.status = outcome.status.value
        execution.message = outcome.message
        execution.completed_at = utc_now()
        execution.external_reference = outcome.external_reference
        execution.failure_code = outcome.failure_code
        execution.failure_reason = outcome.failure_reason
        audit_service.append_audit_event(
            db,
            event_type=(
                AuditEventType.ACTION_SUCCEEDED
                if outcome.status == ActionExecutionStatus.COMPLETED
                else AuditEventType.ACTION_FAILED
            ),
            actor_type=AuditActorType.SIMULATOR,
            actor_name=executor.name,
            correlation_id=approval.correlation_id,
            incident_id=plan.incident_id,
            analysis_id=plan.analysis_id,
            plan_id=plan.id,
            execution_id=execution.id,
            metadata={
                "message": outcome.message,
                "external_reference": outcome.external_reference,
            },
            previous_status=ActionExecutionStatus.RUNNING.value,
            new_status=outcome.status.value,
            simulation=True,
        )
        results.append(execution)

    statuses = {item.status for item in results}
    if not results:
        plan.execution_status = PlanExecutionStatus.FAILED.value
    elif statuses == {ActionExecutionStatus.COMPLETED.value}:
        plan.execution_status = PlanExecutionStatus.EXECUTED.value
    elif ActionExecutionStatus.COMPLETED.value in statuses:
        plan.execution_status = PlanExecutionStatus.PARTIALLY_FAILED.value
    else:
        plan.execution_status = PlanExecutionStatus.FAILED.value

    db.commit()
    loaded = db.scalars(
        select(ActionExecution)
        .options(selectinload(ActionExecution.action))
        .where(ActionExecution.approval_id == approval.id)
        .order_by(ActionExecution.created_at.asc())
    ).all()
    return ExecutePlanResponse(
        plan_id=plan.id,
        plan_code=plan.plan_code,
        execution_status=PlanExecutionStatus(plan.execution_status),
        simulation=True,
        correlation_id=approval.correlation_id,
        executions=[_execution_to_read(item) for item in loaded],
        message="Simulated execution finished. No real external systems were contacted.",
    )


def list_plan_executions(db: Session, plan_identifier: str) -> list[ActionExecutionRead]:
    plan = _get_plan(db, plan_identifier)
    rows = db.scalars(
        select(ActionExecution)
        .options(selectinload(ActionExecution.action))
        .where(ActionExecution.plan_id == plan.id)
        .order_by(ActionExecution.created_at.asc())
    ).all()
    return [_execution_to_read(row) for row in rows]


def retry_execution(
    db: Session,
    execution_identifier: str,
    *,
    fail_action_ids: set[str] | None = None,
) -> ActionExecutionRead:
    execution = db.scalars(
        select(ActionExecution)
        .options(
            selectinload(ActionExecution.action),
            selectinload(ActionExecution.approval),
            selectinload(ActionExecution.plan),
        )
        .where(
            or_(
                ActionExecution.id == execution_identifier,
                ActionExecution.execution_code == execution_identifier,
            )
        )
    ).first()
    if execution is None:
        raise AppError("EXECUTION_NOT_FOUND", "Execution was not found.", status_code=404)
    if execution.status == ActionExecutionStatus.COMPLETED.value:
        raise AppError(
            "ALREADY_COMPLETED",
            "Successful simulated actions are not re-executed as new actions.",
            status_code=409,
        )
    if execution.status != ActionExecutionStatus.FAILED.value:
        raise AppError(
            "NOT_RETRYABLE",
            "Only failed simulated executions can be retried.",
            status_code=409,
        )

    approval = execution.approval
    action = execution.action
    correlation_id = approval.correlation_id if approval else execution.correlation_id
    audit_service.append_audit_event(
        db,
        event_type=AuditEventType.RETRY_REQUESTED,
        actor_type=AuditActorType.HUMAN,
        actor_name=approval.reviewer_name if approval else "demo-reviewer",
        correlation_id=correlation_id,
        incident_id=execution.plan.incident_id if execution.plan else None,
        analysis_id=execution.plan.analysis_id if execution.plan else None,
        plan_id=execution.plan_id,
        execution_id=execution.id,
        metadata={"previous_attempt": execution.attempt_number},
        simulation=True,
    )

    executor = get_action_executor(fail_action_ids=fail_action_ids)
    execution.attempt_number += 1
    execution.status = ActionExecutionStatus.RUNNING.value
    execution.started_at = utc_now()
    execution.completed_at = None
    execution.failure_code = None
    execution.failure_reason = None
    execution.message = "Simulated retry started."
    db.flush()

    outcome = executor.execute(action, attempt=execution.attempt_number)
    execution.status = outcome.status.value
    execution.message = outcome.message
    execution.completed_at = utc_now()
    execution.external_reference = outcome.external_reference
    execution.failure_code = outcome.failure_code
    execution.failure_reason = outcome.failure_reason

    audit_service.append_audit_event(
        db,
        event_type=(
            AuditEventType.ACTION_SUCCEEDED
            if outcome.status == ActionExecutionStatus.COMPLETED
            else AuditEventType.ACTION_FAILED
        ),
        actor_type=AuditActorType.SIMULATOR,
        actor_name=executor.name,
        correlation_id=correlation_id,
        incident_id=execution.plan.incident_id if execution.plan else None,
        plan_id=execution.plan_id,
        execution_id=execution.id,
        metadata={"attempt": execution.attempt_number, "message": outcome.message},
        new_status=outcome.status.value,
        simulation=True,
    )

    # Refresh plan aggregate status.
    plan = execution.plan
    if plan is not None:
        rows = db.scalars(
            select(ActionExecution).where(ActionExecution.plan_id == plan.id)
        ).all()
        statuses = {row.status for row in rows}
        if statuses == {ActionExecutionStatus.COMPLETED.value}:
            plan.execution_status = PlanExecutionStatus.EXECUTED.value
        elif ActionExecutionStatus.FAILED.value in statuses and ActionExecutionStatus.COMPLETED.value in statuses:
            plan.execution_status = PlanExecutionStatus.PARTIALLY_FAILED.value
        elif ActionExecutionStatus.FAILED.value in statuses:
            plan.execution_status = PlanExecutionStatus.FAILED.value

    db.commit()
    db.refresh(execution)
    return _execution_to_read(execution)

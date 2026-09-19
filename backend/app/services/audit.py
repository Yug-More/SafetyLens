"""Append-only application audit trail (prototype; not a compliance ledger)."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import AuditActorType, AuditEventType
from app.database.base import utc_now
from app.models.execution import AuditEvent
from app.schemas.execution import AuditEventRead


def _year_prefix() -> str:
    return str(utc_now().year)


def _next_event_code(db: Session) -> str:
    count = (
        db.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.event_code.like(f"AUD-{_year_prefix()}-%"))
        )
        or 0
    )
    return f"AUD-{_year_prefix()}-{count + 1:04d}"


def append_audit_event(
    db: Session,
    *,
    event_type: AuditEventType | str,
    actor_type: AuditActorType | str,
    actor_name: str,
    correlation_id: str,
    incident_id: str | None = None,
    analysis_id: str | None = None,
    plan_id: str | None = None,
    execution_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    previous_status: str | None = None,
    new_status: str | None = None,
    simulation: bool = True,
) -> AuditEvent:
    event = AuditEvent(
        id=str(uuid4()),
        event_code=_next_event_code(db),
        incident_id=incident_id,
        analysis_id=analysis_id,
        plan_id=plan_id,
        execution_id=execution_id,
        event_type=event_type.value if hasattr(event_type, "value") else str(event_type),
        actor_type=actor_type.value if hasattr(actor_type, "value") else str(actor_type),
        actor_name=actor_name,
        occurred_at=utc_now(),
        metadata_json=json.dumps(metadata or {}),
        previous_status=previous_status,
        new_status=new_status,
        correlation_id=correlation_id,
        simulation=simulation,
    )
    db.add(event)
    db.flush()
    return event


def audit_to_read(event: AuditEvent) -> AuditEventRead:
    meta: dict[str, Any] = {}
    if event.metadata_json:
        try:
            loaded = json.loads(event.metadata_json)
            if isinstance(loaded, dict):
                meta = loaded
        except json.JSONDecodeError:
            meta = {}
    return AuditEventRead(
        id=event.id,
        event_code=event.event_code,
        incident_id=event.incident_id,
        analysis_id=event.analysis_id,
        plan_id=event.plan_id,
        execution_id=event.execution_id,
        event_type=event.event_type,
        actor_type=event.actor_type,
        actor_name=event.actor_name,
        occurred_at=event.occurred_at,
        metadata=meta,
        previous_status=event.previous_status,
        new_status=event.new_status,
        correlation_id=event.correlation_id,
        simulation=event.simulation,
    )


def list_audit_events(
    db: Session,
    *,
    incident_id: str | None = None,
    plan_id: str | None = None,
    analysis_id: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditEventRead]:
    query = select(AuditEvent)
    if incident_id:
        query = query.where(AuditEvent.incident_id == incident_id)
    if plan_id:
        query = query.where(AuditEvent.plan_id == plan_id)
    if analysis_id:
        query = query.where(AuditEvent.analysis_id == analysis_id)
    rows = db.scalars(
        query.order_by(AuditEvent.occurred_at.asc(), AuditEvent.event_code.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [audit_to_read(row) for row in rows]

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    ActionExecutionStatus,
    PlanApprovalStatus,
    ReportStatus,
)
from app.database.base import Base, IdMixin, TimestampMixin


class PlanApproval(Base, IdMixin, TimestampMixin):
    __tablename__ = "plan_approvals"

    approval_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("response_plans.id"),
        nullable=False,
        index=True,
    )
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=PlanApprovalStatus.PENDING.value,
        index=True,
    )
    reviewer_name: Mapped[str] = mapped_column(String(120), nullable=False, default="demo-reviewer")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    selected_action_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    plan = relationship("ResponsePlan", back_populates="approvals")
    incident = relationship("Incident")
    executions = relationship("ActionExecution", back_populates="approval")


class ActionExecution(Base, IdMixin, TimestampMixin):
    __tablename__ = "action_executions"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_action_execution_idempotency"),
    )

    execution_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("response_plans.id"),
        nullable=False,
        index=True,
    )
    action_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("planned_actions.id"),
        nullable=False,
        index=True,
    )
    approval_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("plan_approvals.id"),
        nullable=False,
        index=True,
    )
    idempotency_key: Mapped[str] = mapped_column(String(120), nullable=False)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    requested_target: Mapped[str] = mapped_column(String(200), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="simulated")
    simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ActionExecutionStatus.PENDING.value,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_reference: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    plan = relationship("ResponsePlan")
    action = relationship("PlannedAction", back_populates="executions")
    approval = relationship("PlanApproval", back_populates="executions")


class AuditEvent(Base, IdMixin):
    """Append-only application audit event (prototype; not a compliance ledger)."""

    __tablename__ = "audit_events"

    event_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=True,
        index=True,
    )
    analysis_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("incident_analyses.id"),
        nullable=True,
        index=True,
    )
    plan_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("response_plans.id"),
        nullable=True,
        index=True,
    )
    execution_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("action_executions.id"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actor_type: Mapped[str] = mapped_column(String(32), nullable=False)
    actor_name: Mapped[str] = mapped_column(String(120), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    previous_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    incident = relationship("Incident")
    analysis = relationship("IncidentAnalysis")
    plan = relationship("ResponsePlan")
    execution = relationship("ActionExecution")


class IncidentReport(Base, IdMixin, TimestampMixin):
    __tablename__ = "incident_reports"

    report_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("response_plans.id"),
        nullable=True,
        index=True,
    )
    approval_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("plan_approvals.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReportStatus.COMPLETE.value,
        index=True,
    )
    simulation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    stored_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    incomplete_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    incident = relationship("Incident")
    plan = relationship("ResponsePlan")
    approval = relationship("PlanApproval")

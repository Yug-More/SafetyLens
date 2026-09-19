from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class ProcedureChunk(Base, IdMixin, TimestampMixin):
    __tablename__ = "procedure_chunks"
    __table_args__ = (
        UniqueConstraint("procedure_id", "chunk_order", name="uq_procedure_chunk_order"),
    )

    procedure_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("safety_procedures.id"),
        nullable=False,
        index=True,
    )
    chunk_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
    section_heading: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    procedure = relationship("SafetyProcedure", back_populates="chunks")


class ProcedureRetrieval(Base, IdMixin, TimestampMixin):
    __tablename__ = "procedure_retrievals"

    retrieval_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_analyses.id"),
        nullable=False,
        index=True,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False, default="lexical")
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    match_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    analysis = relationship("IncidentAnalysis")
    matches = relationship(
        "ProcedureRetrievalMatch",
        back_populates="retrieval",
        cascade="all, delete-orphan",
        order_by="ProcedureRetrievalMatch.rank",
    )


class ProcedureRetrievalMatch(Base, IdMixin, TimestampMixin):
    __tablename__ = "procedure_retrieval_matches"

    retrieval_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("procedure_retrievals.id"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("procedure_chunks.id"),
        nullable=False,
        index=True,
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[str] = mapped_column(String(32), nullable=False)

    retrieval = relationship("ProcedureRetrieval", back_populates="matches")
    chunk = relationship("ProcedureChunk")


class ResponsePlan(Base, IdMixin, TimestampMixin):
    __tablename__ = "response_plans"

    plan_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_analyses.id"),
        nullable=False,
        index=True,
    )
    retrieval_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("procedure_retrievals.id"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider_name: Mapped[str] = mapped_column(String(64), nullable=False)
    provider_model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_simulated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    limitations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
        index=True,
    )
    execution_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="none",
        index=True,
    )
    incident_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=True,
        index=True,
    )

    analysis = relationship("IncidentAnalysis")
    retrieval = relationship("ProcedureRetrieval")
    incident = relationship("Incident")
    actions = relationship(
        "PlannedAction",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlannedAction.action_order",
    )
    approvals = relationship(
        "PlanApproval",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class PlannedAction(Base, IdMixin, TimestampMixin):
    __tablename__ = "planned_actions"

    plan_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("response_plans.id"),
        nullable=False,
        index=True,
    )
    action_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    responsible_role: Mapped[str] = mapped_column(String(120), nullable=False)
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_policy_grounded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    selection_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="recommended",
    )
    # recommended | approved | rejected | unselected

    plan = relationship("ResponsePlan", back_populates="actions")
    citations = relationship(
        "PlanCitation",
        back_populates="action",
        cascade="all, delete-orphan",
    )
    executions = relationship(
        "ActionExecution",
        back_populates="action",
        cascade="all, delete-orphan",
    )


class PlanCitation(Base, IdMixin, TimestampMixin):
    __tablename__ = "plan_citations"

    action_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("planned_actions.id"),
        nullable=False,
        index=True,
    )
    chunk_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("procedure_chunks.id"),
        nullable=False,
        index=True,
    )
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)

    action = relationship("PlannedAction", back_populates="citations")
    chunk = relationship("ProcedureChunk")

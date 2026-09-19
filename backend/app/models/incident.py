from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import IncidentStatus, ReviewStatus, Severity
from app.database.base import Base, IdMixin, TimestampMixin, utc_now


class Incident(Base, IdMixin, TimestampMixin):
    __tablename__ = "incidents"

    incident_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    camera_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cameras.id"),
        nullable=False,
        index=True,
    )
    severity: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=Severity.MEDIUM.value,
        index=True,
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    evidence_summary: Mapped[str] = mapped_column(Text, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=IncidentStatus.DETECTED.value,
        index=True,
    )
    review_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ReviewStatus.PENDING.value,
    )
    matched_procedure_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("safety_procedures.id"),
        nullable=True,
    )

    camera = relationship("Camera", back_populates="incidents")
    evidence_items = relationship(
        "Evidence",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    actions = relationship(
        "RecommendedAction",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    matched_procedure = relationship("SafetyProcedure", back_populates="incidents")
    activity_events = relationship("ActivityEvent", back_populates="incident")

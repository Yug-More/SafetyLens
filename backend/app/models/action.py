from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import ActionPriority, ActionStatus
from app.database.base import Base, IdMixin, TimestampMixin


class RecommendedAction(Base, IdMixin, TimestampMixin):
    __tablename__ = "recommended_actions"

    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ActionPriority.STANDARD.value,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ActionStatus.PENDING.value,
    )
    requires_approval: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    incident = relationship("Incident", back_populates="actions")

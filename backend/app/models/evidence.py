from typing import Optional

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, utc_now
from datetime import datetime
from sqlalchemy import DateTime


class Evidence(Base, IdMixin):
    __tablename__ = "evidence"

    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incidents.id"),
        nullable=False,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    incident = relationship("Incident", back_populates="evidence_items")

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class AnalysisEvidence(Base, IdMixin, TimestampMixin):
    __tablename__ = "analysis_evidence"

    analysis_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_analyses.id"),
        nullable=False,
        index=True,
    )
    frame_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("video_frames.id"),
        nullable=False,
        index=True,
    )
    frame_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    relevance: Mapped[str] = mapped_column(String(32), nullable=False, default="supporting")
    content_url: Mapped[str] = mapped_column(String(500), nullable=False)

    analysis = relationship("IncidentAnalysis", back_populates="evidence_items")
    frame = relationship("VideoFrame")

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import JobStatus, JobType
from app.database.base import Base, IdMixin, TimestampMixin


class ProcessingJob(Base, IdMixin, TimestampMixin):
    __tablename__ = "processing_jobs"

    job_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    video_asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("video_assets.id"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=JobType.VIDEO_PREPARE.value,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=JobStatus.QUEUED.value,
        index=True,
    )
    progress: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[str] = mapped_column(String(120), nullable=False, default="queued")
    error_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    video_asset = relationship("VideoAsset", back_populates="jobs")

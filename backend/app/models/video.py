from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import VideoStatus
from app.database.base import Base, IdMixin, TimestampMixin


class VideoAsset(Base, IdMixin, TimestampMixin):
    __tablename__ = "video_assets"

    asset_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    camera_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("cameras.id"),
        nullable=True,
        index=True,
    )
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=VideoStatus.UPLOADING.value,
        index=True,
    )
    # Demo scenario selection (hackathon): person_down | ppe_compliance
    demo_scenario: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    # hard_hat_not_visible | high_visibility_vest_not_visible | both_not_visible
    demo_ppe_observation: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)

    camera = relationship("Camera")
    frames = relationship(
        "VideoFrame",
        back_populates="video_asset",
        cascade="all, delete-orphan",
    )
    jobs = relationship(
        "ProcessingJob",
        back_populates="video_asset",
        cascade="all, delete-orphan",
    )
    analyses = relationship(
        "IncidentAnalysis",
        back_populates="video_asset",
        cascade="all, delete-orphan",
    )

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, utc_now


class VideoFrame(Base, IdMixin):
    __tablename__ = "video_frames"

    video_asset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("video_assets.id"),
        nullable=False,
        index=True,
    )
    frame_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    frame_number: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    video_asset = relationship("VideoAsset", back_populates="frames")

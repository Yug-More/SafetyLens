from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import CameraStatus
from app.database.base import Base, IdMixin, TimestampMixin, utc_now


class Camera(Base, IdMixin, TimestampMixin):
    __tablename__ = "cameras"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    location: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=CameraStatus.ONLINE.value,
        index=True,
    )
    stream_status: Mapped[str] = mapped_column(String(64), nullable=False, default="connected")
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    incidents = relationship("Incident", back_populates="camera")

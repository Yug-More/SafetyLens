"""Additive platform tables; historical camera/incident schemas stay intact."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base, IdMixin, TimestampMixin, utc_now


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "platform_users"
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class UserSession(Base, IdMixin):
    __tablename__ = "platform_sessions"
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("platform_users.id"), index=True)
    csrf_token: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class LoginThrottle(Base):
    __tablename__ = "login_throttles"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class StreamEvent(Base):
    __tablename__ = "stream_events"
    __table_args__ = {"sqlite_autoincrement": True}
    sequence: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    kind: Mapped[str] = mapped_column(String(80))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )


class CameraConfiguration(Base, TimestampMixin):
    __tablename__ = "camera_configurations"
    camera_id: Mapped[str] = mapped_column(ForeignKey("cameras.id"), primary_key=True)
    facility: Mapped[str] = mapped_column(String(120), default="Default facility")
    zone: Mapped[str] = mapped_column(String(120), default="Unassigned")
    source_kind: Mapped[str] = mapped_column(String(20), default="replay")
    source_ciphertext: Mapped[str | None] = mapped_column(Text, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_json: Mapped[str] = mapped_column(Text, default="{}")
    health_details: Mapped[str] = mapped_column(String(200), default="Not connected")


class IncidentOperation(Base, TimestampMixin):
    __tablename__ = "incident_operations"
    incident_id: Mapped[str] = mapped_column(
        ForeignKey("incidents.id"), primary_key=True
    )
    assigned_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("platform_users.id"), nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    notes: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)

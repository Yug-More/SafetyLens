from __future__ import annotations

import json
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class CameraPpePolicy(Base, IdMixin, TimestampMixin):
    """Typed PPE requirements for a monitored camera / zone."""

    __tablename__ = "camera_ppe_policies"
    __table_args__ = (
        UniqueConstraint("camera_id", name="uq_camera_ppe_policies_camera"),
    )

    camera_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cameras.id"), nullable=False, index=True
    )
    zone_label: Mapped[str] = mapped_column(String(200), nullable=False)
    required_ppe_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    procedure_code: Mapped[str] = mapped_column(String(64), nullable=False, default="SOP-PPE-3.4")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    camera = relationship("Camera")

    @property
    def required_ppe(self) -> list[str]:
        try:
            data = json.loads(self.required_ppe_json or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(data, list):
            return []
        return [str(item) for item in data if str(item).strip()]

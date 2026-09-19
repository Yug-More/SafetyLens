from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import ServiceStatus
from app.database.base import Base, IdMixin, utc_now


class SystemService(Base, IdMixin):
    __tablename__ = "system_services"

    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ServiceStatus.OPERATIONAL.value,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    last_checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

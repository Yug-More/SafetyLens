from datetime import date
from typing import Optional

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, IdMixin, TimestampMixin


class SafetyProcedure(Base, IdMixin, TimestampMixin):
    __tablename__ = "safety_procedures"

    procedure_code: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    effective_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    source_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_format: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    stored_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    incidents = relationship("Incident", back_populates="matched_procedure")
    chunks = relationship(
        "ProcedureChunk",
        back_populates="procedure",
        cascade="all, delete-orphan",
        order_by="ProcedureChunk.chunk_order",
    )

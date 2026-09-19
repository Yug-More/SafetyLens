from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.core.enums import DetectorIngestionStatus
from app.schemas.common import APIModel, require_non_blank


SUPPORTED_SCHEMA_VERSION = "1.0"


class DetectorEvidencePayload(APIModel):
    clip_relative_path: str | None = None
    pre_event_seconds: float | None = None
    post_event_seconds: float | None = None
    frame_offsets_seconds: list[float] = Field(default_factory=list)


class DetectorEventPayload(APIModel):
    """Version 1 detector event contract (with Sean shape compatibility)."""

    schema_version: str
    event_id: str
    event_type: str = "possible_person_down"
    source_id: str
    camera_id: str | None = None
    track_id: str | None = None
    occurred_at: datetime | None = None
    occurred_at_seconds: float | None = None
    source_timestamp_seconds: float | None = None
    clip_event_offset_seconds: float | None = None
    state: str | None = None
    trigger_signals: list[str] = Field(default_factory=list)
    pose_quality: float | None = None
    heuristic_score: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    evidence: DetectorEvidencePayload | None = None
    limitations: list[str] = Field(default_factory=list)

    @field_validator("schema_version")
    @classmethod
    def validate_schema(cls, value: str) -> str:
        cleaned = require_non_blank(value)
        if cleaned != SUPPORTED_SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported schema_version '{cleaned}'. Expected {SUPPORTED_SCHEMA_VERSION}."
            )
        return cleaned

    @field_validator("event_id", "source_id")
    @classmethod
    def require_ids(cls, value: str) -> str:
        return require_non_blank(value)

    @field_validator("pose_quality", "heuristic_score")
    @classmethod
    def bounded_optional(cls, value: float | None) -> float | None:
        if value is None:
            return None
        if value < 0 or value > 1:
            raise ValueError("pose_quality and heuristic_score must be in [0, 1] when provided")
        return value


class DetectorEventIngestRequest(APIModel):
    event: DetectorEventPayload
    location: str = Field(default="Loading Zone B", min_length=1, max_length=200)
    auto_analyze: bool | None = None
    incident_identifier: str | None = Field(default="INC-2026-0042")

    @field_validator("location")
    @classmethod
    def clean_location(cls, value: str) -> str:
        return require_non_blank(value)


class DetectorEventRead(APIModel):
    id: str
    event_id: str
    schema_version: str
    event_type: str
    source_id: str
    camera_id: str | None = None
    camera_name: str | None = None
    track_id: str | None = None
    occurred_at: datetime | None = None
    source_timestamp_seconds: float | None = None
    clip_event_offset_seconds: float | None = None
    detector_state: str | None = None
    trigger_signals: list[str] = Field(default_factory=list)
    pose_quality: float | None = None
    pose_quality_label: str = "landmark reliability (not fall probability)"
    heuristic_score: float | None = None
    heuristic_score_note: str = (
        "Null or heuristic only — not a calibrated probability"
    )
    metrics: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)
    status: DetectorIngestionStatus
    location: str
    asset_code: str | None = None
    job_code: str | None = None
    analysis_code: str | None = None
    incident_code: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    retry_count: int = 0
    correlation_id: str
    is_simulated: bool = True
    message: str
    created_at: datetime
    updated_at: datetime


class DemoResetRequest(APIModel):
    confirmed: bool = False
    preserve_seed_incidents: bool = True

    @field_validator("confirmed")
    @classmethod
    def must_confirm(cls, value: bool) -> bool:
        if not value:
            raise ValueError("confirmed must be true to reset demo state")
        return value


class DemoResetResponse(APIModel):
    reset: bool
    message: str
    deleted_videos: int
    deleted_detector_events: int
    deleted_reports: int
    reseeding_completed: bool
    demo_mode: bool

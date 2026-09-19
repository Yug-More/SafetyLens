from datetime import datetime

from pydantic import Field, field_validator

from app.core.enums import JobStatus, JobType, VideoStatus
from app.schemas.common import APIModel, require_non_blank


class VideoAssetRead(APIModel):
    id: str
    asset_code: str
    original_filename: str
    mime_type: str
    file_size_bytes: int = Field(ge=0)
    duration_seconds: float | None = Field(default=None, ge=0)
    width: int | None = Field(default=None, ge=0)
    height: int | None = Field(default=None, ge=0)
    fps: float | None = Field(default=None, ge=0)
    frame_count: int | None = Field(default=None, ge=0)
    camera_id: str | None = None
    camera_name: str | None = None
    location: str
    status: VideoStatus
    demo_scenario: str | None = None
    demo_ppe_observation: str | None = None
    created_at: datetime
    updated_at: datetime
    content_url: str | None = None
    latest_job_code: str | None = None
    latest_job_status: JobStatus | None = None


class VideoFrameRead(APIModel):
    id: str
    frame_code: str
    video_asset_id: str
    frame_number: int = Field(ge=0)
    timestamp_seconds: float = Field(ge=0)
    width: int = Field(ge=1)
    height: int = Field(ge=1)
    created_at: datetime
    content_url: str


class ProcessingJobRead(APIModel):
    id: str
    job_code: str
    video_asset_id: str
    video_asset_code: str | None = None
    job_type: JobType
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    current_step: str
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class VideoUploadResponse(APIModel):
    asset_code: str
    job_code: str
    status: VideoStatus
    original_filename: str
    location: str
    created_at: datetime


class VideoUploadForm(APIModel):
    location: str = Field(min_length=1, max_length=200)
    camera_id: str | None = None

    @field_validator("location")
    @classmethod
    def location_not_blank(cls, value: str) -> str:
        return require_non_blank(value)

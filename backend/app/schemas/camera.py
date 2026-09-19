from datetime import datetime

from pydantic import Field, field_validator

from app.core.enums import CameraStatus
from app.schemas.common import APIModel, require_non_blank


class CameraRead(APIModel):
    id: str
    name: str
    location: str
    status: CameraStatus
    stream_status: str
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime


class CameraCreate(APIModel):
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=200)
    status: CameraStatus = CameraStatus.ONLINE
    stream_status: str = Field(default="connected", min_length=1, max_length=64)

    @field_validator("name", "location", "stream_status")
    @classmethod
    def not_blank(cls, value: str) -> str:
        return require_non_blank(value)

from datetime import datetime

from pydantic import Field, field_validator

from app.core.enums import ActionPriority, ActionStatus, IncidentStatus, ReviewStatus, Severity
from app.schemas.camera import CameraRead
from app.schemas.common import APIModel, require_non_blank
from app.schemas.procedure import ProcedureRead


class EvidenceRead(APIModel):
    id: str
    incident_id: str
    evidence_type: str
    description: str
    timestamp_seconds: float = Field(ge=0)
    media_url: str | None = None
    created_at: datetime


class RecommendedActionRead(APIModel):
    id: str
    incident_id: str
    title: str
    description: str
    priority: ActionPriority
    status: ActionStatus
    requires_approval: bool
    created_at: datetime
    updated_at: datetime


class IncidentRead(APIModel):
    id: str
    incident_code: str
    title: str
    incident_type: str
    location: str
    camera_id: str
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    evidence_summary: str
    detected_at: datetime
    status: IncidentStatus
    review_status: ReviewStatus
    matched_procedure_id: str | None = None
    created_at: datetime
    updated_at: datetime
    camera_name: str | None = None


class IncidentDetail(APIModel):
    incident: IncidentRead
    camera: CameraRead
    evidence: list[EvidenceRead]
    actions: list[RecommendedActionRead]
    matched_procedure: ProcedureRead | None = None


class IncidentCreate(APIModel):
    incident_code: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    incident_type: str = Field(min_length=1, max_length=64)
    location: str = Field(min_length=1, max_length=200)
    camera_id: str
    severity: Severity
    confidence: float = Field(ge=0, le=1)
    evidence_summary: str = Field(min_length=1)
    status: IncidentStatus = IncidentStatus.DETECTED
    review_status: ReviewStatus = ReviewStatus.PENDING
    matched_procedure_id: str | None = None

    @field_validator(
        "incident_code",
        "title",
        "incident_type",
        "location",
        "evidence_summary",
    )
    @classmethod
    def not_blank(cls, value: str) -> str:
        return require_non_blank(value)

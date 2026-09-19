from datetime import datetime

from pydantic import Field, field_validator

from app.core.enums import AnalysisSeverity, AnalysisStatus, ReviewDecision
from app.schemas.common import APIModel, require_non_blank


class AnalysisEvidenceRead(APIModel):
    id: str
    frame_id: str
    frame_code: str
    timestamp_seconds: float = Field(ge=0)
    observation: str
    relevance: str
    content_url: str


class AnalysisReviewRead(APIModel):
    id: str
    decision: ReviewDecision
    reviewer_name: str
    notes: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class IncidentAnalysisRead(APIModel):
    id: str
    analysis_code: str
    video_asset_id: str
    video_asset_code: str | None = None
    processing_job_id: str | None = None
    processing_job_code: str | None = None
    status: AnalysisStatus
    provider_name: str
    is_demo: bool
    is_simulated: bool
    incident_detected: bool | None = None
    incident_type: str | None = None
    summary: str | None = None
    detailed_analysis: str | None = None
    severity: AnalysisSeverity | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    recommended_actions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    inconclusive: bool = False
    required_ppe: list[str] = Field(default_factory=list)
    observed_ppe: list[str] = Field(default_factory=list)
    possibly_missing_ppe: list[str] = Field(default_factory=list)
    analysis_mode: str | None = None
    human_review_required: bool = True
    error_code: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    evidence: list[AnalysisEvidenceRead] = Field(default_factory=list)
    review: AnalysisReviewRead | None = None
    provider_label: str | None = None
    human_approval_required: bool = True


class AnalyzeVideoResponse(APIModel):
    analysis_code: str
    job_code: str
    status: AnalysisStatus
    provider_name: str
    is_demo: bool
    is_simulated: bool
    message: str


class AnalysisReviewCreate(APIModel):
    decision: ReviewDecision
    reviewer_name: str = Field(default="demo-reviewer", min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("reviewer_name")
    @classmethod
    def clean_reviewer(cls, value: str) -> str:
        return require_non_blank(value)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("decision")
    @classmethod
    def decision_not_pending(cls, value: ReviewDecision) -> ReviewDecision:
        if value == ReviewDecision.PENDING:
            raise ValueError("decision must not be pending")
        return value


class AIProviderInfo(APIModel):
    provider_name: str
    is_demo: bool
    is_simulated: bool
    label: str
    description: str

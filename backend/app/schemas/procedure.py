from datetime import date, datetime

from pydantic import Field, field_validator

from app.core.enums import (
    ActionPriority,
    ResponsePlanStatus,
    RetrievalMethod,
    RetrievalStatus,
)
from app.schemas.common import APIModel, require_non_blank


class ProcedureChunkRead(APIModel):
    id: str
    chunk_code: str
    chunk_order: int
    section_heading: str | None = None
    page_number: int | None = None
    content: str
    procedure_id: str
    procedure_code: str | None = None
    procedure_title: str | None = None
    procedure_version: str | None = None


class ProcedureRead(APIModel):
    id: str
    procedure_code: str
    title: str
    category: str
    version: str
    content: str
    source_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    steps: list[str] = Field(default_factory=list)
    effective_date: date | None = None
    source_filename: str | None = None
    source_format: str | None = None
    chunk_count: int = 0
    is_sample: bool = False


class ProcedureUploadResponse(APIModel):
    id: str
    procedure_code: str
    title: str
    version: str
    source_format: str
    source_filename: str
    chunk_count: int
    is_sample: bool
    message: str


class RetrievalMatchRead(APIModel):
    procedure_id: str
    procedure_code: str
    procedure_title: str
    procedure_version: str
    chunk_id: str
    chunk_code: str
    chunk_order: int
    section_heading: str | None = None
    page_number: int | None = None
    excerpt: str
    score: float
    method: str
    rank: int


class ProcedureRetrievalRead(APIModel):
    id: str
    retrieval_code: str
    analysis_id: str
    analysis_code: str | None = None
    query_text: str
    method: RetrievalMethod
    status: RetrievalStatus
    match_count: int
    message: str | None = None
    matches: list[RetrievalMatchRead] = Field(default_factory=list)
    created_at: datetime


class RetrieveProceduresRequest(APIModel):
    query: str | None = Field(default=None, max_length=2000)

    @field_validator("query")
    @classmethod
    def clean_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class PlanCitationRead(APIModel):
    id: str
    chunk_id: str
    chunk_code: str | None = None
    procedure_code: str | None = None
    procedure_title: str | None = None
    section_heading: str | None = None
    page_number: int | None = None
    excerpt: str


class PlannedActionRead(APIModel):
    id: str
    action_order: int
    title: str
    description: str
    priority: ActionPriority
    responsible_role: str
    requires_human_approval: bool
    is_policy_grounded: bool
    citations: list[PlanCitationRead] = Field(default_factory=list)


class ResponsePlanRead(APIModel):
    id: str
    plan_code: str
    analysis_id: str
    analysis_code: str | None = None
    retrieval_id: str | None = None
    retrieval_code: str | None = None
    status: ResponsePlanStatus
    summary: str | None = None
    rationale: str | None = None
    provider_name: str
    provider_model: str | None = None
    is_demo: bool
    is_simulated: bool
    provider_label: str
    limitations: list[str] = Field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    actions: list[PlannedActionRead] = Field(default_factory=list)
    recommendations_executed: bool = False
    created_at: datetime
    updated_at: datetime


class GenerateResponsePlanRequest(APIModel):
    retrieval_id: str | None = None

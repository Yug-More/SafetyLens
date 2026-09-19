from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.core.enums import (
    ActionExecutionStatus,
    PlanApprovalStatus,
    PlanExecutionStatus,
    ReportStatus,
)
from app.schemas.common import APIModel, require_non_blank


class PlanApproveRequest(APIModel):
    selected_action_ids: list[str] = Field(min_length=1)
    reviewer_name: str = Field(default="demo-reviewer", min_length=1, max_length=120)
    notes: str | None = Field(default=None, max_length=4000)
    incident_identifier: str | None = None
    confirmed: bool = False

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

    @field_validator("confirmed")
    @classmethod
    def must_confirm(cls, value: bool) -> bool:
        if not value:
            raise ValueError("confirmed must be true to approve actions")
        return value


class PlanRejectRequest(APIModel):
    reviewer_name: str = Field(default="demo-reviewer", min_length=1, max_length=120)
    reason: str | None = Field(default=None, max_length=4000)
    notes: str | None = Field(default=None, max_length=4000)

    @field_validator("reviewer_name")
    @classmethod
    def clean_reviewer(cls, value: str) -> str:
        return require_non_blank(value)


class PlanApprovalRead(APIModel):
    id: str
    approval_code: str
    plan_id: str
    plan_code: str | None = None
    incident_id: str | None = None
    incident_code: str | None = None
    status: PlanApprovalStatus
    reviewer_name: str
    notes: str | None = None
    rejection_reason: str | None = None
    selected_action_ids: list[str] = Field(default_factory=list)
    correlation_id: str
    decided_at: datetime | None = None
    is_simulated: bool = True
    created_at: datetime
    updated_at: datetime


class ActionExecutionRead(APIModel):
    id: str
    execution_code: str
    plan_id: str
    action_id: str
    action_title: str | None = None
    approval_id: str
    idempotency_key: str
    action_type: str
    requested_target: str
    provider: str
    simulation: bool
    status: ActionExecutionStatus
    message: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    failure_code: str | None = None
    failure_reason: str | None = None
    external_reference: str | None = None
    attempt_number: int
    correlation_id: str
    created_at: datetime
    updated_at: datetime


class ExecutePlanRequest(APIModel):
    confirmed: bool = False

    @field_validator("confirmed")
    @classmethod
    def must_confirm(cls, value: bool) -> bool:
        if not value:
            raise ValueError("confirmed must be true to execute approved actions")
        return value


class ExecutePlanResponse(APIModel):
    plan_id: str
    plan_code: str
    execution_status: PlanExecutionStatus
    simulation: bool = True
    correlation_id: str
    executions: list[ActionExecutionRead] = Field(default_factory=list)
    message: str


class AuditEventRead(APIModel):
    id: str
    event_code: str
    incident_id: str | None = None
    analysis_id: str | None = None
    plan_id: str | None = None
    execution_id: str | None = None
    event_type: str
    actor_type: str
    actor_name: str
    occurred_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)
    previous_status: str | None = None
    new_status: str | None = None
    correlation_id: str
    simulation: bool


class GenerateReportRequest(APIModel):
    plan_identifier: str | None = None
    force_regenerate: bool = False


class IncidentReportRead(APIModel):
    id: str
    report_code: str
    incident_id: str
    incident_code: str | None = None
    plan_id: str | None = None
    plan_code: str | None = None
    approval_id: str | None = None
    status: ReportStatus
    simulation: bool
    title: str
    summary: dict[str, Any] = Field(default_factory=dict)
    incomplete_reason: str | None = None
    download_url: str | None = None
    generated_at: datetime
    created_at: datetime
    updated_at: datetime

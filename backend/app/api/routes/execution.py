from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse, Meta
from app.schemas.execution import (
    ActionExecutionRead,
    AuditEventRead,
    ExecutePlanRequest,
    ExecutePlanResponse,
    GenerateReportRequest,
    IncidentReportRead,
    PlanApprovalRead,
    PlanApproveRequest,
    PlanRejectRequest,
)
from app.services import approval_execution as approval_service
from app.services import audit as audit_service
from app.services import reports as report_service
from app.services.reports import _resolve_incident as resolve_incident
from app.core.errors import AppError

router = APIRouter(tags=["execution"])


@router.post(
    "/api/response-plans/{plan_identifier}/approve",
    response_model=ItemResponse[PlanApprovalRead],
)
def approve_response_plan(
    plan_identifier: str,
    payload: PlanApproveRequest,
    db: Session = Depends(get_db),
) -> ItemResponse[PlanApprovalRead]:
    return ItemResponse(data=approval_service.approve_plan(db, plan_identifier, payload))


@router.post(
    "/api/response-plans/{plan_identifier}/reject",
    response_model=ItemResponse[PlanApprovalRead],
)
def reject_response_plan(
    plan_identifier: str,
    payload: PlanRejectRequest,
    db: Session = Depends(get_db),
) -> ItemResponse[PlanApprovalRead]:
    return ItemResponse(data=approval_service.reject_plan(db, plan_identifier, payload))


@router.get(
    "/api/response-plans/{plan_identifier}/approval",
    response_model=ItemResponse[PlanApprovalRead],
)
def get_response_plan_approval(
    plan_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[PlanApprovalRead]:
    return ItemResponse(data=approval_service.get_plan_approval(db, plan_identifier))


@router.post(
    "/api/response-plans/{plan_identifier}/execute",
    response_model=ItemResponse[ExecutePlanResponse],
)
def execute_response_plan(
    plan_identifier: str,
    payload: ExecutePlanRequest | None = None,
    db: Session = Depends(get_db),
) -> ItemResponse[ExecutePlanResponse]:
    request = payload or ExecutePlanRequest(confirmed=False)
    if not request.confirmed:
        raise AppError(
            "CONFIRMATION_REQUIRED",
            "confirmed must be true to execute approved simulated actions.",
            status_code=422,
        )
    return ItemResponse(data=approval_service.execute_plan(db, plan_identifier))


@router.get(
    "/api/response-plans/{plan_identifier}/executions",
    response_model=CollectionResponse[ActionExecutionRead],
)
def list_response_plan_executions(
    plan_identifier: str,
    db: Session = Depends(get_db),
) -> CollectionResponse[ActionExecutionRead]:
    data = approval_service.list_plan_executions(db, plan_identifier)
    return CollectionResponse(
        data=data,
        meta=Meta(count=len(data), limit=len(data) or 1, offset=0),
    )


@router.post(
    "/api/executions/{execution_identifier}/retry",
    response_model=ItemResponse[ActionExecutionRead],
)
def retry_execution(
    execution_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[ActionExecutionRead]:
    return ItemResponse(data=approval_service.retry_execution(db, execution_identifier))


@router.get(
    "/api/incidents/{incident_identifier}/audit",
    response_model=CollectionResponse[AuditEventRead],
)
def list_incident_audit(
    incident_identifier: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> CollectionResponse[AuditEventRead]:
    incident = resolve_incident(db, incident_identifier)
    data = audit_service.list_audit_events(
        db,
        incident_id=incident.id,
        limit=limit,
        offset=offset,
    )
    return CollectionResponse(
        data=data,
        meta=Meta(count=len(data), limit=limit, offset=offset),
    )


@router.post(
    "/api/incidents/{incident_identifier}/reports",
    response_model=ItemResponse[IncidentReportRead],
    status_code=201,
)
def create_incident_report(
    incident_identifier: str,
    payload: GenerateReportRequest | None = None,
    db: Session = Depends(get_db),
) -> ItemResponse[IncidentReportRead]:
    return ItemResponse(
        data=report_service.generate_incident_report(
            db,
            incident_identifier,
            payload,
        )
    )


@router.get(
    "/api/incidents/{incident_identifier}/reports",
    response_model=CollectionResponse[IncidentReportRead],
)
def list_reports_for_incident(
    incident_identifier: str,
    db: Session = Depends(get_db),
) -> CollectionResponse[IncidentReportRead]:
    data = report_service.list_incident_reports(db, incident_identifier)
    return CollectionResponse(
        data=data,
        meta=Meta(count=len(data), limit=len(data) or 1, offset=0),
    )


@router.get(
    "/api/reports/{report_identifier}",
    response_model=ItemResponse[IncidentReportRead],
)
def get_report(
    report_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[IncidentReportRead]:
    return ItemResponse(data=report_service.get_report(db, report_identifier))


@router.get("/api/reports/{report_identifier}/download")
def download_report(
    report_identifier: str,
    db: Session = Depends(get_db),
) -> Response:
    report, content = report_service.get_report_pdf_bytes(db, report_identifier)
    filename = f"{report.report_code}.pdf"
    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-SafetyLens-Simulation": "true",
        },
    )

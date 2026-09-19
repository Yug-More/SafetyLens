from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse, Meta
from app.services import workflow as workflow_service

router = APIRouter(tags=["workflow"])


@router.post(
    "/api/analyses/{analysis_identifier}/prepare-response",
    response_model=ItemResponse[workflow_service.WorkflowStatusRead],
)
def prepare_response(
    analysis_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[workflow_service.WorkflowStatusRead]:
    return ItemResponse(
        data=workflow_service.prepare_response_for_analysis(db, analysis_identifier)
    )


@router.get(
    "/api/analyses/{analysis_identifier}/workflow",
    response_model=ItemResponse[workflow_service.WorkflowStatusRead],
)
def get_workflow(
    analysis_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[workflow_service.WorkflowStatusRead]:
    return ItemResponse(data=workflow_service.get_workflow_status(db, analysis_identifier))


@router.get(
    "/api/notifications",
    response_model=CollectionResponse[workflow_service.OperatorNotificationRead],
)
def list_notifications(
    db: Session = Depends(get_db),
    include_dismissed: bool = Query(default=False),
) -> CollectionResponse[workflow_service.OperatorNotificationRead]:
    data = workflow_service.list_notifications(db, include_dismissed=include_dismissed)
    return CollectionResponse(data=data, meta=Meta(count=len(data), limit=50, offset=0))


@router.post(
    "/api/notifications/{notification_identifier}/dismiss",
    response_model=ItemResponse[workflow_service.OperatorNotificationRead],
)
def dismiss_notification(
    notification_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[workflow_service.OperatorNotificationRead]:
    return ItemResponse(
        data=workflow_service.dismiss_notification(db, notification_identifier)
    )

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse
from app.schemas.dashboard import ActivityEventRead, DashboardSummary
from app.services import dashboard as dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/api/dashboard/summary", response_model=ItemResponse[DashboardSummary])
def dashboard_summary(db: Session = Depends(get_db)) -> ItemResponse[DashboardSummary]:
    return ItemResponse(data=dashboard_service.get_dashboard_summary(db))


@router.get(
    "/api/dashboard/activity",
    response_model=CollectionResponse[ActivityEventRead],
)
def dashboard_activity(
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> CollectionResponse[ActivityEventRead]:
    data, meta = dashboard_service.list_activity(db, limit=limit)
    return CollectionResponse(data=data, meta=meta)

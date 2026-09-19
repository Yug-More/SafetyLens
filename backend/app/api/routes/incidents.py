from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.enums import IncidentStatus, Severity
from app.database.session import get_db
from app.schemas.common import CollectionResponse, ItemResponse
from app.schemas.incident import IncidentDetail, IncidentRead
from app.services import incidents as incident_service

router = APIRouter(tags=["incidents"])


@router.get("/api/incidents", response_model=CollectionResponse[IncidentRead])
def list_incidents(
    db: Session = Depends(get_db),
    severity: Severity | None = None,
    status: IncidentStatus | None = None,
    camera_id: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CollectionResponse[IncidentRead]:
    data, meta = incident_service.list_incidents(
        db,
        severity=severity,
        status=status,
        camera_id=camera_id,
        search=search,
        limit=limit,
        offset=offset,
    )
    return CollectionResponse(data=data, meta=meta)


@router.get(
    "/api/incidents/{incident_identifier}",
    response_model=ItemResponse[IncidentDetail],
)
def get_incident(
    incident_identifier: str,
    db: Session = Depends(get_db),
) -> ItemResponse[IncidentDetail]:
    return ItemResponse(data=incident_service.get_incident_detail(db, incident_identifier))

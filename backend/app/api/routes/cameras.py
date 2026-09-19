from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.enums import CameraStatus
from app.database.session import get_db
from app.schemas.camera import CameraRead
from app.schemas.common import CollectionResponse, ItemResponse
from app.services import cameras as camera_service

router = APIRouter(tags=["cameras"])


@router.get("/api/cameras", response_model=CollectionResponse[CameraRead])
def list_cameras(
    db: Session = Depends(get_db),
    status: CameraStatus | None = None,
    location: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> CollectionResponse[CameraRead]:
    data, meta = camera_service.list_cameras(
        db,
        status=status,
        location=location,
        search=search,
        limit=limit,
        offset=offset,
    )
    return CollectionResponse(data=data, meta=meta)


@router.get("/api/cameras/{camera_id}", response_model=ItemResponse[CameraRead])
def get_camera(camera_id: str, db: Session = Depends(get_db)) -> ItemResponse[CameraRead]:
    return ItemResponse(data=camera_service.get_camera(db, camera_id))

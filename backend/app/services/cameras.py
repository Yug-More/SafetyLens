from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.enums import CameraStatus
from app.core.errors import AppError
from app.models.camera import Camera
from app.schemas.camera import CameraRead
from app.schemas.common import Meta


def list_cameras(
    db: Session,
    *,
    status: CameraStatus | None = None,
    location: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[CameraRead], Meta]:
    query = select(Camera)
    if status is not None:
        query = query.where(Camera.status == status.value)
    if location:
        query = query.where(Camera.location.ilike(f"%{location}%"))
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Camera.name.ilike(pattern), Camera.location.ilike(pattern)))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(Camera.name.asc()).limit(limit).offset(offset)
    ).all()
    return [CameraRead.model_validate(row) for row in rows], Meta(
        count=total,
        limit=limit,
        offset=offset,
    )


def get_camera(db: Session, camera_id: str) -> CameraRead:
    camera = db.get(Camera, camera_id)
    if camera is None:
        raise AppError("NOT_FOUND", "Camera not found", status_code=404)
    return CameraRead.model_validate(camera)

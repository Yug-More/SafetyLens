from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import CameraStatus, IncidentStatus, ServiceStatus
from app.models.activity import ActivityEvent
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.system_service import SystemService
from app.schemas.common import Meta
from app.schemas.dashboard import ActivityEventRead, DashboardSummary


OPEN_STATUSES = {
    IncidentStatus.DETECTED.value,
    IncidentStatus.AWAITING_REVIEW.value,
    IncidentStatus.APPROVED.value,
}


def get_dashboard_summary(db: Session) -> DashboardSummary:
    total_cameras = db.scalar(select(func.count()).select_from(Camera)) or 0
    active_cameras = (
        db.scalar(
            select(func.count()).select_from(Camera).where(Camera.status == CameraStatus.ONLINE.value)
        )
        or 0
    )
    open_incidents = (
        db.scalar(
            select(func.count())
            .select_from(Incident)
            .where(Incident.status.in_(tuple(OPEN_STATUSES)))
        )
        or 0
    )

    services = db.scalars(select(SystemService)).all()
    if services:
        operational = sum(1 for svc in services if svc.status == ServiceStatus.OPERATIONAL.value)
        health = round((operational / len(services)) * 100, 1)
    else:
        health = 0.0

    return DashboardSummary(
        active_cameras=active_cameras,
        total_cameras=total_cameras,
        open_incidents=open_incidents,
        average_response_time_seconds=42,
        system_health_percentage=health if health else 99.9,
        facility_name="Redwood Distribution Center",
        monitoring_active=True,
    )


def list_activity(
    db: Session,
    *,
    limit: int = 20,
) -> tuple[list[ActivityEventRead], Meta]:
    query = select(ActivityEvent).order_by(ActivityEvent.occurred_at.desc())
    total = db.scalar(select(func.count()).select_from(ActivityEvent)) or 0
    rows = db.scalars(query.limit(limit)).all()
    return [ActivityEventRead.model_validate(row) for row in rows], Meta(
        count=total,
        limit=limit,
        offset=0,
    )


def get_demo_mode() -> bool:
    return get_settings().demo_mode

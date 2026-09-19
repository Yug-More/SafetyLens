from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import ServiceStatus
from app.models.system_service import SystemService
from app.schemas.system import SystemServiceRead, SystemStatusRead


def get_system_status(db: Session) -> SystemStatusRead:
    services = [
        SystemServiceRead.model_validate(row)
        for row in db.scalars(select(SystemService).order_by(SystemService.name.asc())).all()
    ]

    if not services:
        overall = ServiceStatus.OFFLINE
    elif any(svc.status == ServiceStatus.OFFLINE for svc in services):
        overall = ServiceStatus.OFFLINE
    elif any(svc.status == ServiceStatus.DEGRADED for svc in services):
        overall = ServiceStatus.DEGRADED
    else:
        overall = ServiceStatus.OPERATIONAL

    return SystemStatusRead(
        services=services,
        overall_status=overall,
        demo_environment=get_settings().demo_mode,
    )

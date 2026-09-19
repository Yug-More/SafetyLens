from datetime import datetime

from app.core.enums import ServiceStatus
from app.schemas.common import APIModel


class SystemServiceRead(APIModel):
    id: str
    name: str
    status: ServiceStatus
    message: str
    last_checked_at: datetime


class SystemStatusRead(APIModel):
    services: list[SystemServiceRead]
    overall_status: ServiceStatus
    demo_environment: bool

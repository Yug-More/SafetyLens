from datetime import datetime

from app.schemas.common import APIModel


class DashboardSummary(APIModel):
    active_cameras: int
    total_cameras: int
    open_incidents: int
    average_response_time_seconds: int
    system_health_percentage: float
    facility_name: str
    monitoring_active: bool


class ActivityEventRead(APIModel):
    id: str
    event_type: str
    title: str
    description: str
    incident_id: str | None = None
    status: str
    occurred_at: datetime

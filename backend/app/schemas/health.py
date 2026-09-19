from datetime import datetime

from app.schemas.common import APIModel


class HealthRead(APIModel):
    status: str
    app_name: str
    environment: str
    demo_mode: bool
    database_status: str
    timestamp: datetime


class DemoInfo(APIModel):
    demo_mode: bool
    facility: str
    scenario: str
    description: str
    simulated_capabilities: list[str]
    limitations: list[str]

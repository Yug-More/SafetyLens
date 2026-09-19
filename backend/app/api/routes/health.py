from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.database.session import get_db
from app.schemas.common import ItemResponse
from app.schemas.health import HealthRead

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=ItemResponse[HealthRead])
def health(db: Session = Depends(get_db)) -> ItemResponse[HealthRead]:
    settings = get_settings()
    database_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unavailable"

    return ItemResponse(
        data=HealthRead(
            status="ok" if database_status == "ok" else "degraded",
            app_name=settings.app_name,
            environment=settings.environment,
            demo_mode=settings.demo_mode,
            database_status=database_status,
            timestamp=datetime.now(timezone.utc),
        )
    )

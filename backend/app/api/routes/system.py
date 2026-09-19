from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import ItemResponse
from app.schemas.health import DemoInfo
from app.schemas.system import SystemStatusRead
from app.services import demo as demo_service
from app.services import system as system_service

router = APIRouter(tags=["system"])


@router.get("/api/system/status", response_model=ItemResponse[SystemStatusRead])
def system_status(db: Session = Depends(get_db)) -> ItemResponse[SystemStatusRead]:
    return ItemResponse(data=system_service.get_system_status(db))


@router.get("/api/demo/info", response_model=ItemResponse[DemoInfo])
def demo_info() -> ItemResponse[DemoInfo]:
    return ItemResponse(data=demo_service.get_demo_info())

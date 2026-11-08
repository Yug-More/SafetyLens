from fastapi import APIRouter, Depends
from app.services.auth import authorize

from app.api.routes import (
    analysis,
    cameras,
    dashboard,
    detector,
    execution,
    health,
    incidents,
    ppe,
    procedures,
    system,
    videos,
    workflow,
)

api_router = APIRouter(dependencies=[Depends(authorize)])
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(cameras.router)
api_router.include_router(incidents.router)
api_router.include_router(procedures.router)
api_router.include_router(system.router)
api_router.include_router(videos.router)
api_router.include_router(analysis.router)
api_router.include_router(execution.router)
api_router.include_router(detector.router)
api_router.include_router(workflow.router)
api_router.include_router(ppe.router)

from app.api.routes.platform import router as platform_router
api_router.include_router(platform_router)

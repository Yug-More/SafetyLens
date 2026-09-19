from fastapi import APIRouter

from app.api.routes import (
    analysis,
    cameras,
    dashboard,
    execution,
    health,
    incidents,
    procedures,
    system,
    videos,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(cameras.router)
api_router.include_router(incidents.router)
api_router.include_router(procedures.router)
api_router.include_router(system.router)
api_router.include_router(videos.router)
api_router.include_router(analysis.router)
api_router.include_router(execution.router)

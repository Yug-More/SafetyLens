from fastapi import APIRouter

from app.api.routes import cameras, dashboard, health, incidents, procedures, system, videos, analysis

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(dashboard.router)
api_router.include_router(cameras.router)
api_router.include_router(incidents.router)
api_router.include_router(procedures.router)
api_router.include_router(system.router)
api_router.include_router(videos.router)
api_router.include_router(analysis.router)

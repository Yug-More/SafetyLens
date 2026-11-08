from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.api.routes.auth import router as auth_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.database.session import init_db
from app.services.storage import ensure_storage_directories


@asynccontextmanager
async def lifespan(_: FastAPI):
    cfg = get_settings()
    if cfg.environment == "production" and (not cfg.auth_enabled or not cfg.cookie_secure):
        raise RuntimeError("Production requires AUTH_ENABLED=true and COOKIE_SECURE=true behind HTTPS")
    init_db()
    ensure_storage_directories()
    from app.services.recovery import snapshot_interrupted_events, recover_events
    event_ids = snapshot_interrupted_events()
    recovery = asyncio.create_task(asyncio.to_thread(recover_events,event_ids)) if event_ids else None
    try:
        yield
    finally:
        if recovery:
            try:
                await asyncio.wait_for(asyncio.shield(recovery),timeout=5)
            except asyncio.TimeoutError:
                logging.getLogger(__name__).warning("Recovery still active on shutdown; unfinished work remains persisted")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.7.0",
        description=(
            "SafetyLens Stage 7 API — detector event handoff, demo reset, "
            "human approval, simulated execution, audit trail, and PDF reports."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    @app.middleware("http")
    async def response_safeguards(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(api_router)
    return app


app = create_app()

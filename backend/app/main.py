from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.database.session import init_db
from app.services.storage import ensure_storage_directories


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    ensure_storage_directories()
    yield


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
        allow_methods=["GET", "POST", "PUT", "PATCH", "OPTIONS"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()

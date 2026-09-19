from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.database.base import Base

settings = get_settings()

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record) -> None:  # noqa: ANN001
    if settings.database_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def init_db() -> None:
    # Import models so metadata is registered.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_columns()


def _ensure_sqlite_columns() -> None:
    """Add newly introduced columns on existing SQLite databases."""
    if not settings.database_url.startswith("sqlite"):
        return
    from sqlalchemy import text

    statements = [
        ("video_assets", "demo_scenario", "ALTER TABLE video_assets ADD COLUMN demo_scenario VARCHAR(64)"),
        (
            "video_assets",
            "demo_ppe_observation",
            "ALTER TABLE video_assets ADD COLUMN demo_ppe_observation VARCHAR(80)",
        ),
        (
            "incident_analyses",
            "required_ppe_json",
            "ALTER TABLE incident_analyses ADD COLUMN required_ppe_json TEXT",
        ),
        (
            "incident_analyses",
            "observed_ppe_json",
            "ALTER TABLE incident_analyses ADD COLUMN observed_ppe_json TEXT",
        ),
        (
            "incident_analyses",
            "possibly_missing_ppe_json",
            "ALTER TABLE incident_analyses ADD COLUMN possibly_missing_ppe_json TEXT",
        ),
        (
            "incident_analyses",
            "analysis_mode",
            "ALTER TABLE incident_analyses ADD COLUMN analysis_mode VARCHAR(64)",
        ),
        (
            "incident_analyses",
            "human_review_required",
            "ALTER TABLE incident_analyses ADD COLUMN human_review_required BOOLEAN DEFAULT 1",
        ),
    ]
    with engine.begin() as conn:
        for table, column, ddl in statements:
            rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            names = {row[1] for row in rows}
            if column not in names:
                conn.execute(text(ddl))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

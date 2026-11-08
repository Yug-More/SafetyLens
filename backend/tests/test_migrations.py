from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from app.database.base import Base
from app.core.config import get_settings
from app import models


def test_migration_adopts_legacy_data_and_is_repeatable(tmp_path, monkeypatch):
    path = tmp_path / "legacy.db"
    url = f"sqlite:///{path}"
    engine = create_engine(url)
    platform = {
        "platform_users",
        "platform_sessions",
        "login_throttles",
        "stream_events",
        "camera_configurations",
        "incident_operations",
    }
    Base.metadata.create_all(
        engine,
        tables=[x for x in Base.metadata.sorted_tables if x.name not in platform],
    )
    with engine.begin() as db:
        db.execute(
            text(
                "INSERT INTO cameras(id,name,location,status,stream_status,last_seen_at) VALUES ('preserved','Historical camera','Dock','offline','disconnected',CURRENT_TIMESTAMP)"
            )
        )
    monkeypatch.setenv("DATABASE_URL", url)
    get_settings.cache_clear()
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")
    command.upgrade(cfg, "head")
    assert platform <= set(inspect(engine).get_table_names())
    with engine.connect() as db:
        assert (
            db.execute(
                text("SELECT name FROM cameras WHERE id='preserved'")
            ).scalar_one()
            == "Historical camera"
        )
        assert (
            db.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0001_platform"
        )
    engine.dispose()
    get_settings.cache_clear()

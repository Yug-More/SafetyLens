from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.database.base import Base
from app.database.session import get_db
from app.main import create_app
from app.seed.seed_data import seed_database
from app.services.storage import ensure_storage_directories


@pytest.fixture()
def temp_media(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    uploads = tmp_path / "uploads"
    frames = tmp_path / "frames"
    procedures = tmp_path / "procedures"
    uploads.mkdir()
    frames.mkdir()
    procedures.mkdir()
    monkeypatch.setenv("UPLOAD_DIRECTORY", str(uploads))
    monkeypatch.setenv("FRAME_DIRECTORY", str(frames))
    monkeypatch.setenv("PROCEDURE_DIRECTORY", str(procedures))
    monkeypatch.setenv("MAX_VIDEO_SIZE_MB", "5")
    monkeypatch.setenv("MAX_VIDEO_DURATION_SECONDS", "30")
    monkeypatch.setenv("FRAME_SAMPLE_COUNT", "8")
    monkeypatch.setenv("AI_PROVIDER", "demo")
    monkeypatch.setenv("AI_DEMO_MODE", "true")
    monkeypatch.setenv("PLANNER_PROVIDER", "demo")
    monkeypatch.setenv("MAX_PROCEDURE_SIZE_MB", "5")
    get_settings.cache_clear()
    ensure_storage_directories()
    yield tmp_path
    get_settings.cache_clear()


@pytest.fixture()
def db_engine(temp_media: Path):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def db_session(db_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    seed_database(session)
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(
    db_engine,
    db_session: Session,
    temp_media: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[TestClient, None, None]:
    TestingSessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr("app.services.videos.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("app.services.analysis.SessionLocal", TestingSessionLocal)

    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_test_video(
    path: Path,
    *,
    frames: int = 24,
    fps: int = 8,
    width: int = 320,
    height: int = 240,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    assert writer.isOpened()
    for index in range(frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (index * 9 % 255, 40, 120)
        cv2.putText(
            frame,
            f"F{index}",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        writer.write(frame)
    writer.release()
    return path

"""Isolated browser-test backend. Never touches an existing SafetyLens database."""

import os
from pathlib import Path
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
data = Path(tempfile.mkdtemp(prefix="safetylens-browser-test-"))
os.environ.update(
    DATABASE_URL=f"sqlite:///{data}/test.db",
    ENVIRONMENT="test",
    AUTH_ENABLED="true",
    COOKIE_SECURE="false",
    DEMO_MODE="true",
    FRONTEND_ORIGINS="http://127.0.0.1:3100",
    UPLOAD_DIRECTORY=str(data / "uploads"),
    FRAME_DIRECTORY=str(data / "frames"),
    PROCEDURE_DIRECTORY=str(data / "procedures"),
    REPORT_DIRECTORY=str(data / "reports"),
    DETECTOR_EVENTS_DIRECTORY=str(data / "detector-events"),
)
from cryptography.fernet import Fernet

os.environ["CAMERA_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
from app.database.session import init_db, SessionLocal
from app.seed.seed_data import seed_database
from app.services.auth import create_user

init_db()
with SessionLocal() as db:
    seed_database(db)
    create_user(db, "qa-admin", os.environ["SAFETYLENS_E2E_PASSWORD"], "administrator")
    create_user(db, "qa-viewer", os.environ["SAFETYLENS_E2E_PASSWORD"], "viewer")
import uvicorn

uvicorn.run("app.main:app", host="127.0.0.1", port=8107, log_level="warning")

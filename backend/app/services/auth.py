"""Single-installation local authentication: opaque revocable sessions and scrypt."""

from __future__ import annotations
import hashlib
import hmac
import secrets
from datetime import timedelta, timezone
from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.errors import AppError
from app.database.base import utc_now
from app.database.session import get_db
from app.models.platform import User, UserSession

ROLES = {"administrator", "safety_manager", "safety_operator", "viewer"}
COOKIE = "safetylens_session"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str) -> str:
    if len(password) < 12 or len(password) > 1024:
        raise ValueError("Password must contain 12–1024 characters")
    salt = secrets.token_hex(16)
    value = hashlib.scrypt(
        password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
    ).hex()
    return f"scrypt${salt}${value}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, salt, expected = encoded.split("$")
        if algorithm != "scrypt" or len(password) > 1024:
            return False
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1
        ).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def as_utc(value):
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def session_user(request: Request, db: Session) -> tuple[User, UserSession]:
    raw = request.cookies.get(COOKIE, "")
    session = (
        db.scalar(select(UserSession).where(UserSession.token_hash == digest(raw)))
        if raw
        else None
    )
    user = db.get(User, session.user_id) if session else None
    if (
        not session
        or as_utc(session.expires_at) <= utc_now()
        or not user
        or not user.active
    ):
        raise AppError("AUTHENTICATION_REQUIRED", "Sign in to access SafetyLens.", 401)
    return user, session


def check_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in get_settings().cors_origins:
        raise AppError("ORIGIN_REJECTED", "Request origin is not allowed.", 403)


def authorize(request: Request, db: Session = Depends(get_db)) -> dict:
    cfg = get_settings()
    path = request.url.path
    if path in {"/api/health", "/api/demo/info"}:
        return {}
    if not cfg.auth_enabled:
        if cfg.environment == "production":
            raise AppError(
                "AUTH_REQUIRED", "Authentication cannot be disabled in production.", 503
            )
        actor = {
            "id": None,
            "username": "demo-reviewer",
            "role": "administrator",
            "mode": "demo",
        }
        request.state.actor = actor
        return actor
    bearer = request.headers.get("authorization", "")
    if (
        path == "/api/detector/events"
        or path == "/api/detector/heartbeat"
        or path.startswith(("/api/detector/snapshot/", "/api/detector/config/"))
    ) and bearer.startswith("Bearer "):
        token = bearer[7:]
        if cfg.detector_api_token and hmac.compare_digest(
            token, cfg.detector_api_token
        ):
            actor = {
                "id": None,
                "username": "detector-device",
                "role": "device",
                "mode": "device",
            }
            request.state.actor = actor
            return actor
        raise AppError("INVALID_DEVICE_TOKEN", "Invalid detector credential.", 401)
    user, session = session_user(request, db)
    actor = {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "mode": "session",
    }
    request.state.actor = actor
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        check_origin(request)
        if not hmac.compare_digest(
            request.headers.get("x-csrf-token", ""), session.csrf_token
        ):
            raise AppError(
                "CSRF_REQUIRED", "Refresh the session before making changes.", 403
            )
        if path == "/api/auth/logout":
            return actor
        required = {"administrator", "safety_manager", "safety_operator"}
        if (
            "/approve" in path
            or "/execute" in path
            or "/executions/" in path
            or "/reject" in path
            or "/operations" in path
        ):
            required = {"administrator", "safety_manager"}
        if path.startswith(
            ("/api/cameras", "/api/users", "/api/demo/reset", "/api/retention")
        ):
            required = {"administrator"}
        if user.role not in required:
            raise AppError("FORBIDDEN", "Your role cannot perform this operation.", 403)
    return actor


def create_user(db: Session, username: str, password: str, role: str) -> User:
    username = username.strip().lower()
    if role not in ROLES or not username or len(username) > 120:
        raise ValueError("Invalid username or role")
    if db.scalar(select(User).where(User.username == username)):
        raise ValueError("Username already exists")
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

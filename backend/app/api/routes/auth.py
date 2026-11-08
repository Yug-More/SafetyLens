from datetime import timedelta
import secrets
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.errors import AppError
from app.database.base import utc_now
from app.database.session import get_db
from app.models.platform import LoginThrottle, User, UserSession
from app.services import auth
from app.services.audit import append_audit_event

router = APIRouter(tags=["authentication"])


class Login(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=1024)


class UserCreate(Login):
    role: str


@router.post("/api/auth/login")
def login(
    payload: Login, request: Request, response: Response, db: Session = Depends(get_db)
):
    auth.check_origin(request)
    now = utc_now()
    key = auth.digest(request.client.host if request.client else "unknown")
    throttle = db.get(LoginThrottle, key)
    if throttle is None:
        throttle = LoginThrottle(key=key, attempts=0, window_start=now)
        db.add(throttle)
    if (now - auth.as_utc(throttle.window_start)).total_seconds() >= 900:
        throttle.attempts, throttle.window_start = 0, now
    if throttle.attempts >= 10:
        raise AppError(
            "LOGIN_THROTTLED", "Too many attempts. Try again after 15 minutes.", 429
        )
    user = db.scalar(
        select(User).where(User.username == payload.username.strip().lower())
    )
    # A fixed-cost dummy hash prevents unknown-account fast-path timing.
    encoded = user.password_hash if user else _DUMMY_HASH
    valid = auth.verify_password(payload.password, encoded)
    if not user or not user.active or not valid:
        throttle.attempts += 1
        db.commit()
        raise AppError("INVALID_LOGIN", "Invalid username or password.", 401)
    throttle.attempts = 0
    raw, csrf = secrets.token_urlsafe(32), secrets.token_hex(32)
    cfg = get_settings()
    db.execute(delete(UserSession).where(UserSession.expires_at < now))
    db.add(
        UserSession(
            token_hash=auth.digest(raw),
            user_id=user.id,
            csrf_token=csrf,
            expires_at=now + timedelta(seconds=cfg.session_lifetime_seconds),
        )
    )
    append_audit_event(
        db,
        event_type="login",
        actor_type="human",
        actor_name=user.username,
        correlation_id=secrets.token_hex(16),
        simulation=False,
    )
    db.commit()
    response.set_cookie(
        auth.COOKIE,
        raw,
        httponly=True,
        secure=cfg.cookie_secure,
        samesite="strict",
        max_age=cfg.session_lifetime_seconds,
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {
        "data": {
            "username": user.username,
            "role": user.role,
            "csrf_token": csrf,
            "mode": "session",
        }
    }


_DUMMY_HASH = auth.hash_password(secrets.token_urlsafe(24))


@router.get("/api/auth/me")
def me(request: Request, response: Response, db: Session = Depends(get_db)):
    response.headers["Cache-Control"] = "no-store"
    if not get_settings().auth_enabled and get_settings().environment != "production":
        return {
            "data": {
                "username": "demo-reviewer",
                "role": "administrator",
                "csrf_token": "",
                "mode": "demo",
            }
        }
    user, session = auth.session_user(request, db)
    return {
        "data": {
            "username": user.username,
            "role": user.role,
            "csrf_token": session.csrf_token,
            "mode": "session",
        }
    }


@router.post("/api/auth/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    auth.authorize(request, db)
    raw = request.cookies.get(auth.COOKIE, "")
    db.execute(delete(UserSession).where(UserSession.token_hash == auth.digest(raw)))
    db.commit()
    response.delete_cookie(
        auth.COOKIE, path="/", samesite="strict", secure=get_settings().cookie_secure
    )
    return {"data": {"logged_out": True}}


@router.post("/api/users", dependencies=[Depends(auth.authorize)], status_code=201)
def add_user(payload: UserCreate, request: Request, db: Session = Depends(get_db)):
    try:
        user = auth.create_user(db, payload.username, payload.password, payload.role)
    except ValueError as exc:
        raise AppError("INVALID_USER", str(exc), 422) from exc
    append_audit_event(
        db,
        event_type="user_created",
        actor_type="human",
        actor_name=request.state.actor["username"],
        correlation_id=secrets.token_hex(16),
        metadata={"user_id": user.id, "role": user.role},
        simulation=False,
    )
    db.commit()
    return {"data": {"id": user.id, "username": user.username, "role": user.role}}


class UserUpdate(BaseModel):
    role: str
    active: bool


@router.get("/api/users", dependencies=[Depends(auth.authorize)])
def list_users(request: Request, db: Session = Depends(get_db)):
    if request.state.actor["role"] not in {"administrator", "safety_manager"}:
        raise AppError("FORBIDDEN", "Manager access required.", 403)
    return {
        "data": [
            {"id": x.id, "username": x.username, "role": x.role, "active": x.active}
            for x in db.scalars(select(User).order_by(User.username)).all()
        ]
    }


@router.patch("/api/users/{user_id}", dependencies=[Depends(auth.authorize)])
def update_user(
    user_id: str, payload: UserUpdate, request: Request, db: Session = Depends(get_db)
):
    from sqlalchemy import func

    user = db.get(User, user_id)
    if not user:
        raise AppError("USER_NOT_FOUND", "User not found.", 404)
    if payload.role not in auth.ROLES:
        raise AppError("INVALID_ROLE", "Unsupported role.", 422)
    admins = db.scalar(
        select(func.count())
        .select_from(User)
        .where(User.role == "administrator", User.active.is_(True))
    )
    if (
        user.role == "administrator"
        and user.active
        and admins <= 1
        and (not payload.active or payload.role != "administrator")
    ):
        raise AppError(
            "LAST_ADMINISTRATOR", "Keep at least one active administrator.", 409
        )
    user.role, user.active = payload.role, payload.active
    db.execute(delete(UserSession).where(UserSession.user_id == user.id))
    append_audit_event(
        db,
        event_type="user_access_changed",
        actor_type="human",
        actor_name=request.state.actor["username"],
        correlation_id=secrets.token_hex(16),
        metadata={"user_id": user.id, "role": user.role, "active": user.active},
        simulation=False,
    )
    db.commit()
    return {
        "data": {
            "id": user.id,
            "role": user.role,
            "active": user.active,
            "sessions_revoked": True,
        }
    }

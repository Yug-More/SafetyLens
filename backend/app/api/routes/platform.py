"""Authenticated camera operations, incident coordination, analytics and resumable events."""

from __future__ import annotations
import asyncio
import csv
import io
import json
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select, delete
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.errors import AppError
from app.database.base import utc_now
from app.database.session import get_db, SessionLocal
from app.models.camera import Camera
from app.models.incident import Incident
from app.models.incident_analysis import IncidentAnalysis
from app.models.analysis_review import AnalysisReview
from app.models.platform import (
    CameraConfiguration,
    IncidentOperation,
    StreamEvent,
    User,
)
from app.models.ppe_policy import CameraPpePolicy
from app.models.video import VideoAsset
from app.services.audit import append_audit_event
from app.services.auth import authorize, as_utc, session_user

router = APIRouter(tags=["platform"], dependencies=[Depends(authorize)])


class DetectionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    detectors: list[Literal["fall", "ppe", "camera_health"]] = Field(
        default_factory=lambda: ["fall", "camera_health"], max_length=3
    )
    confidence_threshold: float = Field(default=0.5, ge=0.05, le=0.99)
    sample_fps: float = Field(default=8, ge=1, le=30)
    pose_region: tuple[float, float, float, float] | None = None

    @field_validator("pose_region")
    @classmethod
    def valid_region(cls, value):
        if value is not None:
            x1, y1, x2, y2 = value
            if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
                raise ValueError("pose_region must be normalized nonempty xyxy")
        return value
    pre_event_seconds: float = Field(default=3, ge=0.5, le=30)
    post_event_seconds: float = Field(default=3, ge=0.5, le=30)
    retention_days: int = Field(default=30, ge=1, le=3650)
    required_ppe: list[Literal["hard_hat", "high_visibility_vest"]] = Field(
        default_factory=list, max_length=2
    )


class CameraInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=200)
    facility: str = Field(default="Default facility", min_length=1, max_length=120)
    zone: str = Field(default="Unassigned", min_length=1, max_length=120)
    source_kind: Literal["webcam", "rtsp", "network", "replay", "simulator"] = "replay"
    source: str | None = Field(default=None, max_length=2048)
    enabled: bool = False
    policy: DetectionPolicy = Field(default_factory=DetectionPolicy)

    @field_validator("name", "location", "facility", "zone")
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError("Must not be blank")
        return value.strip()


class Heartbeat(BaseModel):
    camera_id: str
    status: Literal["online", "offline", "degraded"]
    frames_processed: int = Field(default=0, ge=0)
    dropped_frames: int | None = Field(default=None, ge=0)
    processing_fps: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class OperationInput(BaseModel):
    version: int = Field(ge=1)
    assigned_user_id: str | None = None
    notes: str = Field(default="", max_length=4000)
    acknowledge: bool = False
    resolve: bool = False


def emit(db, kind, payload):
    db.add(StreamEvent(kind=kind, payload_json=json.dumps(payload)))


def configuration(db, camera_id):
    camera = db.get(Camera, camera_id)
    if not camera:
        raise AppError("CAMERA_NOT_FOUND", "Camera not found.", 404)
    return camera, db.get(CameraConfiguration, camera_id)


def encrypted_source(value: str):
    from cryptography.fernet import Fernet

    key = get_settings().camera_encryption_key
    if not key:
        raise AppError(
            "ENCRYPTION_REQUIRED",
            "Configure CAMERA_ENCRYPTION_KEY before saving a camera source.",
            409,
        )
    return Fernet(key.encode()).encrypt(value.encode()).decode()


def view(camera, cfg):
    age = max(0, (utc_now() - as_utc(camera.last_seen_at)).total_seconds())
    return {
        "id": camera.id,
        "name": camera.name,
        "location": camera.location,
        "status": camera.status if age < 30 else "offline",
        "heartbeat_age_seconds": round(age, 1),
        "facility": cfg.facility if cfg else "Historical demo",
        "zone": cfg.zone if cfg else camera.location,
        "source_kind": cfg.source_kind if cfg else "demo",
        "source_configured": bool(cfg and cfg.source_ciphertext),
        "enabled": bool(cfg and cfg.enabled),
        "policy": json.loads(cfg.policy_json) if cfg else {},
        "health_details": cfg.health_details
        if cfg
        else "Seeded metadata; not an active connection",
        "snapshot_url": f"/api/cameras/{camera.id}/snapshot",
        "capability_status": "experimental" if cfg else "demo_simulation",
    }


@router.get("/api/camera-management")
def camera_inventory(db: Session = Depends(get_db)):
    cameras = db.scalars(select(Camera).order_by(Camera.name)).all()
    return {"data": [view(x, db.get(CameraConfiguration, x.id)) for x in cameras]}


def save_camera(db, payload, camera_id=None):
    duplicate = db.scalar(select(Camera).where(Camera.name == payload.name))
    if duplicate and duplicate.id != camera_id:
        raise AppError("DUPLICATE_CAMERA", "Camera name is already in use.", 409)
    camera = (
        db.get(Camera, camera_id)
        if camera_id
        else Camera(
            name=payload.name,
            location=payload.location,
            status="offline",
            stream_status="disconnected",
        )
    )
    if camera is None:
        raise AppError("CAMERA_NOT_FOUND", "Camera not found.", 404)
    db.add(camera)
    db.flush()
    cfg = db.get(CameraConfiguration, camera.id)
    if cfg is None:
        cfg = CameraConfiguration(camera_id=camera.id)
        db.add(cfg)
    if payload.source:
        from urllib.parse import urlparse

        if payload.source_kind == "webcam" and not payload.source.isdigit():
            raise AppError(
                "INVALID_SOURCE",
                "Webcam source must be a non-negative camera index.",
                422,
            )
        if payload.source_kind in {"rtsp", "network"} and urlparse(
            payload.source
        ).scheme not in {"rtsp", "rtsps", "http", "https"}:
            raise AppError("INVALID_SOURCE", "Unsupported stream protocol.", 422)
        cfg.source_ciphertext = encrypted_source(payload.source)
    if (
        payload.enabled
        and not (payload.source or cfg.source_ciphertext)
        and payload.source_kind != "simulator"
    ):
        raise AppError(
            "SOURCE_REQUIRED", "A source is required before enabling a camera.", 422
        )
    camera.name, camera.location = payload.name, payload.location
    cfg.facility, cfg.zone, cfg.enabled, cfg.source_kind = (
        payload.facility,
        payload.zone,
        payload.enabled,
        payload.source_kind,
    )
    cfg.policy_json = json.dumps(payload.policy.model_dump())
    ppe = db.scalar(
        select(CameraPpePolicy).where(CameraPpePolicy.camera_id == camera.id)
    )
    if not ppe:
        ppe = CameraPpePolicy(camera_id=camera.id, zone_label=payload.zone)
        db.add(ppe)
    ppe.required_ppe_json, ppe.is_active = (
        json.dumps(payload.policy.required_ppe),
        bool(payload.policy.required_ppe),
    )
    emit(db, "camera_configuration", {"camera_id": camera.id})
    db.commit()
    return {"data": view(camera, cfg)}


@router.post("/api/cameras", status_code=201)
def register_camera(
    payload: CameraInput, request: Request, db: Session = Depends(get_db)
):
    result = save_camera(db, payload)
    append_audit_event(
        db,
        event_type="camera_created",
        actor_type="human",
        actor_name=request.state.actor["username"],
        correlation_id=secrets.token_hex(16),
        metadata={"camera_id": result["data"]["id"]},
        simulation=False,
    )
    db.commit()
    return result


@router.put("/api/cameras/{camera_id}")
def update_camera(camera_id: str, payload: CameraInput, db: Session = Depends(get_db)):
    return save_camera(db, payload, camera_id)


@router.delete("/api/cameras/{camera_id}")
def remove_camera(camera_id: str, db: Session = Depends(get_db)):
    camera, cfg = configuration(db, camera_id)
    if db.scalar(
        select(Incident.id).where(Incident.camera_id == camera_id).limit(1)
    ) or db.scalar(
        select(VideoAsset.id).where(VideoAsset.camera_id == camera_id).limit(1)
    ):
        raise AppError(
            "CAMERA_HAS_EVIDENCE",
            "Disable cameras with incident/media history instead of deleting them.",
            409,
        )
    from app.models.detector import DetectorEventIngestion

    if db.scalar(
        select(DetectorEventIngestion.id)
        .where(DetectorEventIngestion.camera_id == camera_id)
        .limit(1)
    ):
        raise AppError(
            "CAMERA_HAS_EVIDENCE", "Camera has detector history; disable instead.", 409
        )
    db.execute(delete(CameraPpePolicy).where(CameraPpePolicy.camera_id == camera_id))
    if cfg:
        db.delete(cfg)
        db.flush()
    db.delete(camera)
    emit(db, "camera_deleted", {"camera_id": camera_id})
    db.commit()
    return {"data": {"deleted": True}}


@router.get("/api/cameras/{camera_id}/snapshot")
def snapshot(camera_id: str, db: Session = Depends(get_db)):
    configuration(db, camera_id)
    path = get_settings().frame_path / f"camera-{secrets_safe_id(camera_id)}.jpg"
    if not path.is_file() or utc_now().timestamp() - path.stat().st_mtime > 30:
        raise AppError(
            "SNAPSHOT_UNAVAILABLE",
            "No recent camera preview. Start the camera worker.",
            404,
        )
    return Response(
        path.read_bytes(),
        media_type="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )


def secrets_safe_id(value):
    import hashlib

    return hashlib.sha256(value.encode()).hexdigest()


@router.post("/api/detector/heartbeat")
def heartbeat(payload: Heartbeat, request: Request, db: Session = Depends(get_db)):
    validate_device_camera(request, payload.camera_id)
    camera, cfg = configuration(db, payload.camera_id)
    changed = camera.status != payload.status
    camera.status, camera.last_seen_at, camera.stream_status = (
        payload.status,
        utc_now(),
        payload.status,
    )
    if cfg:
        cfg.health_details = json.dumps(
            payload.model_dump(exclude={"camera_id", "status"})
        )
    if changed:
        emit(db, "camera_health", {"camera_id": camera.id, "status": payload.status})
    db.commit()
    return {"data": {"acknowledged": True}}


def validate_device_camera(request, camera_id):
    if request.state.actor.get("mode") == "device":
        allowed = {
            x.strip()
            for x in get_settings().detector_camera_ids.split(",")
            if x.strip()
        }
        if camera_id not in allowed:
            raise AppError(
                "CAMERA_NOT_AUTHORIZED",
                "Device is not authorized for this camera.",
                403,
            )


@router.post("/api/detector/snapshot/{camera_id}")
async def upload_snapshot(
    camera_id: str,
    request: Request,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    validate_device_camera(request, camera_id)
    configuration(db, camera_id)
    raw = await image.read(2_000_001)
    if len(raw) > 2_000_000:
        raise AppError("FILE_TOO_LARGE", "Preview exceeds 2 MB.", 413)
    from PIL import Image, UnidentifiedImageError

    try:
        picture = Image.open(io.BytesIO(raw))
        if picture.width * picture.height > 8_000_000:
            raise ValueError("Too many pixels")
        picture.thumbnail((960, 540))
        output = io.BytesIO()
        picture.convert("RGB").save(output, format="JPEG", quality=75)
    except (ValueError, OSError, UnidentifiedImageError) as exc:
        raise AppError(
            "INVALID_IMAGE", "Preview is not a supported image.", 422
        ) from exc
    root = get_settings().frame_path
    root.mkdir(parents=True, exist_ok=True)
    target = root / f"camera-{secrets_safe_id(camera_id)}.jpg"
    temporary = root / f"{secrets.token_hex(16)}.tmp"
    temporary.write_bytes(output.getvalue())
    temporary.replace(target)
    return {"data": {"stored": True}}


@router.get("/api/detector/config/{camera_id}")
def worker_config(camera_id: str, request: Request, db: Session = Depends(get_db)):
    validate_device_camera(request, camera_id)
    if request.state.actor["role"] not in {"device", "administrator"}:
        raise AppError("FORBIDDEN", "Device or administrator access required.", 403)
    camera, cfg = configuration(db, camera_id)
    if not cfg:
        raise AppError("NOT_CONFIGURED", "Configure this camera first.", 409)
    source = None
    if cfg.source_ciphertext:
        from cryptography.fernet import Fernet

        source = (
            Fernet(get_settings().camera_encryption_key.encode())
            .decrypt(cfg.source_ciphertext.encode())
            .decode()
        )
    return {"data": {**view(camera, cfg), "source": source}}


@router.get("/api/analytics")
def analytics(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    cutoff = utc_now() - timedelta(days=days)
    rows = db.scalars(select(Incident).where(Incident.detected_at >= cutoff)).all()
    by_day, by_type, by_severity, by_camera = {}, {}, {}, {}
    for item in rows:
        day = item.detected_at.date().isoformat()
        for group, key in [
            (by_day, day),
            (by_type, item.incident_type),
            (by_severity, item.severity),
            (by_camera, item.camera_id),
        ]:
            group[key] = group.get(key, 0) + 1
    reviews = db.scalars(
        select(AnalysisReview)
        .join(IncidentAnalysis)
        .where(IncidentAnalysis.created_at >= cutoff)
    ).all()
    latencies, confirmed, rejected = [], 0, 0
    for review in reviews:
        confirmed += review.decision == "confirmed"
        rejected += review.decision == "rejected"
        if review.reviewed_at and review.decision != "pending":
            seconds = (
                as_utc(review.reviewed_at) - as_utc(review.analysis.created_at)
            ).total_seconds()
            if seconds >= 0:
                latencies.append(seconds)
    return {
        "data": {
            "window_days": days,
            "incidents": len(rows),
            "by_day": sorted(by_day.items()),
            "by_type": by_type,
            "by_severity": by_severity,
            "by_camera": by_camera,
            "confirmed_reviews": confirmed,
            "rejected_reviews": rejected,
            "mean_review_seconds": round(sum(latencies) / len(latencies), 2)
            if latencies
            else None,
            "review_sample_size": len(latencies),
            "false_alarm_review_fraction": rejected / (confirmed + rejected)
            if confirmed + rejected
            else None,
            "ppe_compliance_accuracy": None,
            "detection_accuracy": None,
            "definitions": {
                "mean_review_seconds": "Analysis creation to latest non-pending review; includes processing, not pure operator response.",
                "false_alarm_review_fraction": "Rejected / (confirmed + rejected) reviews; not held-out detector false-positive rate.",
                "incidents": "Stored incident records including historical seeds when within the selected dates.",
            },
            "includes_demo_records": True,
        }
    }


@router.get("/api/incidents-export")
def export_incidents(request: Request, db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Incident).order_by(Incident.detected_at.desc()).limit(10000)
    ).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        ["incident_code", "type", "location", "severity", "status", "detected_at"]
    )

    def safe(value):
        value = str(value)
        return (
            "'" + value
            if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
            else value
        )

    for row in rows:
        writer.writerow(
            [
                safe(x)
                for x in [
                    row.incident_code,
                    row.incident_type,
                    row.location,
                    row.severity,
                    row.status,
                    row.detected_at.isoformat(),
                ]
            ]
        )
    append_audit_event(
        db,
        event_type="incident_export",
        actor_type="human",
        actor_name=request.state.actor["username"],
        correlation_id=secrets.token_hex(16),
        metadata={"count": len(rows)},
        simulation=False,
    )
    db.commit()
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": 'attachment; filename="safetylens-incidents.csv"'
        },
    )


@router.get("/api/incidents/{incident_id}/operations")
def get_operations(incident_id: str, db: Session = Depends(get_db)):
    if not db.get(Incident, incident_id):
        raise AppError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
    op = db.get(IncidentOperation, incident_id)
    return {
        "data": operation_view(op)
        if op
        else {
            "version": 1,
            "notes": "",
            "assigned_user_id": None,
            "acknowledged_at": None,
            "resolved_at": None,
        }
    }


def operation_view(op):
    return {
        name: getattr(op, name)
        for name in [
            "version",
            "notes",
            "assigned_user_id",
            "acknowledged_at",
            "resolved_at",
        ]
    }


@router.put("/api/incidents/{incident_id}/operations")
def update_operations(
    incident_id: str,
    payload: OperationInput,
    request: Request,
    db: Session = Depends(get_db),
):
    incident = db.get(Incident, incident_id)
    if not incident:
        raise AppError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
    if payload.assigned_user_id:
        user = db.get(User, payload.assigned_user_id)
        if not user or not user.active:
            raise AppError("INVALID_ASSIGNEE", "User is not active.", 422)
    op = db.get(IncidentOperation, incident_id)
    if not op:
        op = IncidentOperation(incident_id=incident_id, version=1)
        db.add(op)
        db.flush()
    # Compare-and-swap at SQL level prevents stale concurrent writes.
    from sqlalchemy import update

    values = {
        "notes": payload.notes,
        "assigned_user_id": payload.assigned_user_id,
        "version": payload.version + 1,
    }
    if payload.acknowledge:
        values["acknowledged_at"] = utc_now()
    if payload.resolve:
        values["resolved_at"] = utc_now()
        incident.status = "resolved"
    result = db.execute(
        update(IncidentOperation)
        .where(
            IncidentOperation.incident_id == incident_id,
            IncidentOperation.version == payload.version,
        )
        .values(**values)
    )
    if result.rowcount != 1:
        db.rollback()
        raise AppError("STALE_VERSION", "Incident changed. Reload before saving.", 409)
    append_audit_event(
        db,
        event_type="incident_operations_updated",
        actor_type="human",
        actor_name=request.state.actor["username"],
        correlation_id=secrets.token_hex(16),
        incident_id=incident_id,
        metadata=values
        | {
            "acknowledged_at": bool(payload.acknowledge),
            "resolved_at": bool(payload.resolve),
        },
        simulation=False,
    )
    db.commit()
    db.expire_all()
    return {"data": operation_view(db.get(IncidentOperation, incident_id))}


@router.get("/api/events")
async def event_stream(
    request: Request, after: int = Query(0, ge=0), db: Session = Depends(get_db)
):
    header = request.headers.get("last-event-id")
    try:
        cursor = max(after, int(header or 0))
    except ValueError as exc:
        raise AppError("INVALID_CURSOR", "Invalid event cursor.", 422) from exc
    # Do not retain a request transaction or connection during a long stream.
    db.close()

    async def stream():
        nonlocal cursor
        while not await request.is_disconnected():
            with SessionLocal() as session:
                if get_settings().auth_enabled:
                    try:
                        session_user(request, session)
                    except AppError:
                        yield "event: session_expired\ndata: {}\n\n"
                        return
                managed = session.scalars(
                    select(Camera)
                    .join(CameraConfiguration)
                    .where(Camera.status == "online")
                ).all()
                changed = False
                for camera in managed:
                    if (utc_now() - as_utc(camera.last_seen_at)).total_seconds() >= 30:
                        camera.status = "offline"
                        emit(
                            session,
                            "camera_health",
                            {"camera_id": camera.id, "status": "offline"},
                        )
                        changed = True
                if changed:
                    session.commit()
                earliest = session.scalar(select(func.min(StreamEvent.sequence)))
                if cursor and earliest and cursor < earliest - 1:
                    yield "event: resync_required\ndata: {}\n\n"
                    cursor = earliest - 1
                events = session.scalars(
                    select(StreamEvent)
                    .where(StreamEvent.sequence > cursor)
                    .order_by(StreamEvent.sequence)
                    .limit(100)
                ).all()
                batch = [(x.sequence, x.kind, x.payload_json) for x in events]
            for sequence, kind, payload in batch:
                cursor = sequence
                yield f"id: {sequence}\nevent: update\ndata: {json.dumps({'kind': kind, 'payload': json.loads(payload)})}\n\n"
            yield ": heartbeat\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/api/investigations/{incident_id}")
def investigation(incident_id: str, db: Session = Depends(get_db)):
    from app.models.notification import OperatorNotification
    from app.services.analysis import get_analysis
    from app.services.workflow import get_workflow_status

    incident = db.get(Incident, incident_id)
    if not incident:
        raise AppError("INCIDENT_NOT_FOUND", "Incident not found.", 404)
    note = db.scalar(
        select(OperatorNotification)
        .where(OperatorNotification.incident_id == incident.id)
        .order_by(OperatorNotification.created_at.desc())
    )
    analysis = get_analysis(db, note.analysis_id) if note else None
    workflow = get_workflow_status(db, note.analysis_id) if note else None
    related = db.scalars(
        select(Incident)
        .where(Incident.camera_id == incident.camera_id, Incident.id != incident.id)
        .order_by(Incident.detected_at.desc())
        .limit(5)
    ).all()
    return {
        "data": {
            "incident": {
                k: getattr(incident, k)
                for k in [
                    "id",
                    "incident_code",
                    "title",
                    "location",
                    "severity",
                    "status",
                    "detected_at",
                    "camera_id",
                ]
            },
            "analysis": analysis.model_dump(mode="json") if analysis else None,
            "workflow": workflow.model_dump(mode="json") if workflow else None,
            "related": [
                {"id": x.id, "title": x.title, "status": x.status} for x in related
            ],
        }
    }


@router.get("/api/platform/config")
def public_configuration():
    cfg = get_settings()
    return {
        "data": {
            "auth_enabled": cfg.auth_enabled,
            "cookie_secure": cfg.cookie_secure,
            "ai_provider": cfg.ai_provider,
            "vision_model": cfg.vision_model,
            "planner_provider": "deterministic-policy",
            "evidence_retention_days": cfg.evidence_retention_days,
            "external_actions": "simulated_only",
            "installation_scope": "single installation; organization isolation not implemented",
            "detectors": {
                "pose_fall": "experimental; external 12-clip results in docs/evaluation",
                "ppe_onnx": "experimental; weights/license review required",
                "fire_smoke": "planned",
            },
        }
    }


class RetentionRequest(BaseModel):
    confirmed: bool = False
    apply: bool = False


@router.post("/api/retention")
def evidence_retention(
    payload: RetentionRequest, request: Request, db: Session = Depends(get_db)
):
    if payload.apply and not payload.confirmed:
        raise AppError(
            "CONFIRMATION_REQUIRED", "Confirm evidence expiration explicitly.", 422
        )
    from app.services.retention import expire_evidence

    result = expire_evidence(db, apply=payload.apply)
    if payload.apply:
        append_audit_event(
            db,
            event_type="evidence_expired",
            actor_type="human",
            actor_name=request.state.actor["username"],
            correlation_id=secrets.token_hex(16),
            metadata=result,
            simulation=False,
        )
        db.commit()
    return {"data": result}

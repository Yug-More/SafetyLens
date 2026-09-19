"""Ingest Sean's detector events into the existing Stage 3–6 application pipeline."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.enums import DetectorIngestionStatus, JobStatus, JobType, VideoStatus
from app.core.errors import AppError
from app.database.base import utc_now
from app.database.session import SessionLocal
from app.models.camera import Camera
from app.models.detector import DetectorEventIngestion
from app.models.incident import Incident
from app.models.incident_analysis import IncidentAnalysis
from app.models.processing_job import ProcessingJob
from app.models.video import VideoAsset
from app.schemas.detector import (
    DetectorEventIngestRequest,
    DetectorEventPayload,
    DetectorEventRead,
)
from app.services import storage
from app.services.analysis import start_analysis
from app.services.video_processing import extract_metadata
from app.services.videos import (
    generate_asset_code,
    generate_job_code,
    process_video_job,
)

logger = logging.getLogger(__name__)


def _dumps(value: object) -> str:
    return json.dumps(value, default=str)


def _loads_list(raw: str | None) -> list:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _loads_dict(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def resolve_clip_event_offset(event: DetectorEventPayload) -> float | None:
    if event.clip_event_offset_seconds is not None:
        return float(event.clip_event_offset_seconds)
    if event.source_timestamp_seconds is not None:
        return float(event.source_timestamp_seconds)
    if event.occurred_at_seconds is not None:
        return float(event.occurred_at_seconds)
    return None


def resolve_occurred_at(event: DetectorEventPayload) -> datetime | None:
    # Detector seconds are relative to the recording/session, NOT Unix time.
    # Preserve an unknown wall-clock date rather than inventing a 1970 incident.
    return event.occurred_at


def _to_read(row: DetectorEventIngestion) -> DetectorEventRead:
    asset_code = row.video_asset.asset_code if row.video_asset is not None else None
    job_code = row.processing_job.job_code if row.processing_job is not None else None
    analysis_code = row.analysis.analysis_code if row.analysis is not None else None
    incident_code = row.incident.incident_code if row.incident is not None else None
    camera_name = row.camera.name if row.camera is not None else None
    status = DetectorIngestionStatus(row.status)
    message = {
        DetectorIngestionStatus.RECEIVED: "Detector event received.",
        DetectorIngestionStatus.UPLOADING: "Uploading detector evidence clip.",
        DetectorIngestionStatus.PROCESSING: "Preparing frames for the detector clip.",
        DetectorIngestionStatus.READY: "Clip ready for AI analysis.",
        DetectorIngestionStatus.ANALYZING: "AI analysis requested for detector clip.",
        DetectorIngestionStatus.COMPLETED: "Detector handoff completed.",
        DetectorIngestionStatus.FAILED: row.error_message or "Detector handoff failed.",
        DetectorIngestionStatus.DETECTOR_UNAVAILABLE: (
            "Detector unavailable — use uploaded-video demo path."
        ),
    }.get(status, "Detector event status updated.")
    return DetectorEventRead(
        id=row.id,
        event_id=row.event_id,
        schema_version=row.schema_version,
        event_type=row.event_type,
        source_id=row.source_id,
        camera_id=row.camera_id,
        camera_name=camera_name,
        track_id=row.track_id,
        occurred_at=row.occurred_at,
        source_timestamp_seconds=row.source_timestamp_seconds,
        clip_event_offset_seconds=row.clip_event_offset_seconds,
        detector_state=row.detector_state,
        trigger_signals=_loads_list(row.trigger_signals_json),
        pose_quality=row.pose_quality,
        heuristic_score=row.heuristic_score,
        metrics=_loads_dict(row.metrics_json),
        limitations=_loads_list(row.limitations_json),
        status=status,
        location=row.location,
        asset_code=asset_code,
        job_code=job_code,
        analysis_code=analysis_code,
        incident_code=incident_code,
        error_code=row.error_code,
        error_message=row.error_message,
        retry_count=row.retry_count,
        correlation_id=row.correlation_id,
        is_simulated=row.is_simulated,
        message=message,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def get_ingestion(db: Session, event_id: str) -> DetectorEventIngestion:
    row = db.scalars(
        select(DetectorEventIngestion)
        .options(
            selectinload(DetectorEventIngestion.video_asset),
            selectinload(DetectorEventIngestion.processing_job),
            selectinload(DetectorEventIngestion.analysis),
            selectinload(DetectorEventIngestion.incident),
            selectinload(DetectorEventIngestion.camera),
        )
        .where(DetectorEventIngestion.event_id == event_id)
    ).first()
    if row is None:
        raise AppError("DETECTOR_EVENT_NOT_FOUND", "Detector event was not found.", status_code=404)
    return row


def get_focus_offset_for_video(db: Session, video_asset_id: str) -> float | None:
    row = db.scalars(
        select(DetectorEventIngestion).where(
            DetectorEventIngestion.video_asset_id == video_asset_id
        )
    ).first()
    if row is None:
        return None
    return row.clip_event_offset_seconds


def _resolve_allowed_clip_path(
    relative_path: str,
    settings: Settings,
) -> Path:
    root = settings.detector_events_path
    root.mkdir(parents=True, exist_ok=True)
    cleaned = relative_path.strip().replace("\\", "/")
    if not cleaned or cleaned.startswith("/") or ".." in Path(cleaned).parts:
        raise AppError(
            "INVALID_CLIP_PATH",
            "Detector clip path is invalid or escapes the allowed directory.",
            status_code=422,
        )
    candidate = (root / cleaned).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise AppError(
            "INVALID_CLIP_PATH",
            "Detector clip path is outside the allowed directory.",
            status_code=422,
        ) from exc
    if not candidate.is_file():
        raise AppError(
            "CLIP_NOT_FOUND",
            "Detector evidence clip was not found under the allowed directory.",
            status_code=404,
        )
    return candidate


async def _store_uploaded_clip(
    upload: UploadFile,
    settings: Settings,
) -> tuple[str, str, int]:
    original_filename = storage.sanitize_original_filename(upload.filename)
    extension = storage.validate_extension(original_filename)
    mime_type = storage.validate_mime_type(upload.content_type or "video/mp4")
    stored_filename = storage.generate_stored_filename(extension)
    destination = storage.resolve_upload_path(stored_filename, settings)
    total = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.max_video_size_bytes:
                    raise AppError(
                        "FILE_TOO_LARGE",
                        "Detector clip exceeds the maximum upload size.",
                        status_code=413,
                    )
                handle.write(chunk)
    except Exception:
        storage.delete_file_quietly(destination)
        raise
    if total <= 0:
        storage.delete_file_quietly(destination)
        raise AppError("EMPTY_UPLOAD", "Detector clip is empty.", status_code=422)
    try:
        extract_metadata(str(destination), settings)
    except AppError:
        storage.delete_file_quietly(destination)
        raise
    return stored_filename, mime_type, total


def _store_local_clip(source: Path, settings: Settings) -> tuple[str, str, int, str]:
    original_filename = storage.sanitize_original_filename(source.name)
    extension = storage.validate_extension(original_filename)
    mime_type = "video/mp4" if extension == ".mp4" else storage.validate_mime_type("video/mp4")
    if extension == ".mov":
        mime_type = "video/quicktime"
    elif extension == ".webm":
        mime_type = "video/webm"
    stored_filename = storage.generate_stored_filename(extension)
    destination = storage.resolve_upload_path(stored_filename, settings)
    try:
        shutil.copyfile(source, destination)
        file_size = destination.stat().st_size
        extract_metadata(str(destination), settings)
    except AppError:
        storage.delete_file_quietly(destination)
        raise
    except Exception as exc:
        storage.delete_file_quietly(destination)
        raise AppError(
            "UNREADABLE_VIDEO",
            "Detector clip could not be validated as a video.",
            status_code=422,
        ) from exc
    return stored_filename, mime_type, file_size, original_filename


def _link_incident(db: Session, identifier: str | None) -> Incident | None:
    if not identifier:
        return None
    incident = db.scalars(
        select(Incident).where(
            (Incident.id == identifier) | (Incident.incident_code == identifier)
        )
    ).first()
    return incident


def _create_video_from_stored(
    db: Session,
    *,
    stored_filename: str,
    original_filename: str,
    mime_type: str,
    file_size: int,
    location: str,
    camera_id: str | None,
) -> tuple[VideoAsset, ProcessingJob]:
    video = VideoAsset(
        id=str(uuid4()),
        asset_code=generate_asset_code(db),
        original_filename=original_filename,
        stored_filename=stored_filename,
        mime_type=mime_type,
        file_size_bytes=file_size,
        camera_id=camera_id,
        location=location,
        status=VideoStatus.UPLOADED.value,
    )
    db.add(video)
    db.flush()
    job = ProcessingJob(
        id=str(uuid4()),
        job_code=generate_job_code(db),
        video_asset_id=video.id,
        job_type=JobType.VIDEO_PREPARE.value,
        status=JobStatus.QUEUED.value,
        progress=5,
        current_step="Detector clip received",
    )
    db.add(job)
    db.flush()
    return video, job


def _refresh_status_from_pipeline(db: Session, row: DetectorEventIngestion) -> None:
    if row.video_asset_id:
        video = db.get(VideoAsset, row.video_asset_id)
        if video is not None and video.status == VideoStatus.FAILED.value:
            row.status = DetectorIngestionStatus.FAILED.value
            row.error_code = "VIDEO_PROCESSING_FAILED"
            row.error_message = "Detector clip processing failed."
            return
        if video is not None and video.status == VideoStatus.READY.value:
            if row.status in {
                DetectorIngestionStatus.UPLOADING.value,
                DetectorIngestionStatus.PROCESSING.value,
                DetectorIngestionStatus.RECEIVED.value,
            }:
                row.status = DetectorIngestionStatus.READY.value
    if row.analysis_id:
        analysis = db.get(IncidentAnalysis, row.analysis_id)
        if analysis is None:
            return
        if analysis.status in {"completed", "needs_review"}:
            row.status = DetectorIngestionStatus.COMPLETED.value
            row.error_code = None
            row.error_message = None
        elif analysis.status == "failed":
            row.status = DetectorIngestionStatus.FAILED.value
            row.error_code = analysis.error_code or "ANALYSIS_FAILED"
            row.error_message = analysis.error_message or "Analysis failed."
        elif analysis.status in {"queued", "running"}:
            row.status = DetectorIngestionStatus.ANALYZING.value


def advance_ingestion(
    db: Session,
    event_id: str,
    *,
    background_tasks: BackgroundTasks | None = None,
    auto_analyze: bool = True,
    settings: Settings | None = None,
) -> DetectorEventRead:
    cfg = settings or get_settings()
    row = get_ingestion(db, event_id)
    _refresh_status_from_pipeline(db, row)

    if row.status == DetectorIngestionStatus.COMPLETED.value:
        db.commit()
        return _to_read(get_ingestion(db, event_id))

    if row.video_asset_id and row.status == DetectorIngestionStatus.READY.value and auto_analyze:
        video = db.get(VideoAsset, row.video_asset_id)
        if video is not None and video.status == VideoStatus.READY.value:
            existing = db.scalars(
                select(IncidentAnalysis)
                .where(IncidentAnalysis.video_asset_id == video.id)
                .order_by(IncidentAnalysis.created_at.desc())
            ).first()
            if existing is not None and existing.status in {"completed", "needs_review"}:
                row.analysis_id = existing.id
                row.status = DetectorIngestionStatus.COMPLETED.value
                db.commit()
                return _to_read(get_ingestion(db, event_id))
            if existing is not None and existing.status in {"queued", "running"}:
                row.analysis_id = existing.id
                row.status = DetectorIngestionStatus.ANALYZING.value
                db.commit()
                return _to_read(get_ingestion(db, event_id))
            try:
                started = start_analysis(db, video.asset_code, settings=cfg)
                analysis = db.scalars(
                    select(IncidentAnalysis).where(
                        IncidentAnalysis.analysis_code == started.analysis_code
                    )
                ).first()
                if analysis is not None:
                    row.analysis_id = analysis.id
                    row.status = DetectorIngestionStatus.ANALYZING.value
                    db.commit()
                    if background_tasks is not None:
                        from app.services.analysis import run_analysis_job

                        background_tasks.add_task(
                            run_analysis_job,
                            analysis.id,
                            analysis.processing_job_id,
                        )
                    else:
                        from app.services.analysis import run_analysis_job

                        run_analysis_job(analysis.id, analysis.processing_job_id)
                        _refresh_status_from_pipeline(db, row)
                        db.commit()
            except AppError as exc:
                if exc.code == "ANALYSIS_IN_PROGRESS":
                    row.status = DetectorIngestionStatus.ANALYZING.value
                    db.commit()
                else:
                    row.status = DetectorIngestionStatus.FAILED.value
                    row.error_code = exc.code
                    row.error_message = exc.message
                    db.commit()

    db.commit()
    return _to_read(get_ingestion(db, event_id))


async def ingest_detector_event(
    db: Session,
    payload: DetectorEventIngestRequest,
    *,
    clip: UploadFile | None = None,
    background_tasks: BackgroundTasks | None = None,
    settings: Settings | None = None,
) -> DetectorEventRead:
    cfg = settings or get_settings()
    storage.ensure_storage_directories(cfg)
    cfg.detector_events_path.mkdir(parents=True, exist_ok=True)
    event = payload.event

    existing = db.scalars(
        select(DetectorEventIngestion).where(DetectorEventIngestion.event_id == event.event_id)
    ).first()
    if existing is not None:
        # Deduplicate: reuse mapping; never re-upload clip.
        return advance_ingestion(
            db,
            existing.event_id,
            background_tasks=background_tasks,
            auto_analyze=payload.auto_analyze
            if payload.auto_analyze is not None
            else cfg.detector_ingest_auto_analyze,
            settings=cfg,
        )

    camera_id = event.camera_id
    if camera_id:
        camera = db.get(Camera, camera_id)
        if camera is None:
            raise AppError(
                "INVALID_CAMERA_ID",
                "camera_id must be a real Camera primary key (for example cam-04), "
                "not a detector source_id label.",
                status_code=422,
            )
    else:
        # Prefer demo Loading Zone B camera when source matches contract demo label.
        preferred = db.get(Camera, "cam-04")
        camera_id = preferred.id if preferred is not None else None

    incident = _link_incident(db, payload.incident_identifier)
    correlation_id = str(uuid4())
    evidence = event.evidence.model_dump() if event.evidence else {}
    metrics = event.metrics if isinstance(event.metrics, dict) else {}
    # Flatten Sean PoseMetrics-shaped nested dict if present.
    if "pose_quality" in metrics and "torso_angle_degrees_from_vertical" not in metrics:
        nested = metrics
        metrics = {
            k: v
            for k, v in nested.items()
            if k
            not in {
                "timestamp_seconds",
                "pose_quality",
            }
        }

    row = DetectorEventIngestion(
        id=str(uuid4()),
        event_id=event.event_id,
        schema_version=event.schema_version,
        event_type=event.event_type,
        source_id=event.source_id,
        camera_id=camera_id,
        track_id=event.track_id,
        occurred_at=resolve_occurred_at(event),
        source_timestamp_seconds=event.source_timestamp_seconds,
        clip_event_offset_seconds=resolve_clip_event_offset(event),
        detector_state=event.state,
        trigger_signals_json=_dumps(event.trigger_signals),
        pose_quality=event.pose_quality,
        heuristic_score=event.heuristic_score,
        metrics_json=_dumps(metrics),
        limitations_json=_dumps(event.limitations),
        evidence_json=_dumps(evidence),
        status=DetectorIngestionStatus.RECEIVED.value,
        location=payload.location,
        incident_id=incident.id if incident else None,
        correlation_id=correlation_id,
        is_simulated=True,
    )
    db.add(row)
    db.flush()

    try:
        row.status = DetectorIngestionStatus.UPLOADING.value
        if clip is not None and clip.filename:
            stored_filename, mime_type, file_size = await _store_uploaded_clip(clip, cfg)
            original_filename = storage.sanitize_original_filename(clip.filename)
        elif event.evidence and event.evidence.clip_relative_path:
            source = _resolve_allowed_clip_path(event.evidence.clip_relative_path, cfg)
            stored_filename, mime_type, file_size, original_filename = _store_local_clip(
                source, cfg
            )
        else:
            raise AppError(
                "CLIP_REQUIRED",
                "Provide a detector evidence clip upload or an allowed clip_relative_path.",
                status_code=422,
            )

        video, job = _create_video_from_stored(
            db,
            stored_filename=stored_filename,
            original_filename=original_filename,
            mime_type=mime_type,
            file_size=file_size,
            location=payload.location,
            camera_id=camera_id,
        )
        row.video_asset_id = video.id
        row.processing_job_id = job.id
        row.status = DetectorIngestionStatus.PROCESSING.value
        db.commit()

        if background_tasks is not None:
            background_tasks.add_task(process_video_job, video.id, job.id)
            background_tasks.add_task(
                _post_process_ingestion,
                event.event_id,
                payload.auto_analyze
                if payload.auto_analyze is not None
                else cfg.detector_ingest_auto_analyze,
            )
        else:
            process_video_job(video.id, job.id)
            return advance_ingestion(
                db,
                event.event_id,
                background_tasks=None,
                auto_analyze=payload.auto_analyze
                if payload.auto_analyze is not None
                else cfg.detector_ingest_auto_analyze,
                settings=cfg,
            )
    except AppError as exc:
        row.status = DetectorIngestionStatus.FAILED.value
        row.error_code = exc.code
        row.error_message = exc.message
        db.commit()
        raise

    return _to_read(get_ingestion(db, event.event_id))


def _post_process_ingestion(event_id: str, auto_analyze: bool) -> None:
    db = SessionLocal()
    try:
        # Wait briefly for prepare job by polling status updates from process_video_job.
        import time

        for _ in range(40):
            row = db.scalars(
                select(DetectorEventIngestion).where(DetectorEventIngestion.event_id == event_id)
            ).first()
            if row is None:
                return
            if row.video_asset_id:
                video = db.get(VideoAsset, row.video_asset_id)
                if video is not None and video.status in {
                    VideoStatus.READY.value,
                    VideoStatus.FAILED.value,
                }:
                    break
            time.sleep(0.05)
        advance_ingestion(db, event_id, auto_analyze=auto_analyze)
    except Exception:  # pragma: no cover - background safety
        logger.exception("Detector post-process failed for %s", event_id)
    finally:
        db.close()


def list_detector_events(db: Session, *, limit: int = 20) -> list[DetectorEventRead]:
    rows = db.scalars(
        select(DetectorEventIngestion)
        .options(
            selectinload(DetectorEventIngestion.video_asset),
            selectinload(DetectorEventIngestion.processing_job),
            selectinload(DetectorEventIngestion.analysis),
            selectinload(DetectorEventIngestion.incident),
            selectinload(DetectorEventIngestion.camera),
        )
        .order_by(DetectorEventIngestion.created_at.desc())
        .limit(limit)
    ).all()
    for row in rows:
        _refresh_status_from_pipeline(db, row)
    db.commit()
    return [_to_read(row) for row in rows]


def retry_detector_event(
    db: Session,
    event_id: str,
    *,
    background_tasks: BackgroundTasks | None = None,
    settings: Settings | None = None,
) -> DetectorEventRead:
    cfg = settings or get_settings()
    row = get_ingestion(db, event_id)
    row.retry_count += 1
    row.updated_at = utc_now()

    if row.status == DetectorIngestionStatus.COMPLETED.value:
        db.commit()
        return _to_read(row)

    if row.video_asset_id is None:
        raise AppError(
            "RETRY_NOT_AVAILABLE",
            "No stored clip mapping exists for this event. Re-submit with a clip.",
            status_code=409,
        )

    video = db.get(VideoAsset, row.video_asset_id)
    if video is None:
        raise AppError("VIDEO_MISSING", "Mapped video asset is missing.", status_code=409)

    if video.status == VideoStatus.FAILED.value:
        job = ProcessingJob(
            id=str(uuid4()),
            job_code=generate_job_code(db),
            video_asset_id=video.id,
            job_type=JobType.VIDEO_PREPARE.value,
            status=JobStatus.QUEUED.value,
            progress=0,
            current_step="Retrying detector clip prepare",
        )
        db.add(job)
        db.flush()
        row.processing_job_id = job.id
        row.status = DetectorIngestionStatus.PROCESSING.value
        row.error_code = None
        row.error_message = None
        video.status = VideoStatus.UPLOADED.value
        db.commit()
        if background_tasks is not None:
            background_tasks.add_task(process_video_job, video.id, job.id)
            background_tasks.add_task(_post_process_ingestion, event_id, True)
        else:
            process_video_job(video.id, job.id)
            return advance_ingestion(db, event_id, auto_analyze=True, settings=cfg)
        return _to_read(get_ingestion(db, event_id))

    row.error_code = None
    row.error_message = None
    db.commit()
    return advance_ingestion(
        db,
        event_id,
        background_tasks=background_tasks,
        auto_analyze=True,
        settings=cfg,
    )

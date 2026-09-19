from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.enums import JobStatus, JobType, VideoStatus
from app.core.errors import AppError
from app.database.base import utc_now
from app.database.session import SessionLocal
from app.models.camera import Camera
from app.models.processing_job import ProcessingJob
from app.models.video import VideoAsset
from app.models.video_frame import VideoFrame
from app.schemas.common import Meta
from app.schemas.video import (
    ProcessingJobRead,
    VideoAssetRead,
    VideoFrameRead,
    VideoUploadResponse,
)
from app.services import storage
from app.services.video_processing import (
    extract_metadata,
    extract_representative_frames,
)

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024


def _year_prefix() -> str:
    return str(datetime.now(timezone.utc).year)


def _next_code(db: Session, model, field_name: str, prefix: str) -> str:
    column = getattr(model, field_name)
    count = db.scalar(select(func.count()).select_from(model).where(column.like(f"{prefix}-%"))) or 0
    return f"{prefix}-{count + 1:04d}"


def generate_asset_code(db: Session) -> str:
    return _next_code(db, VideoAsset, "asset_code", f"VID-{_year_prefix()}")


def generate_job_code(db: Session) -> str:
    return _next_code(db, ProcessingJob, "job_code", f"JOB-{_year_prefix()}")


def generate_frame_code(db: Session, asset_code: str, index: int) -> str:
    return f"{asset_code}-F{index:03d}"


def _video_to_read(video: VideoAsset, latest_job: ProcessingJob | None = None) -> VideoAssetRead:
    camera_name = video.camera.name if video.camera is not None else None
    job = latest_job
    if job is None and video.jobs:
        job = sorted(video.jobs, key=lambda item: item.created_at, reverse=True)[0]
    return VideoAssetRead(
        id=video.id,
        asset_code=video.asset_code,
        original_filename=video.original_filename,
        mime_type=video.mime_type,
        file_size_bytes=video.file_size_bytes,
        duration_seconds=video.duration_seconds,
        width=video.width,
        height=video.height,
        fps=video.fps,
        frame_count=video.frame_count,
        camera_id=video.camera_id,
        camera_name=camera_name,
        location=video.location,
        status=VideoStatus(video.status),
        demo_scenario=video.demo_scenario,
        demo_ppe_observation=video.demo_ppe_observation,
        created_at=video.created_at,
        updated_at=video.updated_at,
        content_url=f"/api/videos/{video.asset_code}/content",
        latest_job_code=job.job_code if job else None,
        latest_job_status=JobStatus(job.status) if job else None,
    )


def _job_to_read(job: ProcessingJob) -> ProcessingJobRead:
    return ProcessingJobRead(
        id=job.id,
        job_code=job.job_code,
        video_asset_id=job.video_asset_id,
        video_asset_code=job.video_asset.asset_code if job.video_asset else None,
        job_type=JobType(job.job_type),
        status=JobStatus(job.status),
        progress=job.progress,
        current_step=job.current_step,
        error_code=job.error_code,
        error_message=job.error_message,
        started_at=job.started_at,
        completed_at=job.completed_at,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


def _frame_to_read(frame: VideoFrame) -> VideoFrameRead:
    return VideoFrameRead(
        id=frame.id,
        frame_code=frame.frame_code,
        video_asset_id=frame.video_asset_id,
        frame_number=frame.frame_number,
        timestamp_seconds=frame.timestamp_seconds,
        width=frame.width,
        height=frame.height,
        created_at=frame.created_at,
        content_url=f"/api/frames/{frame.frame_code}/content",
    )


async def stream_upload_to_disk(
    upload: UploadFile,
    destination: Path,
    max_bytes: int,
) -> int:
    total = 0
    try:
        with destination.open("wb") as handle:
            while True:
                chunk = await upload.read(CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise AppError(
                        "FILE_TOO_LARGE",
                        f"Uploaded file exceeds the maximum size of {max_bytes // (1024 * 1024)} MB.",
                        status_code=413,
                    )
                handle.write(chunk)
    except Exception:
        storage.delete_file_quietly(destination)
        raise

    if total <= 0:
        storage.delete_file_quietly(destination)
        raise AppError("EMPTY_UPLOAD", "Uploaded file is empty.", status_code=422)
    return total


async def create_upload(
    db: Session,
    *,
    upload: UploadFile,
    location: str,
    camera_id: str | None,
    demo_scenario: str | None = None,
    demo_ppe_observation: str | None = None,
    settings: Settings | None = None,
) -> tuple[VideoUploadResponse, str]:
    cfg = settings or get_settings()
    storage.ensure_storage_directories(cfg)

    cleaned_location = location.strip()
    if not cleaned_location:
        raise AppError("VALIDATION_ERROR", "Location cannot be blank.", status_code=422)

    if camera_id:
        camera = db.get(Camera, camera_id)
        if camera is None:
            raise AppError("NOT_FOUND", "Camera not found.", status_code=404)

    original_filename = storage.sanitize_original_filename(upload.filename)
    extension = storage.validate_extension(original_filename)
    mime_type = storage.validate_mime_type(upload.content_type)
    stored_filename = storage.generate_stored_filename(extension)
    destination = storage.resolve_upload_path(stored_filename, cfg)

    file_size = await stream_upload_to_disk(upload, destination, cfg.max_video_size_bytes)

    # Decode check before creating durable ready-state records.
    try:
        extract_metadata(str(destination), cfg)
    except AppError:
        storage.delete_file_quietly(destination)
        raise
    except Exception as exc:  # pragma: no cover - defensive
        storage.delete_file_quietly(destination)
        raise AppError(
            "UNREADABLE_VIDEO",
            "The uploaded file could not be validated as a video.",
            status_code=422,
        ) from exc

    asset_code = generate_asset_code(db)
    job_code = generate_job_code(db)
    video = VideoAsset(
        id=str(uuid4()),
        asset_code=asset_code,
        original_filename=original_filename,
        stored_filename=stored_filename,
        mime_type=mime_type,
        file_size_bytes=file_size,
        camera_id=camera_id,
        location=cleaned_location,
        status=VideoStatus.UPLOADED.value,
        demo_scenario=(demo_scenario or None),
        demo_ppe_observation=(demo_ppe_observation or None),
    )
    job = ProcessingJob(
        id=str(uuid4()),
        job_code=job_code,
        video_asset_id=video.id,
        job_type=JobType.VIDEO_PREPARE.value,
        status=JobStatus.QUEUED.value,
        progress=5,
        current_step="Upload received",
    )
    # Need video id before flush for FK; set relationship via explicit ids.
    db.add(video)
    db.flush()
    job.video_asset_id = video.id
    db.add(job)
    db.commit()
    db.refresh(video)
    db.refresh(job)

    response = VideoUploadResponse(
        asset_code=video.asset_code,
        job_code=job.job_code,
        status=VideoStatus(video.status),
        original_filename=video.original_filename,
        location=video.location,
        created_at=video.created_at,
    )
    return response, video.id


def process_video_job(video_id: str, job_id: str) -> None:
    """Background worker: metadata + frame sampling with progress updates."""
    cfg = get_settings()
    db = SessionLocal()
    try:
        video = db.get(VideoAsset, video_id)
        job = db.get(ProcessingJob, job_id)
        if video is None or job is None:
            return

        def update_job(progress: int, step: str, status: JobStatus = JobStatus.PROCESSING) -> None:
            job.status = status.value
            job.progress = progress
            job.current_step = step
            job.updated_at = utc_now()
            if status == JobStatus.PROCESSING and job.started_at is None:
                job.started_at = utc_now()
            db.commit()

        try:
            update_job(10, "Validating video")
            video.status = VideoStatus.PROCESSING.value
            db.commit()

            video_path = storage.resolve_upload_path(video.stored_filename, cfg)
            if not video_path.exists():
                raise AppError("MISSING_FILE", "Stored video file is missing.", status_code=500)

            update_job(25, "Reading metadata")
            metadata = extract_metadata(str(video_path), cfg)
            video.duration_seconds = metadata.duration_seconds
            video.width = metadata.width
            video.height = metadata.height
            video.fps = metadata.fps
            video.frame_count = metadata.frame_count
            db.commit()

            update_job(55, "Sampling frames")
            focus_offset = None
            try:
                from app.services.detector_ingestion import get_focus_offset_for_video

                focus_offset = get_focus_offset_for_video(db, video.id)
            except Exception:  # pragma: no cover - optional detector mapping
                focus_offset = None
            frames = extract_representative_frames(
                str(video_path),
                fps=metadata.fps,
                frame_count=metadata.frame_count,
                settings=cfg,
                focus_offset_seconds=focus_offset,
            )

            update_job(80, "Preparing evidence")
            for existing in list(video.frames):
                storage.delete_file_quietly(storage.resolve_frame_path(existing.stored_filename, cfg))
                db.delete(existing)
            db.flush()

            for index, item in enumerate(frames, start=1):
                db.add(
                    VideoFrame(
                        id=str(uuid4()),
                        video_asset_id=video.id,
                        frame_code=generate_frame_code(db, video.asset_code, index),
                        frame_number=item.frame_number,
                        timestamp_seconds=item.timestamp_seconds,
                        stored_filename=item.stored_filename,
                        width=item.width,
                        height=item.height,
                    )
                )
            db.commit()

            video.status = VideoStatus.READY.value
            job.status = JobStatus.COMPLETED.value
            job.progress = 100
            job.current_step = "Ready for AI analysis"
            job.completed_at = utc_now()
            job.error_code = None
            job.error_message = None
            db.commit()

            # Automatically continue the demo pipeline: analysis → notification → SOP → plan.
            try:
                from app.services import analysis as analysis_service

                analyze_response, should_run = analysis_service.ensure_analysis_for_video(
                    db, video.asset_code
                )
                job.current_step = "Analysis queued"
                db.commit()
                if should_run:
                    analysis_row = analysis_service.get_analysis(
                        db, analyze_response.analysis_code
                    )
                    if analysis_row.processing_job_id:
                        analysis_service.run_analysis_job(
                            analysis_row.id, analysis_row.processing_job_id
                        )
                    analysis_row = analysis_service.get_analysis(
                        db, analyze_response.analysis_code
                    )
                    if analysis_row.status.value in {
                        "completed",
                        "needs_review",
                    }:
                        job.current_step = "Analysis complete — awaiting human review"
                    else:
                        job.current_step = "Analysis queued"
                    db.commit()
                else:
                    job.current_step = "Analysis ready — awaiting human review"
                    db.commit()
            except Exception:
                logger.exception(
                    "Automatic analysis failed for video %s; operator can retry.",
                    video.asset_code,
                )
                job.current_step = "Ready for AI analysis"
                db.commit()
        except AppError as exc:
            video.status = VideoStatus.FAILED.value
            job.status = JobStatus.FAILED.value
            job.progress = min(job.progress, 99)
            job.current_step = "Processing failed"
            job.error_code = exc.code
            job.error_message = exc.message
            job.completed_at = utc_now()
            db.commit()
        except Exception:
            video.status = VideoStatus.FAILED.value
            job.status = JobStatus.FAILED.value
            job.progress = min(job.progress, 99)
            job.current_step = "Processing failed"
            job.error_code = "PROCESSING_ERROR"
            job.error_message = "Video processing failed unexpectedly."
            job.completed_at = utc_now()
            db.commit()
    finally:
        db.close()


def list_videos(
    db: Session,
    *,
    status: VideoStatus | None = None,
    camera_id: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[VideoAssetRead], Meta]:
    query = select(VideoAsset).options(
        selectinload(VideoAsset.camera),
        selectinload(VideoAsset.jobs),
    )
    if status is not None:
        query = query.where(VideoAsset.status == status.value)
    if camera_id:
        query = query.where(VideoAsset.camera_id == camera_id)
    if search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                VideoAsset.original_filename.ilike(pattern),
                VideoAsset.asset_code.ilike(pattern),
                VideoAsset.location.ilike(pattern),
            )
        )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(
        query.order_by(VideoAsset.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return [_video_to_read(row) for row in rows], Meta(count=total, limit=limit, offset=offset)


def get_video(db: Session, identifier: str) -> VideoAssetRead:
    video = _get_video_entity(db, identifier)
    return _video_to_read(video)


def get_video_entity(db: Session, identifier: str) -> VideoAsset:
    return _get_video_entity(db, identifier)


def _get_video_entity(db: Session, identifier: str) -> VideoAsset:
    video = db.scalars(
        select(VideoAsset)
        .options(selectinload(VideoAsset.camera), selectinload(VideoAsset.jobs))
        .where(or_(VideoAsset.id == identifier, VideoAsset.asset_code == identifier))
    ).first()
    if video is None:
        raise AppError("NOT_FOUND", "Video not found.", status_code=404)
    return video


def list_video_frames(db: Session, identifier: str) -> list[VideoFrameRead]:
    video = _get_video_entity(db, identifier)
    frames = db.scalars(
        select(VideoFrame)
        .where(VideoFrame.video_asset_id == video.id)
        .order_by(VideoFrame.timestamp_seconds.asc(), VideoFrame.frame_number.asc())
    ).all()
    return [_frame_to_read(frame) for frame in frames]


def get_job(db: Session, identifier: str) -> ProcessingJobRead:
    job = db.scalars(
        select(ProcessingJob)
        .options(selectinload(ProcessingJob.video_asset))
        .where(or_(ProcessingJob.id == identifier, ProcessingJob.job_code == identifier))
    ).first()
    if job is None:
        raise AppError("NOT_FOUND", "Processing job not found.", status_code=404)
    return _job_to_read(job)


def get_frame_entity(db: Session, identifier: str) -> VideoFrame:
    frame = db.scalars(
        select(VideoFrame).where(
            or_(VideoFrame.id == identifier, VideoFrame.frame_code == identifier)
        )
    ).first()
    if frame is None:
        raise AppError("NOT_FOUND", "Frame not found.", status_code=404)
    return frame

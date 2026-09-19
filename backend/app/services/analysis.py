from __future__ import annotations

import json
import logging
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.ai.base import AIProviderError
from app.ai.factory import get_ai_provider
from app.ai.schemas import FrameAnalysisInput
from app.core.config import Settings, get_settings
from app.core.enums import (
    AnalysisSeverity,
    AnalysisStatus,
    IncidentStatus,
    JobStatus,
    JobType,
    ReviewDecision,
    ReviewStatus,
    VideoStatus,
)
from app.core.errors import AppError
from app.database.base import utc_now
from app.database.session import SessionLocal
from app.models.analysis_evidence import AnalysisEvidence
from app.models.analysis_review import AnalysisReview
from app.models.incident import Incident
from app.models.incident_analysis import IncidentAnalysis
from app.models.notification import OperatorNotification
from app.models.processing_job import ProcessingJob
from app.models.video import VideoAsset
from app.models.video_frame import VideoFrame
from app.schemas.analysis import (
    AIProviderInfo,
    AnalysisEvidenceRead,
    AnalysisReviewCreate,
    AnalysisReviewRead,
    AnalyzeVideoResponse,
    IncidentAnalysisRead,
)
from app.schemas.common import Meta
from app.services import storage

logger = logging.getLogger(__name__)



def _year_prefix() -> str:
    return str(utc_now().year)


def _next_code(db: Session, model, field_name: str, prefix: str) -> str:
    column = getattr(model, field_name)
    count = db.scalar(select(func.count()).select_from(model).where(column.like(f"{prefix}-%"))) or 0
    return f"{prefix}-{count + 1:04d}"


def generate_analysis_code(db: Session) -> str:
    return _next_code(db, IncidentAnalysis, "analysis_code", f"ANL-{_year_prefix()}")


def generate_job_code(db: Session) -> str:
    return _next_code(db, ProcessingJob, "job_code", f"JOB-{_year_prefix()}")


def provider_label(provider_name: str, *, is_demo: bool, is_simulated: bool) -> str:
    if provider_name == "demo" or is_demo:
        return "Demo AI (simulated)"
    if is_simulated:
        return f"{provider_name} (simulated)"
    return f"{provider_name} (real provider)"


def get_provider_info(settings: Settings | None = None) -> AIProviderInfo:
    cfg = settings or get_settings()
    provider = get_ai_provider(cfg)
    return AIProviderInfo(
        provider_name=provider.name,
        is_demo=provider.is_demo,
        is_simulated=provider.is_simulated,
        label=provider_label(
            provider.name,
            is_demo=provider.is_demo,
            is_simulated=provider.is_simulated,
        ),
        description=(
            "Deterministic local provider — no API key required."
            if provider.is_demo
            else "Configured multimodal provider using environment credentials."
        ),
    )


def _loads_json_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(item) for item in data if str(item).strip()]


def _analysis_to_read(analysis: IncidentAnalysis) -> IncidentAnalysisRead:
    video_code = analysis.video_asset.asset_code if analysis.video_asset else None
    job_code = analysis.processing_job.job_code if analysis.processing_job else None
    evidence = [
        AnalysisEvidenceRead(
            id=item.id,
            frame_id=item.frame_id,
            frame_code=item.frame_code,
            timestamp_seconds=item.timestamp_seconds,
            observation=item.observation,
            relevance=item.relevance,
            content_url=item.content_url,
        )
        for item in analysis.evidence_items
    ]
    review = None
    if analysis.review is not None:
        review = AnalysisReviewRead(
            id=analysis.review.id,
            decision=ReviewDecision(analysis.review.decision),
            reviewer_name=analysis.review.reviewer_name,
            notes=analysis.review.notes,
            reviewed_at=analysis.review.reviewed_at,
            created_at=analysis.review.created_at,
            updated_at=analysis.review.updated_at,
        )
    severity = (
        AnalysisSeverity(analysis.severity)
        if analysis.severity
        else None
    )
    return IncidentAnalysisRead(
        id=analysis.id,
        analysis_code=analysis.analysis_code,
        video_asset_id=analysis.video_asset_id,
        video_asset_code=video_code,
        processing_job_id=analysis.processing_job_id,
        processing_job_code=job_code,
        status=AnalysisStatus(analysis.status),
        provider_name=analysis.provider_name,
        is_demo=analysis.is_demo,
        is_simulated=analysis.is_simulated,
        incident_detected=analysis.incident_detected,
        incident_type=analysis.incident_type,
        summary=analysis.summary,
        detailed_analysis=analysis.detailed_analysis,
        severity=severity,
        confidence=analysis.confidence,
        recommended_actions=_loads_json_list(analysis.recommended_actions_json),
        limitations=_loads_json_list(analysis.limitations_json),
        inconclusive=analysis.inconclusive,
        error_code=analysis.error_code,
        error_message=analysis.error_message,
        started_at=analysis.started_at,
        completed_at=analysis.completed_at,
        created_at=analysis.created_at,
        updated_at=analysis.updated_at,
        evidence=evidence,
        review=review,
        provider_label=provider_label(
            analysis.provider_name,
            is_demo=analysis.is_demo,
            is_simulated=analysis.is_simulated,
        ),
        human_approval_required=True,
    )


def _get_video_or_404(db: Session, identifier: str) -> VideoAsset:
    video = db.scalar(
        select(VideoAsset)
        .options(selectinload(VideoAsset.camera), selectinload(VideoAsset.frames))
        .where(
            (VideoAsset.asset_code == identifier) | (VideoAsset.id == identifier)
        )
    )
    if video is None:
        raise AppError("VIDEO_NOT_FOUND", "Video asset was not found.", status_code=404)
    return video


def _get_analysis_or_404(db: Session, identifier: str) -> IncidentAnalysis:
    analysis = db.scalar(
        select(IncidentAnalysis)
        .options(
            selectinload(IncidentAnalysis.video_asset),
            selectinload(IncidentAnalysis.processing_job),
            selectinload(IncidentAnalysis.evidence_items),
            selectinload(IncidentAnalysis.review),
        )
        .where(
            (IncidentAnalysis.analysis_code == identifier)
            | (IncidentAnalysis.id == identifier)
        )
    )
    if analysis is None:
        raise AppError("ANALYSIS_NOT_FOUND", "Analysis was not found.", status_code=404)
    return analysis


def select_frames_for_analysis(
    frames: list[VideoFrame],
    *,
    max_frames: int,
    focus_offset_seconds: float | None = None,
) -> list[VideoFrame]:
    if not frames:
        return []
    ordered = sorted(frames, key=lambda item: item.timestamp_seconds)
    if len(ordered) <= max_frames:
        return ordered
    if max_frames == 1:
        if focus_offset_seconds is None:
            return [ordered[len(ordered) // 2]]
        nearest = min(
            ordered,
            key=lambda item: abs(item.timestamp_seconds - focus_offset_seconds),
        )
        return [nearest]

    if focus_offset_seconds is not None:
        # Prefer frames nearest the detector event offset, keep chronological order.
        ranked = sorted(
            ordered,
            key=lambda item: abs(item.timestamp_seconds - focus_offset_seconds),
        )
        selected = sorted(ranked[:max_frames], key=lambda item: item.timestamp_seconds)
        return selected

    # Evenly spaced indices including first and last.
    indices = [
        round(i * (len(ordered) - 1) / (max_frames - 1))
        for i in range(max_frames)
    ]
    unique_indices = sorted(set(indices))
    return [ordered[index] for index in unique_indices]


def _analyze_response_from_analysis(analysis: IncidentAnalysis) -> AnalyzeVideoResponse:
    return AnalyzeVideoResponse(
        analysis_code=analysis.analysis_code,
        job_code=analysis.processing_job.job_code if analysis.processing_job else "",
        status=AnalysisStatus(analysis.status),
        provider_name=analysis.provider_name,
        is_demo=analysis.is_demo,
        is_simulated=analysis.is_simulated,
        message=(
            "Existing analysis reused (idempotent)."
            if analysis.status
            in {
                AnalysisStatus.COMPLETED.value,
                AnalysisStatus.NEEDS_REVIEW.value,
                AnalysisStatus.QUEUED.value,
                AnalysisStatus.RUNNING.value,
            }
            else (
                "Analysis queued. Demo AI will produce a simulated structured result."
                if analysis.is_demo
                else "Analysis queued with the configured multimodal provider."
            )
        ),
    )


def ensure_analysis_for_video(
    db: Session,
    video_identifier: str,
    *,
    force_new: bool = False,
    settings: Settings | None = None,
) -> tuple[AnalyzeVideoResponse, bool]:
    """Idempotently ensure an analysis exists for a ready video.

    Returns (response, should_run_job). When should_run_job is True the caller
    must schedule/run run_analysis_job for the new analysis.
    """
    cfg = settings or get_settings()
    video = _get_video_or_404(db, video_identifier)

    if video.status != VideoStatus.READY.value:
        raise AppError(
            "VIDEO_NOT_READY",
            "Video must finish processing before analysis can start.",
            status_code=409,
        )

    frames = list(video.frames)
    if not frames:
        raise AppError(
            "FRAMES_REQUIRED",
            "No extracted frames are available for analysis.",
            status_code=409,
        )

    if not force_new:
        active = db.scalars(
            select(IncidentAnalysis)
            .options(selectinload(IncidentAnalysis.processing_job))
            .where(
                IncidentAnalysis.video_asset_id == video.id,
                IncidentAnalysis.status.in_(
                    [AnalysisStatus.QUEUED.value, AnalysisStatus.RUNNING.value]
                ),
            )
            .order_by(IncidentAnalysis.created_at.desc())
        ).first()
        if active is not None:
            return _analyze_response_from_analysis(active), False

        completed = db.scalars(
            select(IncidentAnalysis)
            .options(selectinload(IncidentAnalysis.processing_job))
            .where(
                IncidentAnalysis.video_asset_id == video.id,
                IncidentAnalysis.status.in_(
                    [
                        AnalysisStatus.COMPLETED.value,
                        AnalysisStatus.NEEDS_REVIEW.value,
                    ]
                ),
            )
            .order_by(IncidentAnalysis.created_at.desc())
        ).first()
        if completed is not None:
            if completed.incident_detected:
                try:
                    from app.services.workflow import prepare_response_for_analysis

                    prepare_response_for_analysis(db, completed.analysis_code)
                except Exception:
                    logger.exception(
                        "Idempotent prepare failed for %s", completed.analysis_code
                    )
            return _analyze_response_from_analysis(completed), False

    response = start_analysis(db, video_identifier, settings=cfg)
    return response, True


def start_analysis(
    db: Session,
    video_identifier: str,
    *,
    settings: Settings | None = None,
) -> AnalyzeVideoResponse:
    cfg = settings or get_settings()
    video = _get_video_or_404(db, video_identifier)

    if video.status != VideoStatus.READY.value:
        raise AppError(
            "VIDEO_NOT_READY",
            "Video must finish processing before analysis can start.",
            status_code=409,
        )

    frames = list(video.frames)
    if not frames:
        raise AppError(
            "FRAMES_REQUIRED",
            "No extracted frames are available for analysis.",
            status_code=409,
        )

    active = db.scalar(
        select(IncidentAnalysis).where(
            IncidentAnalysis.video_asset_id == video.id,
            IncidentAnalysis.status.in_(
                [AnalysisStatus.QUEUED.value, AnalysisStatus.RUNNING.value]
            ),
        )
    )
    if active is not None:
        raise AppError(
            "ANALYSIS_IN_PROGRESS",
            "An analysis job is already running for this video.",
            status_code=409,
        )

    provider = get_ai_provider(cfg)
    job = ProcessingJob(
        id=str(uuid4()),
        job_code=generate_job_code(db),
        video_asset_id=video.id,
        job_type=JobType.ANALYSIS.value,
        status=JobStatus.QUEUED.value,
        progress=0,
        current_step="queued",
    )
    analysis = IncidentAnalysis(
        id=str(uuid4()),
        analysis_code=generate_analysis_code(db),
        video_asset_id=video.id,
        processing_job_id=job.id,
        status=AnalysisStatus.QUEUED.value,
        provider_name=provider.name,
        is_demo=provider.is_demo,
        is_simulated=provider.is_simulated,
    )
    review = AnalysisReview(
        id=str(uuid4()),
        analysis_id=analysis.id,
        decision=ReviewDecision.PENDING.value,
        reviewer_name="demo-reviewer",
        notes=None,
        reviewed_at=None,
    )
    db.add(job)
    db.add(analysis)
    db.add(review)
    db.commit()
    db.refresh(analysis)
    db.refresh(job)

    return AnalyzeVideoResponse(
        analysis_code=analysis.analysis_code,
        job_code=job.job_code,
        status=AnalysisStatus(analysis.status),
        provider_name=analysis.provider_name,
        is_demo=analysis.is_demo,
        is_simulated=analysis.is_simulated,
        message=(
            "Analysis queued. Demo AI will produce a simulated structured result."
            if analysis.is_demo
            else "Analysis queued with the configured multimodal provider."
        ),
    )


def get_analysis(db: Session, identifier: str) -> IncidentAnalysisRead:
    return _analysis_to_read(_get_analysis_or_404(db, identifier))


def list_video_analyses(
    db: Session,
    video_identifier: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[IncidentAnalysisRead], Meta]:
    video = _get_video_or_404(db, video_identifier)
    total = db.scalar(
        select(func.count())
        .select_from(IncidentAnalysis)
        .where(IncidentAnalysis.video_asset_id == video.id)
    ) or 0
    rows = db.scalars(
        select(IncidentAnalysis)
        .options(
            selectinload(IncidentAnalysis.video_asset),
            selectinload(IncidentAnalysis.processing_job),
            selectinload(IncidentAnalysis.evidence_items),
            selectinload(IncidentAnalysis.review),
        )
        .where(IncidentAnalysis.video_asset_id == video.id)
        .order_by(IncidentAnalysis.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return (
        [_analysis_to_read(row) for row in rows],
        Meta(count=total, limit=limit, offset=offset),
    )


def submit_review(
    db: Session,
    identifier: str,
    payload: AnalysisReviewCreate,
) -> IncidentAnalysisRead:
    analysis = _get_analysis_or_404(db, identifier)
    if analysis.status not in {
        AnalysisStatus.COMPLETED.value,
        AnalysisStatus.NEEDS_REVIEW.value,
    }:
        raise AppError(
            "ANALYSIS_NOT_REVIEWABLE",
            "Only completed analyses can receive a human review decision.",
            status_code=409,
        )

    review = analysis.review
    if review is None:
        review = AnalysisReview(analysis_id=analysis.id)
        db.add(review)

    review.decision = payload.decision.value
    review.reviewer_name = payload.reviewer_name
    review.notes = payload.notes
    review.reviewed_at = utc_now()
    analysis.status = AnalysisStatus.NEEDS_REVIEW.value
    if payload.decision == ReviewDecision.CONFIRMED:
        analysis.status = AnalysisStatus.COMPLETED.value
    elif payload.decision == ReviewDecision.REJECTED:
        analysis.status = AnalysisStatus.COMPLETED.value
    elif payload.decision == ReviewDecision.NEEDS_MORE_INFO:
        analysis.status = AnalysisStatus.NEEDS_REVIEW.value

    # Keep operator notification / linked incident in sync with the review gate.
    note = db.scalars(
        select(OperatorNotification).where(OperatorNotification.analysis_id == analysis.id)
    ).first()
    if note is not None:
        if payload.decision == ReviewDecision.CONFIRMED:
            note.review_status = "confirmed"
            note.status = "reviewed"
            note.message = "Incident confirmed — awaiting action approval"
        elif payload.decision == ReviewDecision.REJECTED:
            note.review_status = "rejected"
            note.status = "resolved"
            note.message = "Marked as false alarm"
            note.dismissed = True
        elif payload.decision == ReviewDecision.NEEDS_MORE_INFO:
            note.review_status = "needs_more_info"
            note.status = "attention"
            note.message = "Needs more information"
        if note.incident_id:
            incident = db.get(Incident, note.incident_id)
            if incident is not None:
                if payload.decision == ReviewDecision.CONFIRMED:
                    incident.status = IncidentStatus.APPROVED.value
                    incident.review_status = ReviewStatus.APPROVED.value
                elif payload.decision == ReviewDecision.REJECTED:
                    incident.status = IncidentStatus.DISMISSED.value
                    incident.review_status = ReviewStatus.REJECTED.value
                elif payload.decision == ReviewDecision.NEEDS_MORE_INFO:
                    incident.status = IncidentStatus.AWAITING_REVIEW.value
                    incident.review_status = ReviewStatus.PENDING.value

    db.commit()
    return get_analysis(db, analysis.analysis_code)


def _update_job(
    db: Session,
    job: ProcessingJob | None,
    *,
    status: JobStatus,
    progress: int,
    step: str,
    error_code: str | None = None,
    error_message: str | None = None,
) -> None:
    if job is None:
        return
    job.status = status.value
    job.progress = progress
    job.current_step = step
    job.error_code = error_code
    job.error_message = error_message
    if status == JobStatus.PROCESSING and job.started_at is None:
        job.started_at = utc_now()
    if status in {JobStatus.COMPLETED, JobStatus.FAILED}:
        job.completed_at = utc_now()


def run_analysis_job(analysis_id: str, job_id: str) -> None:
    """Background worker: analyze selected frames and persist structured results."""
    db = SessionLocal()
    try:
        analysis = db.scalar(
            select(IncidentAnalysis)
            .options(
                selectinload(IncidentAnalysis.video_asset).selectinload(VideoAsset.camera),
                selectinload(IncidentAnalysis.video_asset).selectinload(VideoAsset.frames),
                selectinload(IncidentAnalysis.processing_job),
                selectinload(IncidentAnalysis.evidence_items),
            )
            .where(IncidentAnalysis.id == analysis_id)
        )
        job = db.get(ProcessingJob, job_id)
        if analysis is None:
            logger.error("Analysis %s not found for background job", analysis_id)
            return

        settings = get_settings()
        analysis.status = AnalysisStatus.RUNNING.value
        analysis.started_at = utc_now()
        analysis.error_code = None
        analysis.error_message = None
        _update_job(
            db,
            job,
            status=JobStatus.PROCESSING,
            progress=10,
            step="selecting_frames",
        )
        db.commit()

        video = analysis.video_asset
        if video is None:
            raise AppError("VIDEO_NOT_FOUND", "Video asset missing for analysis.", 404)

        focus_offset = None
        try:
            from app.services.detector_ingestion import get_focus_offset_for_video

            focus_offset = get_focus_offset_for_video(db, video.id)
        except Exception:  # pragma: no cover
            focus_offset = None

        selected = select_frames_for_analysis(
            list(video.frames),
            max_frames=settings.ai_max_frames,
            focus_offset_seconds=focus_offset,
        )
        frame_inputs: list[FrameAnalysisInput] = []
        frame_by_code: dict[str, VideoFrame] = {}
        for frame in selected:
            absolute = storage.resolve_frame_path(frame.stored_filename, settings)
            if not absolute.is_file():
                continue
            frame_by_code[frame.frame_code] = frame
            frame_inputs.append(
                FrameAnalysisInput(
                    frame_code=frame.frame_code,
                    timestamp_seconds=frame.timestamp_seconds,
                    absolute_path=str(absolute),
                    content_url=f"/api/frames/{frame.frame_code}/content",
                )
            )

        _update_job(
            db,
            job,
            status=JobStatus.PROCESSING,
            progress=40,
            step="running_provider",
        )
        db.commit()

        provider = get_ai_provider(settings)
        camera_name = video.camera.name if video.camera is not None else None
        result = provider.analyze_frames(
            frames=frame_inputs,
            location=video.location,
            camera_name=camera_name,
            video_asset_code=video.asset_code,
            duration_seconds=video.duration_seconds,
        )

        _update_job(
            db,
            job,
            status=JobStatus.PROCESSING,
            progress=80,
            step="persisting_results",
        )
        db.commit()

        # Replace prior evidence rows for this analysis.
        for existing in list(analysis.evidence_items):
            db.delete(existing)
        db.flush()

        for item in result.evidence:
            frame = frame_by_code.get(item.frame_id)
            if frame is None:
                # Skip hallucinated frame IDs rather than failing the whole job
                # for demo robustness; OpenAI provider already validates strictly.
                logger.warning(
                    "Skipping evidence with unknown frame_id %s",
                    item.frame_id,
                )
                continue
            db.add(
                AnalysisEvidence(
                    analysis_id=analysis.id,
                    frame_id=frame.id,
                    frame_code=frame.frame_code,
                    timestamp_seconds=frame.timestamp_seconds,
                    observation=item.observation,
                    relevance=item.relevance,
                    content_url=f"/api/frames/{frame.frame_code}/content",
                )
            )

        analysis.incident_detected = result.incident_detected
        analysis.incident_type = result.incident_type
        analysis.summary = result.summary
        analysis.detailed_analysis = result.detailed_analysis
        analysis.severity = result.severity.value
        analysis.confidence = result.confidence
        analysis.recommended_actions_json = json.dumps(result.recommended_actions)
        analysis.limitations_json = json.dumps(result.limitations)
        analysis.inconclusive = result.inconclusive
        analysis.provider_name = provider.name
        analysis.is_demo = provider.is_demo
        analysis.is_simulated = provider.is_simulated
        analysis.status = (
            AnalysisStatus.NEEDS_REVIEW.value
            if result.incident_detected
            else AnalysisStatus.COMPLETED.value
        )
        analysis.completed_at = utc_now()
        _update_job(
            db,
            job,
            status=JobStatus.COMPLETED,
            progress=100,
            step="completed",
        )
        db.commit()

        # Idempotent post-analysis preparation (notification + SOP + draft plan).
        if result.incident_detected:
            try:
                from app.services.workflow import prepare_response_for_analysis

                prepare_response_for_analysis(db, analysis.analysis_code)
            except Exception:
                logger.exception(
                    "Post-analysis workflow preparation failed for %s",
                    analysis.analysis_code,
                )
    except AIProviderError as exc:
        logger.exception("AI provider failed for analysis %s", analysis_id)
        _fail_analysis(db, analysis_id, job_id, "AI_PROVIDER_ERROR", str(exc))
    except AppError as exc:
        logger.exception("Analysis job app error for %s", analysis_id)
        _fail_analysis(db, analysis_id, job_id, exc.code, exc.message)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected analysis failure for %s", analysis_id)
        _fail_analysis(db, analysis_id, job_id, "ANALYSIS_FAILED", str(exc))
    finally:
        db.close()


def _fail_analysis(
    db: Session,
    analysis_id: str,
    job_id: str,
    error_code: str,
    error_message: str,
) -> None:
    analysis = db.get(IncidentAnalysis, analysis_id)
    job = db.get(ProcessingJob, job_id)
    if analysis is not None:
        analysis.status = AnalysisStatus.FAILED.value
        analysis.error_code = error_code
        analysis.error_message = error_message
        analysis.completed_at = utc_now()
    _update_job(
        db,
        job,
        status=JobStatus.FAILED,
        progress=100,
        step="failed",
        error_code=error_code,
        error_message=error_message,
    )
    db.commit()

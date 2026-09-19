"""Safe demo-state reset — only clears demo runtime artifacts when DEMO_MODE is enabled."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.analysis_evidence import AnalysisEvidence
from app.models.analysis_review import AnalysisReview
from app.models.detector import DetectorEventIngestion
from app.models.execution import ActionExecution, AuditEvent, IncidentReport, PlanApproval
from app.models.incident_analysis import IncidentAnalysis
from app.models.notification import OperatorNotification
from app.models.procedure_policy import (
    PlanCitation,
    PlannedAction,
    ProcedureRetrieval,
    ProcedureRetrievalMatch,
    ResponsePlan,
)
from app.models.processing_job import ProcessingJob
from app.models.video import VideoAsset
from app.models.video_frame import VideoFrame
from app.schemas.detector import DemoResetRequest, DemoResetResponse
from app.seed.seed_data import seed_database
from app.services import storage


def _clear_directory_files(directory: Path) -> int:
    if not directory.exists():
        return 0
    removed = 0
    for path in directory.iterdir():
        if path.is_file():
            path.unlink(missing_ok=True)
            removed += 1
        elif path.is_dir():
            # Only remove one level of generated subdirs under known roots.
            for child in path.rglob("*"):
                if child.is_file():
                    child.unlink(missing_ok=True)
                    removed += 1
            for child in sorted(path.rglob("*"), reverse=True):
                if child.is_dir():
                    child.rmdir()
            path.rmdir()
    return removed


def reset_demo_state(
    db: Session,
    payload: DemoResetRequest,
    *,
    settings: Settings | None = None,
) -> DemoResetResponse:
    cfg = settings or get_settings()
    if not cfg.demo_mode:
        raise AppError(
            "DEMO_RESET_DISABLED",
            "Demo reset is only available when DEMO_MODE=true.",
            status_code=403,
        )

    video_count = db.scalar(select(VideoAsset.id)) is not None
    videos = list(db.scalars(select(VideoAsset)).all())
    detector_count = len(list(db.scalars(select(DetectorEventIngestion)).all()))
    report_rows = list(db.scalars(select(IncidentReport)).all())

    # Delete runtime rows in FK-safe order.
    db.execute(delete(ActionExecution))
    db.execute(delete(PlanApproval))
    db.execute(delete(AuditEvent))
    db.execute(delete(IncidentReport))
    db.execute(delete(PlanCitation))
    db.execute(delete(PlannedAction))
    db.execute(delete(ResponsePlan))
    db.execute(delete(ProcedureRetrievalMatch))
    db.execute(delete(ProcedureRetrieval))
    db.execute(delete(OperatorNotification))
    db.execute(delete(AnalysisEvidence))
    db.execute(delete(AnalysisReview))
    db.execute(delete(DetectorEventIngestion))
    # Clear analysis FKs before deleting analyses / jobs / videos.
    for analysis in db.scalars(select(IncidentAnalysis)).all():
        db.delete(analysis)
    db.flush()
    for job in db.scalars(select(ProcessingJob)).all():
        db.delete(job)
    db.flush()
    for frame in db.scalars(select(VideoFrame)).all():
        db.delete(frame)
    db.flush()
    for video in videos:
        db.delete(video)
    db.commit()

    storage.ensure_storage_directories(cfg)
    _clear_directory_files(cfg.upload_path)
    _clear_directory_files(cfg.frame_path)
    deleted_report_files = _clear_directory_files(cfg.report_path)
    # Never touch arbitrary user paths — only configured demo media roots.
    cfg.detector_events_path.mkdir(parents=True, exist_ok=True)

    # Re-seed cameras/incidents/procedures without wiping seed IDs.
    seed_database(db)

    return DemoResetResponse(
        reset=True,
        message=(
            "Demo runtime state cleared and seed data restored. "
            "Uploaded clips, detector ingestions, analyses, plans, executions, "
            "and generated reports were removed from configured demo directories only."
        ),
        deleted_videos=len(videos) if video_count or videos else len(videos),
        deleted_detector_events=detector_count,
        deleted_reports=max(len(report_rows), deleted_report_files),
        reseeding_completed=True,
        demo_mode=True,
    )

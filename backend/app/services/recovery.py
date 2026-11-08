"""Restart recovery for persisted local detector jobs in a single API process.

Snapshots work before accepting requests; new uploads are not stolen from their
normal background task. This is not a distributed task queue/lease protocol.
"""

import logging
from sqlalchemy import select
from app.models.detector import DetectorEventIngestion
from app.models.video import VideoAsset
from app.models.processing_job import ProcessingJob
from app.core.enums import VideoStatus
from app.services import detector_ingestion, videos

logger = logging.getLogger(__name__)


def snapshot_interrupted_events():
    with detector_ingestion.SessionLocal() as db:
        return list(
            db.scalars(
                select(DetectorEventIngestion.event_id).where(
                    DetectorEventIngestion.is_simulated.is_(False),
                    DetectorEventIngestion.video_asset_id.is_not(None),
                    DetectorEventIngestion.status.in_(
                        ["processing", "ready", "analyzing"]
                    ),
                )
            ).all()
        )


def recover_events(event_ids):
    result = {"attempted": len(event_ids), "recovered": 0, "failed": 0}
    for event_id in event_ids:
        try:
            with detector_ingestion.SessionLocal() as db:
                row = detector_ingestion.get_ingestion(db, event_id)
                video = db.get(VideoAsset, row.video_asset_id)
                job = db.get(ProcessingJob, row.processing_job_id)
                if video and job and video.status != VideoStatus.READY.value:
                    video_id, job_id = video.id, job.id
                    db.close()
                    videos.process_video_job(video_id, job_id)
            with detector_ingestion.SessionLocal() as db:
                row = detector_ingestion.get_ingestion(db, event_id)
                video = db.get(VideoAsset, row.video_asset_id)
                if video and video.status == VideoStatus.READY.value:
                    from app.services.local_detection import prepare_detector_analysis

                    prepare_detector_analysis(db, video)
                outcome = detector_ingestion.advance_ingestion(
                    db, event_id, auto_analyze=False
                )
                result[
                    "recovered" if outcome.status.value == "completed" else "failed"
                ] += 1
        except Exception:
            result["failed"] += 1
            logger.exception("Interrupted detector recovery failed for %s", event_id)
    logger.info("Detector restart recovery: %s", result)
    return result

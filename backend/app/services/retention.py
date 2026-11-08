"""Expire resolved evidence only, retaining relational/audit provenance.

Dry-run by default. Open/unlinked incidents and unfinished jobs are preserved.
"""

import json
from datetime import timedelta
from sqlalchemy import select
from app.core.config import get_settings
from app.database.base import utc_now
from app.models.video import VideoAsset
from app.models.notification import OperatorNotification
from app.models.incident import Incident
from app.models.incident_analysis import IncidentAnalysis
from app.models.platform import CameraConfiguration
from app.services.storage import resolve_upload_path, resolve_frame_path


def expire_evidence(db, *, apply=False):
    cfg = get_settings()
    candidates = []
    removed = 0
    videos = db.scalars(
        select(VideoAsset).where(VideoAsset.status.in_(["ready", "failed"]))
    ).all()
    for video in videos:
        camera_cfg = (
            db.get(CameraConfiguration, video.camera_id) if video.camera_id else None
        )
        days = (
            json.loads(camera_cfg.policy_json).get(
                "retention_days", cfg.evidence_retention_days
            )
            if camera_cfg
            else cfg.evidence_retention_days
        )
        created = (
            video.created_at.replace(tzinfo=utc_now().tzinfo)
            if video.created_at.tzinfo is None
            else video.created_at
        )
        if created > utc_now() - timedelta(days=days):
            continue
        note = db.scalar(
            select(OperatorNotification).where(
                OperatorNotification.video_asset_id == video.id
            )
        )
        incident = (
            db.get(Incident, note.incident_id) if note and note.incident_id else None
        )
        if not incident or incident.status not in {"resolved", "dismissed", "closed"}:
            continue
        if any(x.status in {"queued", "processing"} for x in video.jobs):
            continue
        candidates.append(video.asset_code)
        if apply:
            from app.services.playback import playback_path

            paths = [
                resolve_upload_path(video.stored_filename, cfg),
                playback_path(video.stored_filename, cfg),
            ] + [resolve_frame_path(x.stored_filename, cfg) for x in video.frames]
            for path in paths:
                if path.is_file():
                    path.unlink()
                    removed += 1
            video.status = "expired"
    if apply:
        db.flush()
    return {
        "dry_run": not apply,
        "candidate_asset_codes": candidates,
        "removed_files": removed,
        "preserved": "Open incidents, unlinked media, reports, metadata and audit events are retained.",
    }

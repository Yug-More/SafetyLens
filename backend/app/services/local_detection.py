"""Translate actual detector observations without sending them through scripted Demo AI."""

import json
from uuid import uuid4
from sqlalchemy import select
from app.database.base import utc_now
from app.models.detector import DetectorEventIngestion
from app.models.incident_analysis import IncidentAnalysis
from app.models.analysis_review import AnalysisReview
from app.models.analysis_evidence import AnalysisEvidence
from app.models.video_frame import VideoFrame


def prepare_detector_analysis(db, video):
    ingestion = db.scalar(
        select(DetectorEventIngestion).where(
            DetectorEventIngestion.video_asset_id == video.id
        )
    )
    if not ingestion or ingestion.is_simulated:
        return None
    existing = db.scalar(
        select(IncidentAnalysis).where(IncidentAnalysis.video_asset_id == video.id)
    )
    if existing:
        return existing
    from app.services.analysis import generate_analysis_code

    ppe = ingestion.event_type == "ppe_noncompliance"
    metrics = json.loads(ingestion.metrics_json or "{}")
    down = ingestion.event_type == "prolonged_person_down"
    signals = json.loads(ingestion.trigger_signals_json or "[]")
    falling = "rapid_drop" in signals
    learned = "learned_temporal_candidate" in signals
    observation = (
        "Required PPE not visible over repeated observations; verify occlusion and association."
        if ppe
        else "Person remains down; falling motion was not established."
        if down
        else "Learned causal pose classifier flagged a candidate; falling motion and injury are unverified."
        if learned
        else "Pose-derived rapid descent followed by sustained down posture; injury is unknown."
        if falling
        else "Detector submitted a possible person-down candidate; falling motion and injury are unverified."
    )
    analysis = IncidentAnalysis(
        id=str(uuid4()),
        analysis_code=generate_analysis_code(db),
        video_asset_id=video.id,
        status="needs_review",
        provider_name="local_cv",
        is_demo=False,
        is_simulated=False,
        incident_detected=True,
        incident_type="ppe_noncompliance" if ppe else "possible_person_down",
        summary=observation,
        detailed_analysis=observation
        + " Local detector findings are uncalibrated and require human review.",
        severity="medium" if ppe else "high",
        confidence=None,
        recommended_actions_json=json.dumps(
            ["Review the preserved evidence before taking action"]
        ),
        limitations_json=json.dumps(
            [
                "Experimental local detector; not a medical diagnosis or safety certification"
            ]
        ),
        inconclusive=False,
        analysis_mode="local_cv",
        human_review_required=True,
        required_ppe_json=json.dumps(metrics.get("required_ppe", [])),
        observed_ppe_json=json.dumps(metrics.get("observed_ppe", [])),
        possibly_missing_ppe_json=json.dumps(metrics.get("possibly_missing_ppe", [])),
        completed_at=utc_now(),
    )
    db.add(analysis)
    db.flush()
    db.add(
        AnalysisReview(
            analysis_id=analysis.id, decision="pending", reviewer_name="unassigned"
        )
    )
    frames = db.scalars(
        select(VideoFrame)
        .where(VideoFrame.video_asset_id == video.id)
        .order_by(VideoFrame.timestamp_seconds)
    ).all()
    if frames:
        focus = ingestion.clip_event_offset_seconds or 0
        frame = min(frames, key=lambda x: abs(x.timestamp_seconds - focus))
        db.add(
            AnalysisEvidence(
                analysis_id=analysis.id,
                frame_id=frame.id,
                frame_code=frame.frame_code,
                timestamp_seconds=frame.timestamp_seconds,
                observation=observation,
                relevance="supporting",
                content_url=f"/api/frames/{frame.frame_code}/content",
            )
        )
    ingestion.analysis_id = analysis.id
    ingestion.status = "completed"
    db.commit()
    from app.services.workflow import prepare_response_for_analysis

    workflow = prepare_response_for_analysis(db, analysis.analysis_code)
    ingestion.incident_id = workflow.incident_id
    db.commit()
    return analysis

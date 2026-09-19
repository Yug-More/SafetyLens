"""Prompt builders for multimodal incident analysis."""

from __future__ import annotations

from app.ai.schemas import FrameAnalysisInput

SYSTEM_PROMPT = """You are SafetyLens, a workplace safety multimodal analyst.
Analyze ONLY the provided video frames and metadata.
Return a single JSON object matching the required schema.
Never invent frame IDs that were not provided.
Do not treat pose quality or heuristic detector scores as fall probability.
If evidence is insufficient or visibility is poor, set inconclusive=true and
incident_detected=false with severity "none". Distinguish inconclusive evidence
from a confident clear-negative (no_incident with conclusive observations).
Keep confidence calibrated to visual evidence quality.
Critical response actions always require human approval."""


def build_user_prompt(
    *,
    frames: list[FrameAnalysisInput],
    location: str,
    camera_name: str | None,
    video_asset_code: str,
    duration_seconds: float | None,
) -> str:
    frame_lines = [
        (
            f"- frame_id={frame.frame_code} "
            f"timestamp_seconds={frame.timestamp_seconds:.3f} "
            f"content_url={frame.content_url}"
        )
        for frame in frames
    ]
    duration = (
        f"{duration_seconds:.2f}s" if duration_seconds is not None else "unknown"
    )
    return (
        "Analyze these workplace camera frames for a possible safety incident "
        "(especially worker fall / person down).\n\n"
        f"video_asset_code: {video_asset_code}\n"
        f"location: {location}\n"
        f"camera_name: {camera_name or 'unassigned'}\n"
        f"duration_seconds: {duration}\n"
        f"frame_count_provided: {len(frames)}\n\n"
        "Frames:\n"
        + "\n".join(frame_lines)
        + "\n\n"
        "Respond with JSON fields: incident_detected (bool), incident_type (string), "
        "summary, detailed_analysis, severity (none|low|medium|high|critical), "
        "confidence (0-1), evidence (array of {frame_id, timestamp_seconds, "
        "observation, relevance}), recommended_actions (string array), "
        "limitations (string array), inconclusive (bool)."
    )

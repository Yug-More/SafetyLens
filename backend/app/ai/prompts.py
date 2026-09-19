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
Critical response actions always require human approval.

Allowed incident_type values ONLY:
- possible_person_down
- ppe_noncompliance
- no_incident
- insufficient_evidence

For PPE: only evaluate hard_hat and high_visibility_vest against the camera's
required_ppe list. If an item is occluded, blurry, distant, or not clearly
visible, do NOT claim it is definitely missing — put it in possibly_missing_ppe
with cautious wording ("not visible in the selected evidence") or return
insufficient_evidence. Never infer safety footwear, gloves, glasses, or respirators.
Never default to person-down when evidence does not support a fall."""


def build_user_prompt(
    *,
    frames: list[FrameAnalysisInput],
    location: str,
    camera_name: str | None,
    video_asset_code: str,
    duration_seconds: float | None,
    required_ppe: list[str] | None = None,
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
    ppe_line = (
        f"required_ppe: {', '.join(required_ppe)}\n"
        if required_ppe
        else "required_ppe: none configured for this camera\n"
    )
    return (
        "Analyze these workplace camera frames for a possible safety incident.\n"
        "Choose exactly one allowed incident_type. Do not bias toward person-down "
        "unless visual evidence supports a fall or person on the floor.\n\n"
        f"video_asset_code: {video_asset_code}\n"
        f"location: {location}\n"
        f"camera_name: {camera_name or 'unassigned'}\n"
        f"duration_seconds: {duration}\n"
        f"{ppe_line}"
        f"frame_count_provided: {len(frames)}\n\n"
        "Frames:\n"
        + "\n".join(frame_lines)
        + "\n\n"
        "Respond with JSON fields: incident_detected (bool), incident_type (string), "
        "summary, detailed_analysis, severity (none|low|medium|high|critical), "
        "confidence (0-1), evidence (array of {frame_id, timestamp_seconds, "
        "observation, relevance}), recommended_actions (string array), "
        "limitations (string array), inconclusive (bool), "
        "required_ppe (string array), observed_ppe (string array), "
        "possibly_missing_ppe (string array), analysis_mode (use \"multimodal\"), "
        "human_review_required (bool, true when incident_detected)."
    )

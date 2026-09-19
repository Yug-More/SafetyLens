"""Deterministic demo multimodal provider — no external credentials required."""

from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.schemas import (
    AnalysisEvidenceItem,
    FrameAnalysisInput,
    IncidentAnalysisResult,
)
from app.core.enums import AnalysisSeverity


class DemoAIProvider(AIProvider):
    name = "demo"
    is_demo = True
    is_simulated = True

    def analyze_frames(
        self,
        *,
        frames: list[FrameAnalysisInput],
        location: str,
        camera_name: str | None,
        video_asset_code: str,
        duration_seconds: float | None,
    ) -> IncidentAnalysisResult:
        if not frames:
            return IncidentAnalysisResult(
                incident_detected=False,
                incident_type="insufficient_evidence",
                summary=(
                    "Demo AI could not analyze this video because no frames "
                    "were available."
                ),
                detailed_analysis=(
                    "Frame extraction produced an empty set. Without visual "
                    "evidence the demo provider returns an inconclusive result "
                    "rather than a confident clear-negative."
                ),
                severity=AnalysisSeverity.NONE,
                confidence=0.15,
                evidence=[],
                recommended_actions=[
                    "Re-run video processing to extract frames",
                    "Confirm the upload completed successfully",
                ],
                limitations=[
                    "Demo AI provider — deterministic simulated analysis",
                    "No frames were available for inspection",
                ],
                inconclusive=True,
            )

        # Deterministic selection: use first, middle, and last frames when present.
        selected = _select_key_frames(frames)
        mid = selected[len(selected) // 2]
        start = selected[0]
        end = selected[-1]

        # Heuristic: longer clips with mid/late timestamps lean toward person-down demo.
        lean_incident = (
            (duration_seconds or 0) >= 3.0
            or mid.timestamp_seconds >= 2.0
            or len(frames) >= 4
        )

        if lean_incident:
            evidence = [
                AnalysisEvidenceItem(
                    frame_id=start.frame_code,
                    timestamp_seconds=start.timestamp_seconds,
                    observation=(
                        f"At {start.timestamp_seconds:.1f}s near {location}, "
                        "a worker is upright in the monitored area "
                        f"({camera_name or 'unassigned camera'})."
                    ),
                    relevance="context",
                ),
                AnalysisEvidenceItem(
                    frame_id=mid.frame_code,
                    timestamp_seconds=mid.timestamp_seconds,
                    observation=(
                        f"At {mid.timestamp_seconds:.1f}s the worker posture "
                        "appears to transition toward the floor — possible fall."
                    ),
                    relevance="supporting",
                ),
                AnalysisEvidenceItem(
                    frame_id=end.frame_code,
                    timestamp_seconds=end.timestamp_seconds,
                    observation=(
                        f"At {end.timestamp_seconds:.1f}s the person remains low "
                        "to the ground with limited motion, consistent with a "
                        "person-down situation pending human review."
                    ),
                    relevance="supporting",
                ),
            ]
            # Deduplicate if start/mid/end collapse to fewer unique frames.
            unique: dict[str, AnalysisEvidenceItem] = {}
            for item in evidence:
                unique[item.frame_id] = item
            evidence = list(unique.values())

            return IncidentAnalysisResult(
                incident_detected=True,
                incident_type="possible_person_down",
                summary=(
                    f"Demo analysis flagged a possible person-down event in "
                    f"{location} on video {video_asset_code}."
                ),
                detailed_analysis=(
                    "This is a deterministic Demo AI result for hackathon "
                    "rehearsal. Selected frames show an upright worker, a "
                    "posture transition, and a low-to-ground posture with "
                    "limited motion. Pose quality or detector heuristic scores "
                    "are not used as fall probability. A human reviewer must "
                    "confirm before any critical response action."
                ),
                severity=AnalysisSeverity.HIGH,
                confidence=0.78,
                evidence=evidence,
                recommended_actions=[
                    "Dispatch a nearby supervisor to verify the worker's condition",
                    "Keep the camera feed under observation until review completes",
                    "Do not trigger automated emergency calls without approval",
                ],
                limitations=[
                    "Demo AI provider — simulated multimodal analysis",
                    "Not a calibrated fall detector; visual interpretation is illustrative",
                    "Critical actions require explicit human approval",
                ],
                inconclusive=False,
            )

        evidence = [
            AnalysisEvidenceItem(
                frame_id=frame.frame_code,
                timestamp_seconds=frame.timestamp_seconds,
                observation=(
                    f"Frame at {frame.timestamp_seconds:.1f}s shows routine "
                    f"activity near {location}; no clear fall transition."
                ),
                relevance="context",
            )
            for frame in selected[:3]
        ]
        return IncidentAnalysisResult(
            incident_detected=False,
            incident_type="no_incident",
            summary=(
                f"Demo analysis found no clear safety incident in "
                f"{video_asset_code} at {location}."
            ),
            detailed_analysis=(
                "Deterministic Demo AI reviewed the available frames and did "
                "not observe a clear fall or person-down transition. This is "
                "a simulated clear-negative for short or early-frame clips, "
                "not a production vision model judgment."
            ),
            severity=AnalysisSeverity.NONE,
            confidence=0.62,
            evidence=evidence,
            recommended_actions=[
                "Continue routine monitoring",
                "Re-analyze if additional evidence becomes available",
            ],
            limitations=[
                "Demo AI provider — simulated multimodal analysis",
                "Short or early-frame samples may miss brief events",
            ],
            inconclusive=False,
        )


def _select_key_frames(frames: list[FrameAnalysisInput]) -> list[FrameAnalysisInput]:
    if len(frames) == 1:
        return frames
    if len(frames) == 2:
        return frames
    mid_index = len(frames) // 2
    return [frames[0], frames[mid_index], frames[-1]]

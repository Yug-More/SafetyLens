"""Deterministic demo multimodal provider — no external credentials required."""

from __future__ import annotations

from app.ai.base import AIProvider
from app.ai.schemas import (
    AnalysisEvidenceItem,
    FrameAnalysisInput,
    IncidentAnalysisResult,
)
from app.core.enums import AnalysisSeverity
from app.core.incident_types import SUPPORTED_PPE_ITEMS, ppe_item_label


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
        camera_id: str | None = None,
        demo_scenario: str | None = None,
        demo_ppe_observation: str | None = None,
        required_ppe: list[str] | None = None,
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
                analysis_mode="demo_heuristic",
                human_review_required=True,
            )

        scenario = (demo_scenario or "person_down").strip().lower()
        if scenario in {"ppe", "ppe_compliance", "ppe_noncompliance"}:
            if not required_ppe:
                return IncidentAnalysisResult(
                    incident_detected=False,
                    incident_type="no_incident",
                    summary=(
                        f"Configured PPE demo was selected, but {camera_name or 'this camera'} "
                        f"at {location} has no active PPE requirement. "
                        "No PPE noncompliance is inferred."
                    ),
                    detailed_analysis=(
                        "SafetyLens only evaluates PPE against a typed camera PPE policy. "
                        "Cameras without required PPE items do not produce PPE violations."
                    ),
                    severity=AnalysisSeverity.NONE,
                    confidence=0.0,
                    evidence=[
                        AnalysisEvidenceItem(
                            frame_id=frames[0].frame_code,
                            timestamp_seconds=frames[0].timestamp_seconds,
                            observation=(
                                "No PPE policy is configured for this camera; "
                                "configured demo did not create a PPE incident."
                            ),
                            relevance="context",
                        )
                    ],
                    recommended_actions=[],
                    limitations=[
                        "Configured PPE Demo — camera has no PPE requirement",
                        "No PPE noncompliance inferred without policy",
                    ],
                    inconclusive=False,
                    required_ppe=[],
                    observed_ppe=[],
                    possibly_missing_ppe=[],
                    analysis_mode="configured_demo",
                    human_review_required=False,
                )
            return self._configured_ppe_result(
                frames=frames,
                location=location,
                camera_name=camera_name,
                video_asset_code=video_asset_code,
                demo_ppe_observation=demo_ppe_observation,
                required_ppe=required_ppe or list(SUPPORTED_PPE_ITEMS),
            )

        # Default person-down demonstration path (unchanged heuristics).
        selected = _select_key_frames(frames)
        mid = selected[len(selected) // 2]
        start = selected[0]
        end = selected[-1]

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
                analysis_mode="demo_heuristic",
                human_review_required=True,
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
            analysis_mode="demo_heuristic",
            human_review_required=False,
        )

    def _configured_ppe_result(
        self,
        *,
        frames: list[FrameAnalysisInput],
        location: str,
        camera_name: str | None,
        video_asset_code: str,
        demo_ppe_observation: str | None,
        required_ppe: list[str],
    ) -> IncidentAnalysisResult:
        required = [item for item in required_ppe if item in SUPPORTED_PPE_ITEMS]
        if not required:
            required = list(SUPPORTED_PPE_ITEMS)

        observation = (demo_ppe_observation or "hard_hat_not_visible").strip().lower()
        if observation in {"both", "both_not_visible"}:
            missing = list(required)
        elif observation in {"high_visibility_vest", "high_visibility_vest_not_visible", "vest"}:
            missing = ["high_visibility_vest"] if "high_visibility_vest" in required else list(required[:1])
        else:
            missing = ["hard_hat"] if "hard_hat" in required else list(required[:1])

        observed = [item for item in required if item not in missing]
        selected = _select_key_frames(frames)
        focus = selected[len(selected) // 2]
        missing_labels = ", ".join(ppe_item_label(item) for item in missing)
        evidence = [
            AnalysisEvidenceItem(
                frame_id=focus.frame_code,
                timestamp_seconds=focus.timestamp_seconds,
                observation=(
                    f"At {focus.timestamp_seconds:.1f}s in the PPE-required zone "
                    f"({location}), {missing_labels} "
                    f"{'are' if len(missing) > 1 else 'is'} not visible in the "
                    "selected evidence. This is a configured demo observation, "
                    "not independent pixel detection."
                ),
                relevance="supporting",
            )
        ]
        for frame in selected:
            if frame.frame_code == focus.frame_code:
                continue
            evidence.append(
                AnalysisEvidenceItem(
                    frame_id=frame.frame_code,
                    timestamp_seconds=frame.timestamp_seconds,
                    observation=(
                        f"Context frame at {frame.timestamp_seconds:.1f}s for "
                        f"{camera_name or 'camera'} · {location}."
                    ),
                    relevance="context",
                )
            )
            if len(evidence) >= 3:
                break

        return IncidentAnalysisResult(
            incident_detected=True,
            incident_type="ppe_noncompliance",
            summary=(
                f"Configured PPE demo: {missing_labels} not visible near "
                f"{location} on video {video_asset_code}."
            ),
            detailed_analysis=(
                "This result is a Configured Demo Scenario for hackathon "
                "rehearsal. Demo AI does not inspect pixels to discover missing "
                "PPE. The presenter selected the observation, and SafetyLens "
                "preserves evidence, notifies the operator, retrieves the PPE "
                "procedure, and prepares a draft plan for human verification."
            ),
            severity=AnalysisSeverity.MEDIUM,
            confidence=0.0,
            evidence=evidence,
            recommended_actions=[
                "Request supervisor verification of required PPE",
                "Pause controlled-zone entry until PPE is confirmed",
                "Document the compliance event after human review",
            ],
            limitations=[
                "Configured PPE Demo — not independent multimodal detection",
                "Only hard hat and high-visibility vest are supported in this version",
                "Occlusion or distance can hide PPE even when worn",
                "Human verification is required before corrective actions",
            ],
            inconclusive=False,
            required_ppe=required,
            observed_ppe=observed,
            possibly_missing_ppe=missing,
            analysis_mode="configured_demo",
            human_review_required=True,
        )


def _select_key_frames(frames: list[FrameAnalysisInput]) -> list[FrameAnalysisInput]:
    if len(frames) == 1:
        return frames
    if len(frames) == 2:
        return frames
    mid_index = len(frames) // 2
    return [frames[0], frames[mid_index], frames[-1]]

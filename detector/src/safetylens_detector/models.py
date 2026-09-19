from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Mapping


class DetectorState(str, Enum):
    NO_PERSON = "no_person"
    MONITORING = "monitoring"
    SUSPECTED = "suspected"
    CONFIRMING = "confirming"
    INCIDENT = "incident"
    COOLDOWN = "cooldown"
    LOW_VISIBILITY = "low_visibility"


@dataclass(frozen=True)
class Landmark:
    x: float
    y: float
    visibility: float = 1.0

    def __post_init__(self) -> None:
        if not 0 <= self.x <= 1 or not 0 <= self.y <= 1:
            raise ValueError("Landmark coordinates must be normalized to [0, 1].")
        if not 0 <= self.visibility <= 1:
            raise ValueError("Landmark visibility must be in [0, 1].")


@dataclass(frozen=True)
class PoseObservation:
    timestamp_seconds: float
    track_id: str
    landmarks: Mapping[str, Landmark]
    source_id: str = "unknown-source"
    source_timestamp_seconds: float | None = None
    frame_aspect_ratio: float = 1.0

    def __post_init__(self) -> None:
        if self.timestamp_seconds < 0:
            raise ValueError("timestamp_seconds must be non-negative.")
        if not self.track_id.strip():
            raise ValueError("track_id must not be blank.")
        if self.frame_aspect_ratio <= 0:
            raise ValueError("frame_aspect_ratio must be positive.")


@dataclass(frozen=True)
class PoseMetrics:
    timestamp_seconds: float
    pose_quality: float
    shoulder_center_y: float | None
    torso_angle_degrees_from_vertical: float | None
    bbox_width_height_ratio: float | None
    downward_hip_velocity_body_lengths_per_second: float | None
    mean_landmark_motion_body_lengths_per_second: float | None


@dataclass(frozen=True)
class DetectorConfig:
    minimum_pose_quality: float = 0.60
    maximum_observation_gap_seconds: float = 0.75
    rapid_drop_velocity: float = 0.65
    horizontal_angle_degrees: float = 58.0
    minimum_horizontal_bbox_ratio: float = 1.25
    down_bbox_width_height_ratio: float = 1.35
    minimum_tilt_for_bbox_down_degrees: float = 25.0
    overhead_shoulder_drop_ratio: float = 0.12
    overhead_settled_motion_threshold: float = 0.75
    overhead_hold_seconds: float = 1.20
    recovery_angle_degrees: float = 35.0
    maximum_recovery_bbox_ratio: float = 1.20
    horizontal_hold_seconds: float = 0.50
    down_posture_gap_tolerance_seconds: float = 0.20
    low_motion_threshold: float = 0.18
    low_motion_hold_seconds: float = 1.20
    suspicion_timeout_seconds: float = 2.50
    cooldown_seconds: float = 4.0
    recovery_hold_seconds: float = 0.6
    enable_overhead_displacement: bool = True

    def __post_init__(self) -> None:
        bounded = {
            "minimum_pose_quality": self.minimum_pose_quality,
        }
        for name, value in bounded.items():
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be in [0, 1].")
        positive = {
            "recovery_hold_seconds": self.recovery_hold_seconds,
            "maximum_observation_gap_seconds": self.maximum_observation_gap_seconds,
            "rapid_drop_velocity": self.rapid_drop_velocity,
            "horizontal_angle_degrees": self.horizontal_angle_degrees,
            "minimum_horizontal_bbox_ratio": self.minimum_horizontal_bbox_ratio,
            "down_bbox_width_height_ratio": self.down_bbox_width_height_ratio,
            "minimum_tilt_for_bbox_down_degrees": self.minimum_tilt_for_bbox_down_degrees,
            "overhead_shoulder_drop_ratio": self.overhead_shoulder_drop_ratio,
            "overhead_settled_motion_threshold": self.overhead_settled_motion_threshold,
            "overhead_hold_seconds": self.overhead_hold_seconds,
            "recovery_angle_degrees": self.recovery_angle_degrees,
            "maximum_recovery_bbox_ratio": self.maximum_recovery_bbox_ratio,
            "horizontal_hold_seconds": self.horizontal_hold_seconds,
            "down_posture_gap_tolerance_seconds": self.down_posture_gap_tolerance_seconds,
            "low_motion_threshold": self.low_motion_threshold,
            "low_motion_hold_seconds": self.low_motion_hold_seconds,
            "suspicion_timeout_seconds": self.suspicion_timeout_seconds,
            "cooldown_seconds": self.cooldown_seconds,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name} must be positive.")
        if self.recovery_angle_degrees >= self.horizontal_angle_degrees:
            raise ValueError("Recovery angle must be lower than horizontal angle.")


@dataclass(frozen=True)
class DetectionEvent:
    schema_version: str
    event_id: str
    event_type: str
    source_id: str
    track_id: str
    occurred_at_seconds: float
    source_timestamp_seconds: float | None
    state: DetectorState
    trigger_signals: tuple[str, ...]
    pose_quality: float
    metrics: PoseMetrics
    limitations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["state"] = self.state.value
        payload["trigger_signals"] = list(self.trigger_signals)
        payload["limitations"] = list(self.limitations)
        return payload


@dataclass(frozen=True)
class DetectorResult:
    track_id: str
    previous_state: DetectorState
    state: DetectorState
    metrics: PoseMetrics | None
    event: DetectionEvent | None = None
    reasons: tuple[str, ...] = field(default_factory=tuple)

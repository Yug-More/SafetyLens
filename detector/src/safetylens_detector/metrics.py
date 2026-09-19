from __future__ import annotations

from math import atan2, degrees, hypot
from statistics import fmean

from .models import Landmark, PoseMetrics, PoseObservation

TORSO_NAMES = ("left_shoulder", "right_shoulder", "left_hip", "right_hip")


def _midpoint(left: Landmark, right: Landmark) -> tuple[float, float]:
    return ((left.x + right.x) / 2, (left.y + right.y) / 2)


def _distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return hypot(a[0] - b[0], a[1] - b[1])


def _visible_landmarks(observation: PoseObservation) -> dict[str, Landmark]:
    return {
        name: landmark
        for name, landmark in observation.landmarks.items()
        if landmark.visibility > 0
    }


def derive_pose_metrics(
    current: PoseObservation,
    previous: PoseObservation | None = None,
) -> PoseMetrics:
    """Derive model-independent metrics from normalized pose landmarks."""

    visible = _visible_landmarks(current)
    torso = [current.landmarks.get(name) for name in TORSO_NAMES]
    quality = fmean(item.visibility if item else 0.0 for item in torso)

    angle: float | None = None
    shoulder_center_y: float | None = None
    ratio: float | None = None
    downward_velocity: float | None = None
    mean_motion: float | None = None

    if all(torso):
        left_shoulder, right_shoulder, left_hip, right_hip = torso
        shoulder_center = _midpoint(left_shoulder, right_shoulder)  # type: ignore[arg-type]
        shoulder_center_y = shoulder_center[1]
        hip_center = _midpoint(left_hip, right_hip)  # type: ignore[arg-type]
        torso_length = _distance(shoulder_center, hip_center)
        if torso_length > 1e-6:
            dx = abs(shoulder_center[0] - hip_center[0])
            dy = abs(shoulder_center[1] - hip_center[1])
            angle = degrees(atan2(dx, dy))

            xs = [item.x for item in visible.values()]
            ys = [item.y for item in visible.values()]
            if xs and ys and max(ys) - min(ys) > 1e-6:
                ratio = (max(xs) - min(xs)) / (max(ys) - min(ys))

            if previous is not None:
                elapsed = current.timestamp_seconds - previous.timestamp_seconds
                if elapsed <= 0:
                    raise ValueError("Observation timestamps must strictly increase per track.")
                previous_torso = [previous.landmarks.get(name) for name in TORSO_NAMES]
                if all(previous_torso):
                    previous_hip = _midpoint(previous_torso[2], previous_torso[3])  # type: ignore[arg-type]
                    downward_velocity = (hip_center[1] - previous_hip[1]) / elapsed / torso_length

                common = sorted(set(visible).intersection(previous.landmarks))
                motions = [
                    _distance(
                        (visible[name].x, visible[name].y),
                        (previous.landmarks[name].x, previous.landmarks[name].y),
                    )
                    / elapsed
                    / torso_length
                    for name in common
                    if previous.landmarks[name].visibility > 0
                ]
                if motions:
                    mean_motion = fmean(motions)

    return PoseMetrics(
        timestamp_seconds=current.timestamp_seconds,
        pose_quality=quality,
        shoulder_center_y=shoulder_center_y,
        torso_angle_degrees_from_vertical=angle,
        bbox_width_height_ratio=ratio,
        downward_hip_velocity_body_lengths_per_second=downward_velocity,
        mean_landmark_motion_body_lengths_per_second=mean_motion,
    )

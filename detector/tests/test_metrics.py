from __future__ import annotations

import unittest
from dataclasses import replace

from safetylens_detector import Landmark, PoseObservation, derive_pose_metrics


def observation(timestamp: float, *, horizontal: bool, hip_y: float) -> PoseObservation:
    if horizontal:
        points = {
            "left_shoulder": (0.30, hip_y),
            "right_shoulder": (0.30, hip_y + 0.06),
            "left_hip": (0.65, hip_y),
            "right_hip": (0.65, hip_y + 0.06),
        }
    else:
        points = {
            "left_shoulder": (0.45, hip_y - 0.30),
            "right_shoulder": (0.55, hip_y - 0.30),
            "left_hip": (0.46, hip_y),
            "right_hip": (0.54, hip_y),
        }
    return PoseObservation(
        timestamp_seconds=timestamp,
        track_id="person-1",
        landmarks={name: Landmark(x, y, 0.9) for name, (x, y) in points.items()},
    )


class PoseMetricTests(unittest.TestCase):
    def test_geometry_is_invariant_to_frame_aspect_ratio(self) -> None:
        square = observation(0.0, horizontal=True, hip_y=0.55)
        wide = replace(square, frame_aspect_ratio=2.0, landmarks={
            name: Landmark(point.x / 2, point.y, point.visibility)
            for name, point in square.landmarks.items()
        })
        a, b = derive_pose_metrics(square), derive_pose_metrics(wide)
        self.assertAlmostEqual(a.bbox_width_height_ratio, b.bbox_width_height_ratio)
        self.assertAlmostEqual(a.torso_angle_degrees_from_vertical, b.torso_angle_degrees_from_vertical)

    def test_unreliable_ankle_and_outstretched_hand_do_not_widen_body(self) -> None:
        original = observation(0.0, horizontal=False, hip_y=0.55)
        noisy = replace(original, landmarks={
            **original.landmarks,
            "left_ankle": Landmark(0.0, 0.9, 0.01),
            "right_wrist": Landmark(1.0, 0.4, 0.99),
        })
        self.assertAlmostEqual(
            derive_pose_metrics(original).bbox_width_height_ratio,
            derive_pose_metrics(noisy).bbox_width_height_ratio,
        )

    def test_torso_angle_distinguishes_upright_and_horizontal(self) -> None:
        upright = derive_pose_metrics(observation(0.0, horizontal=False, hip_y=0.55))
        horizontal = derive_pose_metrics(observation(0.0, horizontal=True, hip_y=0.65))
        self.assertIsNotNone(upright.torso_angle_degrees_from_vertical)
        self.assertIsNotNone(horizontal.torso_angle_degrees_from_vertical)
        self.assertLess(upright.torso_angle_degrees_from_vertical, 5)  # type: ignore[arg-type]
        self.assertGreater(horizontal.torso_angle_degrees_from_vertical, 85)  # type: ignore[arg-type]

    def test_downward_velocity_uses_elapsed_time_and_body_scale(self) -> None:
        previous = observation(0.0, horizontal=False, hip_y=0.40)
        current = observation(0.2, horizontal=False, hip_y=0.55)
        metrics = derive_pose_metrics(current, previous)
        self.assertIsNotNone(metrics.downward_hip_velocity_body_lengths_per_second)
        self.assertGreater(metrics.downward_hip_velocity_body_lengths_per_second or 0, 2)

    def test_rejects_equal_timestamps_when_comparing_motion(self) -> None:
        previous = observation(1.0, horizontal=False, hip_y=0.40)
        current = observation(1.0, horizontal=False, hip_y=0.50)
        with self.assertRaisesRegex(ValueError, "strictly increase"):
            derive_pose_metrics(current, previous)


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import unittest
from dataclasses import dataclass

from safetylens_detector.mediapipe_provider import landmarks_to_observation


@dataclass
class RawLandmark:
    x: float
    y: float
    visibility: float | None = None
    presence: float | None = None


class MediaPipeConversionTests(unittest.TestCase):
    def test_converts_all_landmarks_and_combines_quality_scores(self) -> None:
        raw = [RawLandmark(0.5, 0.4, 0.9, 0.8) for _ in range(33)]
        observation = landmarks_to_observation(
            raw,
            timestamp_seconds=1.25,
            source_id="camera-1",
        )
        self.assertEqual(len(observation.landmarks), 33)
        self.assertEqual(observation.landmarks["left_shoulder"].visibility, 0.8)
        self.assertEqual(observation.landmarks["right_ankle"].x, 0.5)
        self.assertEqual(observation.source_timestamp_seconds, 1.25)

    def test_clamps_model_coordinates_to_observation_contract(self) -> None:
        raw = [RawLandmark(-0.2, 1.3, 2.0, -0.1) for _ in range(33)]
        observation = landmarks_to_observation(
            raw,
            timestamp_seconds=0.0,
            source_id="camera-1",
        )
        landmark = observation.landmarks["nose"]
        self.assertEqual((landmark.x, landmark.y, landmark.visibility), (0.0, 1.0, 0.0))

    def test_rejects_wrong_landmark_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "Expected 33"):
            landmarks_to_observation(
                [RawLandmark(0.5, 0.5)],
                timestamp_seconds=0.0,
                source_id="camera-1",
            )


if __name__ == "__main__":
    unittest.main()

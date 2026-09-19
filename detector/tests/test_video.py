from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from safetylens_detector.models import DetectorState, Landmark, PoseObservation
from safetylens_detector.video import analyze_video


class FakeCapture:
    def __init__(self, frame_count: int = 12, fps: float = 10.0) -> None:
        self.frame_count = frame_count
        self.fps = fps
        self.index = 0

    def isOpened(self) -> bool:
        return True

    def get(self, prop: int) -> float:
        return self.fps if prop == 5 else float(self.frame_count)

    def read(self) -> tuple[bool, object | None]:
        if self.index >= self.frame_count:
            return False, None
        self.index += 1
        return True, object()

    def release(self) -> None:
        pass


def observation(timestamp: float) -> PoseObservation:
    return PoseObservation(
        timestamp_seconds=timestamp,
        source_timestamp_seconds=timestamp,
        source_id="test",
        track_id="person-1",
        landmarks={
            "left_shoulder": Landmark(0.45, 0.2, 0.99),
            "right_shoulder": Landmark(0.55, 0.2, 0.99),
            "left_hip": Landmark(0.46, 0.5, 0.99),
            "right_hip": Landmark(0.54, 0.5, 0.99),
        },
    )


class VideoAnalysisTests(unittest.TestCase):
    @patch("safetylens_detector.video.MediaPipePoseProvider")
    def test_short_pose_dropout_does_not_mark_track_missing(self, provider_type: MagicMock) -> None:
        provider = provider_type.return_value.__enter__.return_value
        provider.detect.side_effect = [
            observation(0.0),
            observation(0.1),
            None,
            None,
            observation(0.4),
        ] + [observation(index / 10) for index in range(5, 12)]

        fake_cv2 = MagicMock()
        fake_cv2.CAP_PROP_FPS = 5
        fake_cv2.CAP_PROP_FRAME_COUNT = 7
        fake_cv2.VideoCapture.return_value = FakeCapture()
        with patch.dict("sys.modules", {"cv2": fake_cv2}):
            analysis = analyze_video("test.mov", "model.task", sample_fps=10)

        self.assertEqual(analysis.missing_poses, 2)
        self.assertFalse(
            any(transition.state == DetectorState.NO_PERSON.value for transition in analysis.transitions)
        )

    @patch("safetylens_detector.video.MediaPipePoseProvider")
    def test_sustained_pose_loss_marks_track_missing(self, provider_type: MagicMock) -> None:
        provider = provider_type.return_value.__enter__.return_value
        provider.detect.side_effect = [observation(0.0)] + [None] * 11

        fake_cv2 = MagicMock()
        fake_cv2.CAP_PROP_FPS = 5
        fake_cv2.CAP_PROP_FRAME_COUNT = 7
        fake_cv2.VideoCapture.return_value = FakeCapture()
        with patch.dict("sys.modules", {"cv2": fake_cv2}):
            analysis = analyze_video("test.mov", "model.task", sample_fps=10)

        self.assertEqual(analysis.missing_poses, 11)
        self.assertTrue(
            any(transition.state == DetectorState.NO_PERSON.value for transition in analysis.transitions)
        )


if __name__ == "__main__":
    unittest.main()

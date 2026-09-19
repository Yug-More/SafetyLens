from __future__ import annotations

import unittest

from safetylens_detector.live import (
    frame_has_visible_signal,
    parse_capture_source,
    pose_is_fully_framed,
    state_presentation,
)
from safetylens_detector.models import DetectorState, Landmark, PoseObservation


class FakeFrame:
    size = 1

    def __init__(self, peak: float) -> None:
        self.peak = peak

    def max(self) -> float:
        return self.peak


class LiveSourceTests(unittest.TestCase):
    def test_camera_index_is_integer(self) -> None:
        self.assertEqual(parse_capture_source(" 2 "), 2)

    def test_stream_url_is_preserved(self) -> None:
        url = "http://192.168.1.25:8080/video"
        self.assertEqual(parse_capture_source(url), url)

    def test_blank_source_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            parse_capture_source("  ")

    def test_black_virtual_camera_frame_has_no_signal(self) -> None:
        self.assertFalse(frame_has_visible_signal(FakeFrame(0)))

    def test_visible_virtual_camera_frame_has_signal(self) -> None:
        self.assertTrue(frame_has_visible_signal(FakeFrame(9)))


class LivePresentationTests(unittest.TestCase):
    def make_observation(self, *, hidden_landmark: str | None = None) -> PoseObservation:
        required_names = (
            "nose",
            "left_shoulder",
            "right_shoulder",
            "left_hip",
            "right_hip",
            "left_knee",
            "right_knee",
            "left_ankle",
            "right_ankle",
        )
        return PoseObservation(
            timestamp_seconds=0.0,
            track_id="person-1",
            landmarks={
                name: Landmark(
                    x=0.5,
                    y=0.5,
                    visibility=0.1 if name == hidden_landmark else 0.9,
                )
                for name in required_names
            },
        )

    def test_full_body_view_is_ready_to_arm(self) -> None:
        self.assertTrue(pose_is_fully_framed(self.make_observation()))

    def test_cropped_ankle_view_does_not_arm(self) -> None:
        observation = self.make_observation(hidden_landmark="left_ankle")
        self.assertFalse(pose_is_fully_framed(observation))

    def test_missing_person_does_not_arm(self) -> None:
        self.assertFalse(pose_is_fully_framed(None))

    def test_internal_state_names_are_hidden_from_demo_labels(self) -> None:
        cooldown = " ".join(state_presentation(DetectorState.COOLDOWN)).lower()
        low_visibility = " ".join(
            state_presentation(DetectorState.LOW_VISIBILITY)
        ).lower()
        self.assertNotIn("cooldown", cooldown)
        self.assertNotIn("low_visibility", low_visibility)


if __name__ == "__main__":
    unittest.main()

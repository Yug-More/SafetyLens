from __future__ import annotations

import json
import unittest

from safetylens_detector import (
    DetectorConfig,
    DetectorEngine,
    DetectorState,
    Landmark,
    PoseObservation,
)


def pose(
    timestamp: float,
    *,
    track_id: str = "person-1",
    horizontal: bool = False,
    center_y: float = 0.45,
    visibility: float = 0.99,
) -> PoseObservation:
    if horizontal:
        points = {
            "left_shoulder": (0.35, center_y),
            "right_shoulder": (0.35, center_y + 0.05),
            "left_hip": (0.65, center_y),
            "right_hip": (0.65, center_y + 0.05),
            "left_knee": (0.75, center_y + 0.02),
            "right_knee": (0.75, center_y + 0.07),
        }
    else:
        points = {
            "left_shoulder": (0.45, center_y - 0.20),
            "right_shoulder": (0.55, center_y - 0.20),
            "left_hip": (0.46, center_y + 0.10),
            "right_hip": (0.54, center_y + 0.10),
            "left_knee": (0.46, center_y + 0.28),
            "right_knee": (0.54, center_y + 0.28),
        }
    return PoseObservation(
        timestamp_seconds=timestamp,
        source_timestamp_seconds=timestamp,
        source_id="test-camera",
        track_id=track_id,
        landmarks={name: Landmark(x, y, visibility) for name, (x, y) in points.items()},
    )


class DetectorEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = DetectorEngine(
            DetectorConfig(
                horizontal_hold_seconds=0.4,
                low_motion_hold_seconds=0.8,
                cooldown_seconds=1.0,
            )
        )

    def test_standing_does_not_trigger(self) -> None:
        results = [self.engine.process(pose(index * 0.2)) for index in range(10)]
        self.assertTrue(all(result.event is None for result in results))
        self.assertEqual(results[-1].state, DetectorState.MONITORING)

    def test_clear_fall_emits_one_event(self) -> None:
        sequence = [
            pose(0.0, center_y=0.35),
            pose(0.2, center_y=0.40),
            pose(0.4, horizontal=True, center_y=0.72),
            pose(0.6, horizontal=True, center_y=0.72),
            pose(0.8, horizontal=True, center_y=0.72),
            pose(1.0, horizontal=True, center_y=0.72),
            pose(1.2, horizontal=True, center_y=0.72),
            pose(1.4, horizontal=True, center_y=0.72),
            pose(1.6, horizontal=True, center_y=0.72),
        ]
        results = [self.engine.process(item) for item in sequence]
        events = [result.event for result in results if result.event]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "possible_person_down")
        self.assertEqual(events[0].state, DetectorState.INCIDENT)
        self.assertIn("horizontal_persistence", events[0].trigger_signals)
        self.assertIn("rapid_drop", events[0].trigger_signals)
        json.dumps(events[0].to_dict())

    def test_brief_horizontal_pose_recovers_without_event(self) -> None:
        sequence = [
            pose(0.0),
            pose(0.2, horizontal=True, center_y=0.60),
            pose(0.4, horizontal=True, center_y=0.60),
            pose(0.6),
            pose(0.8),
        ]
        results = [self.engine.process(item) for item in sequence]
        self.assertTrue(all(result.event is None for result in results))
        self.assertEqual(results[-1].state, DetectorState.MONITORING)

    def test_low_visibility_does_not_trigger(self) -> None:
        result = self.engine.process(pose(0.0, horizontal=True, visibility=0.2))
        self.assertEqual(result.state, DetectorState.LOW_VISIBILITY)
        self.assertIsNone(result.event)

    def test_requires_recovery_before_rearming(self) -> None:
        times = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
        frames = [pose(times[0])] + [pose(t, horizontal=True, center_y=0.70) for t in times[1:]]
        results = [self.engine.process(item) for item in frames]
        self.assertEqual(sum(result.event is not None for result in results), 1)
        for t in [1.6, 2.0, 2.6, 3.0]:
            result = self.engine.process(pose(t, horizontal=True, center_y=0.70))
            self.assertIsNone(result.event)
        self.assertEqual(result.state, DetectorState.COOLDOWN)
        recovered = self.engine.process(pose(3.2))
        self.assertEqual(recovered.state, DetectorState.MONITORING)

    def test_tracks_have_independent_state(self) -> None:
        self.engine.process(pose(0.0, track_id="a"))
        suspected = self.engine.process(pose(0.2, track_id="a", horizontal=True, center_y=0.7))
        normal = self.engine.process(pose(0.0, track_id="b"))
        self.assertEqual(suspected.state, DetectorState.SUSPECTED)
        self.assertEqual(normal.state, DetectorState.MONITORING)

    def test_confirmation_uses_time_at_different_frame_rates(self) -> None:
        for step in (0.1, 0.25):
            with self.subTest(step=step):
                engine = DetectorEngine(
                    DetectorConfig(
                        horizontal_hold_seconds=0.4,
                        low_motion_hold_seconds=0.8,
                    )
                )
                engine.process(pose(0.0))
                events = []
                timestamp = step
                while timestamp <= 2.25:
                    result = engine.process(pose(timestamp, horizontal=True, center_y=0.70))
                    if result.event:
                        events.append(result.event)
                    timestamp += step
                self.assertEqual(len(events), 1)

    def test_rejects_non_increasing_timestamps(self) -> None:
        self.engine.process(pose(1.0))
        with self.assertRaisesRegex(ValueError, "strictly increase"):
            self.engine.process(pose(1.0))

    def test_missing_track_clears_history(self) -> None:
        self.engine.process(pose(0.0))
        result = self.engine.mark_missing("person-1")
        self.assertEqual(result.state, DetectorState.NO_PERSON)
        resumed = self.engine.process(pose(5.0))
        self.assertEqual(resumed.state, DetectorState.MONITORING)

    def test_tracking_loss_does_not_rearm_after_incident(self) -> None:
        frames = [pose(0.0)] + [
            pose(t, horizontal=True, center_y=0.70)
            for t in [0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4]
        ]
        results = [self.engine.process(item) for item in frames]
        self.assertEqual(sum(result.event is not None for result in results), 1)
        self.engine.mark_missing("person-1")

        reappeared = [
            self.engine.process(pose(t, horizontal=True, center_y=0.70))
            for t in [3.0, 3.2, 3.4, 3.6, 3.8]
        ]
        self.assertTrue(all(result.event is None for result in reappeared))
        self.assertEqual(reappeared[-1].state, DetectorState.COOLDOWN)

        recovered = self.engine.process(pose(4.0))
        self.assertEqual(recovered.state, DetectorState.MONITORING)


if __name__ == "__main__":
    unittest.main()

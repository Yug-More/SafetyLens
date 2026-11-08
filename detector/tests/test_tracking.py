import unittest
from dataclasses import replace
from safetylens_detector.tracking import PoseTracker
from safetylens_detector.models import Landmark
from test_detector import pose


def shifted(t, x):
    observation = pose(t)
    return replace(
        observation,
        landmarks={
            k: Landmark(p.x + x, p.y, p.visibility)
            for k, p in observation.landmarks.items()
        },
    )


class PoseTrackingTests(unittest.TestCase):
    def test_order_changes_do_not_exchange_temporal_identities(self):
        tracker = PoseTracker()
        first, _, _ = tracker.update(0, [shifted(0, -0.25), shifted(0, 0.25)])
        second, _, _ = tracker.update(0.1, [shifted(0.1, 0.24), shifted(0.1, -0.24)])
        self.assertEqual(
            [x.track_id for x in second], [first[1].track_id, first[0].track_id]
        )

    def test_ambiguous_crossing_does_not_reuse_either_identity(self):
        tracker = PoseTracker()
        first, _, _ = tracker.update(0, [shifted(0, -0.05), shifted(0, 0.05)])
        second, _, ambiguous = tracker.update(0.1, [shifted(0.1, 0)])
        self.assertEqual(ambiguous, 1)
        self.assertNotIn(second[0].track_id, [x.track_id for x in first])

    def test_expired_track_cannot_bridge_another_persons_motion(self):
        tracker = PoseTracker()
        first, _, _ = tracker.update(0, [pose(0)])
        second, expired, _ = tracker.update(1, [pose(1)])
        self.assertEqual(expired, [first[0].track_id])
        self.assertNotEqual(first[0].track_id, second[0].track_id)
        with self.assertRaises(ValueError):
            tracker.update(1, [])

        for index in range(1, 1000):
            tracker.update(
                1 + index * 0.0001,
                [shifted(1 + index * 0.0001, -0.05), shifted(1 + index * 0.0001, 0.05)],
            )
        self.assertLessEqual(len(tracker.tracks), 64)

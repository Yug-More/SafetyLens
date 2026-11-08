import json
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock
from safetylens_detector.delivery import EventOutbox
from safetylens_detector.ppe import Box, associate_ppe, PpeTemporalMonitor
from safetylens_detector.enhanced import EnhancedDetectorEngine, SafetyState
from safetylens_detector.evaluation import wilson


class DeliveryTests(unittest.TestCase):
    def test_durable_retry_acknowledgement_and_deduplication(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clip = root / "source.mp4"
            clip.write_bytes(b"not decoded in transport unit test")
            outbox = EventOutbox(root / "outbox")
            event = {"event_id": str(uuid4()), "schema_version": "1.0"}
            outbox.enqueue(
                event,
                clip,
                camera_id="cam-03",
                location="Dock",
                clip_event_offset_seconds=1,
            )
            outbox.enqueue(
                event,
                clip,
                camera_id="cam-03",
                location="Dock",
                clip_event_offset_seconds=1,
            )
            client = Mock()
            client.post.return_value = Mock(status_code=503)
            self.assertFalse(
                outbox.flush_once(
                    "http://localhost:8000", "secret", client=client, now=0
                )
            )
            reopened = EventOutbox(root / "outbox")
            with reopened.connect() as db:
                self.assertEqual(
                    db.execute("SELECT count(*) FROM deliveries").fetchone()[0], 1
                )
            client.post.return_value = Mock(
                status_code=202,
                json=lambda: {
                    "data": {
                        "event_id": event["event_id"],
                        "asset_code": "VID-1",
                        "status": "processing",
                    }
                },
            )
            self.assertTrue(
                reopened.flush_once(
                    "http://localhost:8000", "secret", client=client, now=100
                )
            )
            self.assertFalse(
                reopened.flush_once(
                    "http://localhost:8000", "secret", client=client, now=200
                )
            )
            self.assertEqual(reopened.prune(acknowledged_before=300), 1)

    def test_bounded_queue_and_permanent_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            clip = root / "clip"
            clip.write_bytes(b"x" * 10)
            outbox = EventOutbox(root / "outbox", maximum_events=1)
            event = {"event_id": str(uuid4())}
            outbox.enqueue(
                event,
                clip,
                camera_id="cam",
                location="Dock",
                clip_event_offset_seconds=0,
            )
            with self.assertRaises(BufferError):
                outbox.enqueue(
                    {"event_id": str(uuid4())},
                    clip,
                    camera_id="cam",
                    location="Dock",
                    clip_event_offset_seconds=0,
                )
            client = Mock()
            client.post.return_value = Mock(status_code=403)
            self.assertFalse(
                outbox.flush_once(
                    "http://localhost:8000", "token", client=client, now=0
                )
            )
            with outbox.connect() as db:
                self.assertEqual(
                    db.execute("SELECT status FROM deliveries").fetchone()[0], "blocked"
                )
            with self.assertRaises(ValueError):
                outbox.flush_once("http://public.example", "token", client=client)


class PpeTests(unittest.TestCase):
    def test_hat_is_not_shared_between_people(self):
        boxes = [
            Box("person", 0.9, (0, 0, 100, 200)),
            Box("person", 0.9, (200, 0, 300, 200)),
            Box("hard_hat", 0.95, (20, 0, 70, 40)),
        ]
        rows = associate_ppe(boxes, ["hard_hat"])
        self.assertEqual(rows[0]["status"], "observed_compliant")
        self.assertEqual(rows[1]["status"], "inconclusive")
        self.assertEqual(rows[1]["possibly_missing"], ["hard_hat"])

    def test_crowded_ambiguous_assignment_is_inconclusive(self):
        boxes = [
            Box("person", 0.9, (0, 0, 100, 200)),
            Box("person", 0.9, (10, 0, 110, 200)),
            Box("hard_hat", 0.9, (30, 0, 70, 40)),
        ]
        rows = associate_ppe(boxes, ["hard_hat"])
        self.assertTrue(all(x["status"] == "inconclusive" for x in rows))
        self.assertTrue(all(x["association_ambiguous"] for x in rows))

    def test_temporal_missing_ppe_is_review_not_certainty(self):
        row = associate_ppe([Box("person", 0.9, (0, 0, 100, 200))], ["hard_hat"])
        monitor = PpeTemporalMonitor(hold_seconds=1, max_gap_seconds=0.75)
        self.assertFalse(monitor.process(0, row)[0]["review_required"])
        self.assertFalse(monitor.process(0.5, row)[0]["review_required"])
        self.assertTrue(monitor.process(1.1, row)[0]["review_required"])
        self.assertFalse(monitor.process(3, row)[0]["review_required"])


class EnhancedTests(unittest.TestCase):
    def test_missing_pose_is_inconclusive(self):
        self.assertEqual(
            EnhancedDetectorEngine().mark_missing("person-1").safety_state,
            SafetyState.INCONCLUSIVE,
        )

    def test_statistical_interval_handles_small_samples(self):
        lo, hi = wilson(1, 1)
        self.assertLess(lo, 0.3)
        self.assertAlmostEqual(hi, 1)
        self.assertIsNone(wilson(0, 0))


class BenchmarkMathTests(unittest.TestCase):
    def test_ap_matches_ranking_and_missing_annotations(self):
        from safetylens_detector.ppe_evaluation import average_precision

        self.assertEqual(average_precision([(0.9, True), (0.8, True)], 2), 1)
        self.assertEqual(average_precision([], 1), 0)
        self.assertIsNone(average_precision([], 0))
        self.assertLess(average_precision([(0.9, False), (0.8, True)], 1), 1)

    def test_already_down_is_not_an_observed_fall(self):
        from test_detector import pose

        engine = EnhancedDetectorEngine()
        results = [
            engine.process(pose(index * 0.2, horizontal=True, center_y=0.7))
            for index in range(15)
        ]
        events = [result.event for result in results if result.event]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "prolonged_person_down")
        self.assertTrue(
            all(result.safety_state != SafetyState.FALL_DETECTED for result in results)
        )


if __name__ == "__main__":
    unittest.main()

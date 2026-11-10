import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from safetylens_detector.temporal import (
    CausalFeatures,
    FEATURE_NAMES,
    FEATURE_VERSION,
    TemporalModel,
    TemporalDetectorEngine,
)
from safetylens_detector.compliance import assess_people, evaluate_associations
from safetylens_detector.ppe import Box, PpeTemporalMonitor, associate_ppe
from test_video import observation


def checkpoint():
    n = len(FEATURE_NAMES)
    return dict(
        feature_version=FEATURE_VERSION,
        feature_names=list(FEATURE_NAMES),
        mean=[0] * n,
        scale=[1] * n,
        w1=[[0] for _ in range(n)],
        b1=[0],
        w2=[0],
        b2=5,
        threshold=0.9,
        linear=True,
    )


class TemporalResearchTests(unittest.TestCase):
    def test_causal_prefix_and_gap_reset(self):
        import numpy as np

        a = CausalFeatures()
        b = CausalFeatures()
        for t in [0, 0.1, 0.2, 0.5]:
            x, _ = a.process(observation(t))
            y, _ = b.process(observation(t))
            np.testing.assert_array_equal(x, y)
        self.assertGreater(x[-2], 0)
        x, _ = a.process(observation(2))
        self.assertEqual(x[-2], 0)
        with self.assertRaises(ValueError):
            a.process(observation(1))

    def test_checkpoint_integrity_shapes_and_nonfinite_rejection(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "model.json"
            p.write_text(json.dumps(checkpoint()))
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            model = TemporalModel.load(p, expected_sha256=digest)
            self.assertGreater(model.score([0] * len(FEATURE_NAMES)), 0.9)
            with self.assertRaises(ValueError):
                TemporalModel.load(p, expected_sha256="0" * 64)
        c = checkpoint()
        c["scale"][0] = float("nan")
        with self.assertRaises(ValueError):
            TemporalModel(c)

    def test_event_debounce_independent_tracks_and_missing_gap(self):
        from dataclasses import replace

        engine = TemporalDetectorEngine(TemporalModel(checkpoint()))
        events = []
        for i in range(10):
            result = engine.process(observation(i / 10))
            if result.event:
                events.append(result.event)
        self.assertEqual(len(events), 1)
        self.assertIn("score_is_not_calibrated_fall_probability", events[0].limitations)
        self.assertEqual(
            engine.process(replace(observation(1), track_id="second")).state.value,
            "confirming",
        )
        engine.mark_missing("person-1")
        self.assertTrue(engine.tracks["person-1"]["decision"].latched)
        engine.forget_track("person-1")
        self.assertNotIn("person-1", engine.tracks)


class PpeResearchTests(unittest.TestCase):
    def test_association_does_not_certify_glasses_or_invisible_footwear(self):
        boxes = [
            Box("person", 0.9, (0, 0, 100, 200)),
            Box("person", 0.9, (200, 0, 300, 200)),
            Box("ordinary_eyewear", 0.9, (30, 20, 60, 35)),
        ]
        rows = assess_people(boxes, ["safety_goggles", "protective_footwear"])
        first = rows[0]["requirements"]
        second = rows[1]["requirements"]
        self.assertIsNotNone(first["safety_goggles"]["observed_object"])
        self.assertIsNone(second["safety_goggles"]["observed_object"])
        self.assertEqual(first["safety_goggles"]["state"], "unknown")
        self.assertEqual(first["protective_footwear"]["state"], "unknown")
        self.assertEqual(first["hard_hat"]["state"], "not_required")
        self.assertIsNone(evaluate_associations({}, None)["accuracy"])

    def test_ambiguous_equipment_never_shared_as_compliance(self):
        rows = assess_people(
            [
                Box("person", 0.9, (0, 0, 100, 200)),
                Box("person", 0.9, (10, 0, 110, 200)),
                Box("hard_hat", 0.9, (45, 10, 65, 30)),
            ],
            ["hard_hat"],
        )
        self.assertTrue(
            all(r["requirements"]["hard_hat"]["association_ambiguous"] for r in rows)
        )
        self.assertTrue(
            all(r["requirements"]["hard_hat"]["observed_object"] is None for r in rows)
        )

    def test_temporal_unknown_stays_unknown_even_when_review_is_due(self):
        person = associate_ppe([Box("person", 0.9, (0, 0, 100, 200))], ["hard_hat"])
        monitor = PpeTemporalMonitor(hold_seconds=0.5)
        monitor.process(0, person)
        result = monitor.process(0.6, person)[0]
        self.assertTrue(result["review_required"])
        self.assertEqual(result["status"], "inconclusive")


class StreamBackpressureTests(unittest.TestCase):
    def test_latest_frame_drops_stale_frames_and_release_ends_consumer(self):
        import threading
        from safetylens_detector.stream import LatestFrameCapture

        class Capture:
            def __init__(self):
                self.i = 0
                self.ended = threading.Event()

            def read(self):
                self.i += 1
                if self.i > 20:
                    self.ended.set()
                    return False, None
                return True, self.i

            def release(self):
                pass

        raw = Capture()
        capture = LatestFrameCapture(raw, wait_seconds=0.05)
        self.assertTrue(raw.ended.wait(1))
        capture.reader.join(timeout=1)
        ok, frame = capture.read()
        self.assertTrue(ok)
        self.assertEqual(frame, 20)
        self.assertEqual(capture.dropped_frames, 19)
        self.assertEqual(capture.read(), (False, None))
        capture.release()

    def test_stalled_stream_does_not_block_consumer_indefinitely(self):
        import threading, time
        from safetylens_detector.stream import LatestFrameCapture

        class Capture:
            def __init__(self):
                self.resume = threading.Event()

            def read(self):
                self.resume.wait(1)
                return False, None

            def release(self):
                pass

        raw = Capture()
        capture = LatestFrameCapture(raw, wait_seconds=0.02)
        start = time.monotonic()
        self.assertEqual(capture.read(), (False, None))
        self.assertLess(time.monotonic() - start, 0.5)
        raw.resume.set()
        capture.release()


class TemporalDecisionParityTests(unittest.TestCase):
    def test_pose_loss_never_counts_as_upright_recovery_or_rearms_alert(self):
        from safetylens_detector.temporal import TemporalDecision
        from safetylens_detector.models import PoseMetrics

        metrics = PoseMetrics(0, 1, 0.2, 10, 0.5, 0, 0)
        decision = TemporalDecision(0.9)
        decision.update(0, 0.99, metrics, 0.5)
        self.assertTrue(decision.update(0.1, 0.99, metrics, 0.5)[1])
        decision.update(0.2, 0.99, metrics, 0.5)
        decision.update(0.3, None, None, 0)
        decision.update(2, 0.99, metrics, 0.5)
        self.assertTrue(decision.latched)
        self.assertFalse(decision.update(2.1, 0.99, metrics, 0.5)[1])
        decision.update(2.5, 0.1, metrics, 0.5)
        decision.update(2.9, 0.1, metrics, 0.5)
        decision.update(3.1, 0.1, metrics, 0.5)
        self.assertFalse(decision.latched)

    def test_evaluator_and_runtime_share_identical_decisions_through_dropouts(self):
        import importlib.util
        from dataclasses import asdict

        path = Path(__file__).resolve().parents[2] / "scripts/temporal_experiment.py"
        spec = importlib.util.spec_from_file_location("temporal_evaluation", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        model = TemporalModel(checkpoint())
        engine = TemporalDetectorEngine(model)
        extract = CausalFeatures()
        rows = []
        times = []
        for t in [
            0,
            0.1,
            0.2,
            0.3,
            0.4,
            0.5,
            0.6,
            0.7,
            0.8,
            1.2,
            1.3,
            1.4,
            1.5,
            1.6,
            2.7,
            2.8,
            3.0,
            3.1,
        ]:
            if t in [1.2, 1.3, 1.4]:
                result = engine.mark_missing("person-1", timestamp_seconds=t)
                rows.append({"t": t, "features": None, "metrics": None})
            else:
                obs = observation(t)
                f, m = extract.process(obs)
                result = engine.process(obs)
                rows.append({"t": t, "features": f.tolist(), "metrics": asdict(m)})
            if result.event:
                times.append(t)
        cached, _ = module.events({"rows": rows}, model)
        self.assertEqual(times, cached)


class AssociationLabelIntegrityTests(unittest.TestCase):
    def test_unknown_or_duplicate_ground_truth_cannot_inflate_accuracy(self):
        with self.assertRaises(ValueError):
            evaluate_associations({}, [{"equipment_id": "helmet", "person_id": None}])
        with self.assertRaises(ValueError):
            evaluate_associations(
                {},
                [
                    {"equipment_id": "helmet", "person_id": "worker"},
                    {"equipment_id": "helmet", "person_id": "worker"},
                ],
            )
        self.assertEqual(
            evaluate_associations(
                {"helmet": "worker"},
                [{"equipment_id": "helmet", "person_id": "worker"}],
            )["accuracy"],
            1,
        )

from __future__ import annotations

import unittest

from safetylens_detector import EvidenceWindowBuffer


class EvidenceWindowBufferTests(unittest.TestCase):
    def test_collects_pre_and_post_event_frames(self) -> None:
        buffer = EvidenceWindowBuffer[str](pre_event_seconds=2.0)
        for timestamp in (0.0, 1.0, 2.0, 3.0):
            buffer.add(timestamp, f"frame-{timestamp}")

        capture = buffer.start_capture(
            event_id="event-1",
            event_timestamp_seconds=3.0,
            post_event_seconds=2.0,
        )
        self.assertEqual([sample.timestamp_seconds for sample in capture.frames], [1.0, 2.0, 3.0])

        buffer.add(4.0, "frame-4")
        self.assertIsNone(buffer.pop_completed())
        buffer.add(5.0, "frame-5")
        completed = buffer.pop_completed()
        self.assertIsNotNone(completed)
        self.assertEqual(
            [sample.timestamp_seconds for sample in completed.frames],  # type: ignore[union-attr]
            [1.0, 2.0, 3.0, 4.0, 5.0],
        )

    def test_rolling_window_is_bounded_by_time_and_count(self) -> None:
        buffer = EvidenceWindowBuffer[int](pre_event_seconds=1.0, maximum_frames=3)
        for index, timestamp in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
            buffer.add(timestamp, index)
        self.assertEqual(buffer.rolling_frame_count, 3)
        capture = buffer.start_capture(
            event_id="bounded",
            event_timestamp_seconds=1.0,
            post_event_seconds=1.0,
        )
        self.assertEqual([sample.timestamp_seconds for sample in capture.frames], [0.5, 0.75, 1.0])

    def test_rejects_non_increasing_timestamps(self) -> None:
        buffer = EvidenceWindowBuffer[str](pre_event_seconds=2.0)
        buffer.add(1.0, "first")
        with self.assertRaisesRegex(ValueError, "strictly increase"):
            buffer.add(1.0, "duplicate")

    def test_rejects_duplicate_event_id(self) -> None:
        buffer = EvidenceWindowBuffer[str](pre_event_seconds=2.0)
        buffer.add(1.0, "first")
        buffer.start_capture(event_id="event-1", event_timestamp_seconds=1.0, post_event_seconds=1.0)
        with self.assertRaisesRegex(ValueError, "already exists"):
            buffer.start_capture(event_id="event-1", event_timestamp_seconds=1.0, post_event_seconds=1.0)

    def test_overlapping_captures_finish_independently(self) -> None:
        buffer = EvidenceWindowBuffer[str](pre_event_seconds=1.0)
        buffer.add(0.0, "zero")
        buffer.add(1.0, "one")
        buffer.start_capture(event_id="early", event_timestamp_seconds=1.0, post_event_seconds=1.0)
        buffer.add(1.5, "one-half")
        buffer.start_capture(event_id="late", event_timestamp_seconds=1.5, post_event_seconds=1.0)
        buffer.add(2.0, "two")
        early = buffer.pop_completed()
        self.assertEqual(early.event_id, "early")  # type: ignore[union-attr]
        self.assertEqual(buffer.active_capture_count, 1)
        buffer.add(2.5, "two-half")
        late = buffer.pop_completed()
        self.assertEqual(late.event_id, "late")  # type: ignore[union-attr]
        self.assertEqual(buffer.active_capture_count, 0)


if __name__ == "__main__":
    unittest.main()

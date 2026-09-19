from __future__ import annotations

import unittest

from safetylens_detector.live import frame_has_visible_signal, parse_capture_source


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


if __name__ == "__main__":
    unittest.main()

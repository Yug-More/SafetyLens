from __future__ import annotations

import unittest

from safetylens_detector.live import parse_capture_source


class LiveSourceTests(unittest.TestCase):
    def test_camera_index_is_integer(self) -> None:
        self.assertEqual(parse_capture_source(" 2 "), 2)

    def test_stream_url_is_preserved(self) -> None:
        url = "http://192.168.1.25:8080/video"
        self.assertEqual(parse_capture_source(url), url)

    def test_blank_source_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be blank"):
            parse_capture_source("  ")


if __name__ == "__main__":
    unittest.main()

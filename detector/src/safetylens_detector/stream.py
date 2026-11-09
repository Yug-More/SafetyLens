"""One-slot live-frame transport: stale frames are counted and replaced.

Recorded videos retain exhaustive decoding. Network streams use explicit OpenCV
open/read deadlines and one daemon reader; timeout support depends on backend.
"""

import threading
import time


class LatestFrameCapture:
    def __init__(self, capture, *, wait_seconds=5):
        self.capture = capture
        self.wait_seconds = wait_seconds
        self.condition = threading.Condition()
        self.frame = None
        self.sequence = 0
        self.consumed = 0
        self.dropped_frames = 0
        self.done = False
        self.closed = False
        self.reader = threading.Thread(
            target=self._read, daemon=True, name="camera-latest-frame"
        )
        self.reader.start()

    def _read(self):
        try:
            while not self.closed:
                ok, frame = self.capture.read()
                if not ok or frame is None:
                    break
                with self.condition:
                    if self.sequence > self.consumed:
                        self.dropped_frames += 1
                    self.sequence += 1
                    self.frame = frame
                    self.condition.notify_all()
        finally:
            with self.condition:
                self.done = True
                self.condition.notify_all()
            self.capture.release()

    def read(self):
        deadline = time.monotonic() + self.wait_seconds
        with self.condition:
            while self.sequence == self.consumed and not self.done and not self.closed:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return False, None
                self.condition.wait(remaining)
            if self.sequence == self.consumed or self.closed:
                return False, None
            self.consumed = self.sequence
            return True, self.frame

    def get(self, prop):
        return self.capture.get(prop)

    def isOpened(self):
        return self.capture.isOpened()

    def release(self):
        # Do not call native release concurrently with read; reader owns it.
        with self.condition:
            self.closed = True
            self.condition.notify_all()
        self.reader.join(timeout=0.25)


def open_network_capture(cv2, source):
    capture = cv2.VideoCapture(
        source,
        cv2.CAP_FFMPEG,
        [cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000, cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000],
    )
    if not capture.isOpened():
        capture.release()
        raise RuntimeError("Network camera unavailable or timeout options unsupported")
    return LatestFrameCapture(capture)

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Generic, TypeVar


FrameT = TypeVar("FrameT")


@dataclass(frozen=True)
class FrameSample(Generic[FrameT]):
    timestamp_seconds: float
    frame: FrameT


@dataclass
class EvidenceCapture(Generic[FrameT]):
    event_id: str
    event_timestamp_seconds: float
    completes_at_seconds: float
    frames: list[FrameSample[FrameT]] = field(default_factory=list)
    completed: bool = False


class EvidenceWindowBuffer(Generic[FrameT]):
    """Keeps a bounded rolling window and completes post-event captures."""

    def __init__(self, *, pre_event_seconds: float, maximum_frames: int = 900) -> None:
        if pre_event_seconds <= 0:
            raise ValueError("pre_event_seconds must be positive.")
        if maximum_frames <= 0:
            raise ValueError("maximum_frames must be positive.")
        self.pre_event_seconds = pre_event_seconds
        self.maximum_frames = maximum_frames
        self._rolling: deque[FrameSample[FrameT]] = deque()
        self._active: dict[str, EvidenceCapture[FrameT]] = {}
        self._completed: deque[EvidenceCapture[FrameT]] = deque()
        self._last_timestamp: float | None = None

    def add(self, timestamp_seconds: float, frame: FrameT) -> None:
        if timestamp_seconds < 0:
            raise ValueError("timestamp_seconds must be non-negative.")
        if self._last_timestamp is not None and timestamp_seconds <= self._last_timestamp:
            raise ValueError("Frame timestamps must strictly increase.")
        self._last_timestamp = timestamp_seconds
        sample = FrameSample(timestamp_seconds=timestamp_seconds, frame=frame)
        self._rolling.append(sample)
        cutoff = timestamp_seconds - self.pre_event_seconds
        while self._rolling and self._rolling[0].timestamp_seconds < cutoff:
            self._rolling.popleft()
        while len(self._rolling) > self.maximum_frames:
            self._rolling.popleft()

        finished: list[str] = []
        for event_id, capture in self._active.items():
            if timestamp_seconds > capture.event_timestamp_seconds:
                capture.frames.append(sample)
            if timestamp_seconds >= capture.completes_at_seconds:
                capture.completed = True
                self._completed.append(capture)
                finished.append(event_id)
        for event_id in finished:
            del self._active[event_id]

    def start_capture(
        self,
        *,
        event_id: str,
        event_timestamp_seconds: float,
        post_event_seconds: float,
    ) -> EvidenceCapture[FrameT]:
        if not event_id.strip():
            raise ValueError("event_id must not be blank.")
        if event_id in self._active or any(item.event_id == event_id for item in self._completed):
            raise ValueError(f"Capture already exists for event {event_id}.")
        if post_event_seconds <= 0:
            raise ValueError("post_event_seconds must be positive.")
        if self._last_timestamp is None:
            raise ValueError("Cannot start a capture before receiving frames.")
        if event_timestamp_seconds > self._last_timestamp:
            raise ValueError("event_timestamp_seconds cannot be in the future.")

        window_start = event_timestamp_seconds - self.pre_event_seconds
        capture = EvidenceCapture(
            event_id=event_id,
            event_timestamp_seconds=event_timestamp_seconds,
            completes_at_seconds=event_timestamp_seconds + post_event_seconds,
            frames=[
                sample
                for sample in self._rolling
                if window_start <= sample.timestamp_seconds <= event_timestamp_seconds
            ],
        )
        self._active[event_id] = capture
        return capture

    def pop_completed(self) -> EvidenceCapture[FrameT] | None:
        return self._completed.popleft() if self._completed else None

    @property
    def rolling_frame_count(self) -> int:
        return len(self._rolling)

    @property
    def active_capture_count(self) -> int:
        return len(self._active)

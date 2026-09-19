from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.services.storage import resolve_frame_path


@dataclass
class VideoMetadata:
    duration_seconds: float
    width: int
    height: int
    fps: float
    frame_count: int


@dataclass
class ExtractedFrame:
    frame_number: int
    timestamp_seconds: float
    stored_filename: str
    width: int
    height: int


def open_capture(path: str) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(path)
    if not capture.isOpened():
        capture.release()
        raise AppError(
            "UNREADABLE_VIDEO",
            "The uploaded file could not be opened as a video.",
            status_code=422,
        )
    return capture


def extract_metadata(path: str, settings: Settings | None = None) -> VideoMetadata:
    cfg = settings or get_settings()
    capture = open_capture(path)
    try:
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

        if width <= 0 or height <= 0:
            raise AppError(
                "INVALID_VIDEO_DIMENSIONS",
                "Video dimensions are invalid or could not be determined.",
                status_code=422,
            )

        if fps <= 0:
            fps = 24.0

        if frame_count <= 0:
            # Defensive fallback: attempt a short decode pass.
            probe_count = 0
            while probe_count < 300:
                ok, _ = capture.read()
                if not ok:
                    break
                probe_count += 1
            frame_count = probe_count
            capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if frame_count <= 0:
            raise AppError(
                "UNREADABLE_VIDEO",
                "No decodable frames were found in the uploaded video.",
                status_code=422,
            )

        duration = frame_count / fps if fps > 0 else 0.0
        if duration <= 0:
            raise AppError(
                "INVALID_VIDEO_DURATION",
                "Video duration could not be determined.",
                status_code=422,
            )
        if duration > cfg.max_video_duration_seconds:
            raise AppError(
                "VIDEO_TOO_LONG",
                f"Video exceeds the maximum duration of {cfg.max_video_duration_seconds} seconds.",
                status_code=422,
            )

        return VideoMetadata(
            duration_seconds=round(duration, 3),
            width=width,
            height=height,
            fps=round(fps, 3),
            frame_count=frame_count,
        )
    finally:
        capture.release()


def choose_frame_indices(frame_count: int, sample_count: int) -> list[int]:
    if frame_count <= 0:
        return []
    count = min(sample_count, frame_count)
    if count == 1:
        return [0]
    # Evenly include beginning, middle, and end without duplicates.
    raw = [int(round(i * (frame_count - 1) / (count - 1))) for i in range(count)]
    unique: list[int] = []
    seen: set[int] = set()
    for index in raw:
        clamped = max(0, min(frame_count - 1, index))
        if clamped not in seen:
            unique.append(clamped)
            seen.add(clamped)
    # Ensure first and last are present when possible.
    if 0 not in seen:
        unique.insert(0, 0)
        seen.add(0)
    last = frame_count - 1
    if last not in seen and len(unique) < sample_count:
        unique.append(last)
    return sorted(unique)[:sample_count]


def choose_event_centered_indices(
    frame_count: int,
    sample_count: int,
    *,
    focus_offset_seconds: float,
    fps: float,
    pre_event_seconds: float = 4.0,
    post_event_seconds: float = 4.0,
) -> list[int]:
    """Bias samples around a detector clip_event_offset while keeping bounds."""
    if frame_count <= 0:
        return []
    if fps <= 0:
        return choose_frame_indices(frame_count, sample_count)

    focus_frame = int(round(max(0.0, focus_offset_seconds) * fps))
    focus_frame = max(0, min(frame_count - 1, focus_frame))
    pre_frames = max(1, int(round(pre_event_seconds * fps)))
    post_frames = max(1, int(round(post_event_seconds * fps)))
    window_start = max(0, focus_frame - pre_frames)
    window_end = min(frame_count - 1, focus_frame + post_frames)

    count = min(sample_count, frame_count)
    if count == 1:
        return [focus_frame]

    # Allocate most samples inside the event window; keep endpoints for context.
    window_span = max(1, window_end - window_start)
    interior_count = max(1, count - 2)
    interior = [
        window_start + int(round(i * window_span / max(1, interior_count - 1)))
        for i in range(interior_count)
    ]
    candidates = [0, focus_frame, frame_count - 1, *interior]
    unique: list[int] = []
    seen: set[int] = set()
    for index in candidates:
        clamped = max(0, min(frame_count - 1, index))
        if clamped not in seen:
            unique.append(clamped)
            seen.add(clamped)
        if len(unique) >= count:
            break
    # Fill remaining with even spacing if needed.
    if len(unique) < count:
        for index in choose_frame_indices(frame_count, sample_count):
            if index not in seen:
                unique.append(index)
                seen.add(index)
            if len(unique) >= count:
                break
    return sorted(unique)[:count]


def _resize_frame(frame: np.ndarray, max_dimension: int) -> np.ndarray:
    height, width = frame.shape[:2]
    largest = max(width, height)
    if largest <= max_dimension:
        return frame
    scale = max_dimension / float(largest)
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)


def save_frame_jpeg(frame: np.ndarray, stored_filename: str, settings: Settings | None = None) -> tuple[int, int]:
    cfg = settings or get_settings()
    resized = _resize_frame(frame, cfg.max_frame_dimension)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(rgb)
    path = resolve_frame_path(stored_filename, cfg)
    image.save(path, format="JPEG", quality=85, optimize=True)
    return image.width, image.height


def extract_representative_frames(
    path: str,
    *,
    fps: float,
    frame_count: int,
    settings: Settings | None = None,
    focus_offset_seconds: float | None = None,
) -> list[ExtractedFrame]:
    cfg = settings or get_settings()
    capture = open_capture(path)
    extracted: list[ExtractedFrame] = []
    try:
        if focus_offset_seconds is not None:
            indices = choose_event_centered_indices(
                frame_count,
                cfg.frame_sample_count,
                focus_offset_seconds=focus_offset_seconds,
                fps=fps,
            )
        else:
            indices = choose_frame_indices(frame_count, cfg.frame_sample_count)
        for frame_number in indices:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ok, frame = capture.read()
            if not ok or frame is None:
                continue
            from app.services.storage import generate_frame_filename

            stored_filename = generate_frame_filename()
            width, height = save_frame_jpeg(frame, stored_filename, cfg)
            timestamp = frame_number / fps if fps > 0 else float(frame_number)
            extracted.append(
                ExtractedFrame(
                    frame_number=frame_number,
                    timestamp_seconds=round(max(0.0, timestamp), 3),
                    stored_filename=stored_filename,
                    width=width,
                    height=height,
                )
            )
    finally:
        capture.release()

    if not extracted:
        raise AppError(
            "FRAME_EXTRACTION_FAILED",
            "No usable frames could be extracted from the uploaded video.",
            status_code=422,
        )
    return extracted

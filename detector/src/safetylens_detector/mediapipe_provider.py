from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .models import Landmark, PoseObservation


def _bounded(value: float | None, default: float = 0.0) -> float:
    return min(1.0, max(0.0, default if value is None else float(value)))


def landmarks_to_observation(
    raw_landmarks: Sequence[Any],
    *,
    timestamp_seconds: float,
    source_id: str,
    track_id: str = "person-1",
) -> PoseObservation:
    """Convert MediaPipe's 33 normalized landmarks without importing its runtime."""

    names = (
        "nose", "left_eye_inner", "left_eye", "left_eye_outer",
        "right_eye_inner", "right_eye", "right_eye_outer", "left_ear",
        "right_ear", "mouth_left", "mouth_right", "left_shoulder",
        "right_shoulder", "left_elbow", "right_elbow", "left_wrist",
        "right_wrist", "left_pinky", "right_pinky", "left_index",
        "right_index", "left_thumb", "right_thumb", "left_hip",
        "right_hip", "left_knee", "right_knee", "left_ankle",
        "right_ankle", "left_heel", "right_heel", "left_foot_index",
        "right_foot_index",
    )
    if len(raw_landmarks) != len(names):
        raise ValueError(f"Expected {len(names)} pose landmarks, got {len(raw_landmarks)}.")

    landmarks: dict[str, Landmark] = {}
    for name, raw in zip(names, raw_landmarks, strict=True):
        visibility = _bounded(getattr(raw, "visibility", None), 1.0)
        presence = _bounded(getattr(raw, "presence", None), 1.0)
        landmarks[name] = Landmark(
            x=_bounded(getattr(raw, "x", None)),
            y=_bounded(getattr(raw, "y", None)),
            visibility=min(visibility, presence),
        )
    return PoseObservation(
        timestamp_seconds=timestamp_seconds,
        source_timestamp_seconds=timestamp_seconds,
        source_id=source_id,
        track_id=track_id,
        landmarks=landmarks,
    )


class MediaPipePoseProvider:
    """Single-person, local pose provider using MediaPipe's video mode."""

    def __init__(
        self,
        model_path: str | Path,
        *,
        min_detection_confidence: float = 0.5,
        min_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        try:
            import mediapipe as mp
        except ImportError as error:
            raise RuntimeError(
                'MediaPipe is required. Install with: pip install -e "detector[video]"'
            ) from error

        model = Path(model_path)
        if not model.is_file():
            raise FileNotFoundError(f"Pose model was not found: {model}")

        self._mp = mp
        options = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model.resolve())),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=min_detection_confidence,
            min_pose_presence_confidence=min_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
            output_segmentation_masks=False,
        )
        self._landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        self._last_timestamp_ms = -1

    def detect(
        self,
        frame_bgr: Any,
        *,
        timestamp_seconds: float,
        source_id: str,
        track_id: str = "person-1",
    ) -> PoseObservation | None:
        import cv2

        timestamp_ms = round(timestamp_seconds * 1000)
        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.pose_landmarks:
            return None
        return landmarks_to_observation(
            result.pose_landmarks[0],
            timestamp_seconds=timestamp_seconds,
            source_id=source_id,
            track_id=track_id,
        )

    def close(self) -> None:
        self._landmarker.close()

    def __enter__(self) -> MediaPipePoseProvider:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

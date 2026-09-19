from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from .engine import DetectorEngine
from .mediapipe_provider import MediaPipePoseProvider
from .models import DetectionEvent, DetectorConfig


@dataclass(frozen=True)
class StateTransition:
    timestamp_seconds: float
    previous_state: str
    state: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class VideoAnalysis:
    source: str
    duration_seconds: float
    source_fps: float
    sample_fps: float
    decoded_frames: int
    analyzed_frames: int
    poses_detected: int
    missing_poses: int
    processing_seconds: float
    events: tuple[DetectionEvent, ...]
    transitions: tuple[StateTransition, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["events"] = [event.to_dict() for event in self.events]
        return payload


def analyze_video(
    video_path: str | Path,
    model_path: str | Path,
    *,
    sample_fps: float = 12.0,
    missing_pose_grace_seconds: float = 0.50,
    source_id: str | None = None,
    config: DetectorConfig | None = None,
) -> VideoAnalysis:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be positive.")
    if missing_pose_grace_seconds < 0:
        raise ValueError("missing_pose_grace_seconds must be non-negative.")
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError(
            'OpenCV is required. Install with: pip install -e "detector[video]"'
        ) from error

    path = Path(video_path)
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        capture.release()
        raise ValueError(f"Could not open video: {path}")

    source_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    if source_fps <= 0:
        capture.release()
        raise ValueError("Video FPS could not be determined.")
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / source_fps if frame_count > 0 else 0.0
    source = source_id or path.stem
    engine = DetectorEngine(config)
    transitions: list[StateTransition] = []
    events: list[DetectionEvent] = []
    decoded = analyzed = detected = missing = 0
    next_sample_seconds = 0.0
    missing_since: float | None = None
    track_marked_missing = False
    started = perf_counter()

    try:
        with MediaPipePoseProvider(model_path) as provider:
            while True:
                ok, frame = capture.read()
                if not ok or frame is None:
                    break
                timestamp = decoded / source_fps
                decoded += 1
                if timestamp + 1e-9 < next_sample_seconds:
                    continue
                next_sample_seconds += 1.0 / sample_fps
                analyzed += 1

                observation = provider.detect(
                    frame,
                    timestamp_seconds=timestamp,
                    source_id=source,
                )
                if observation is None:
                    missing += 1
                    missing_since = timestamp if missing_since is None else missing_since
                    if (
                        not track_marked_missing
                        and timestamp - missing_since >= missing_pose_grace_seconds
                    ):
                        result = engine.mark_missing("person-1")
                        track_marked_missing = True
                    else:
                        continue
                else:
                    detected += 1
                    missing_since = None
                    track_marked_missing = False
                    result = engine.process(observation)
                if result.state != result.previous_state:
                    transitions.append(
                        StateTransition(
                            timestamp_seconds=round(timestamp, 3),
                            previous_state=result.previous_state.value,
                            state=result.state.value,
                            reasons=result.reasons,
                        )
                    )
                if result.event is not None:
                    events.append(result.event)
    finally:
        capture.release()

    return VideoAnalysis(
        source=str(path),
        duration_seconds=round(duration, 3),
        source_fps=round(source_fps, 3),
        sample_fps=sample_fps,
        decoded_frames=decoded,
        analyzed_frames=analyzed,
        poses_detected=detected,
        missing_poses=missing,
        processing_seconds=round(perf_counter() - started, 3),
        events=tuple(events),
        transitions=tuple(transitions),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run MediaPipe pose and the SafetyLens fall state machine on a video."
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--sample-fps", type=float, default=12.0)
    parser.add_argument("--missing-pose-grace-seconds", type=float, default=0.50)
    parser.add_argument("--source-id")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    analysis = analyze_video(
        args.video,
        args.model,
        sample_fps=args.sample_fps,
        missing_pose_grace_seconds=args.missing_pose_grace_seconds,
        source_id=args.source_id,
    )
    rendered = json.dumps(analysis.to_dict(), indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

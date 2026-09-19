from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .engine import DetectorEngine
from .evidence_buffer import EvidenceCapture, EvidenceWindowBuffer
from .mediapipe_provider import MediaPipePoseProvider
from .models import DetectorState


def parse_capture_source(value: str) -> int | str:
    """Treat a decimal value as a camera index; preserve URLs and file paths."""

    stripped = value.strip()
    if not stripped:
        raise ValueError("Camera source must not be blank.")
    return int(stripped) if stripped.isdecimal() else stripped


def _open_capture(cv2: Any, source: int | str) -> Any:
    if isinstance(source, int) and hasattr(cv2, "CAP_DSHOW"):
        capture = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if capture.isOpened():
            return capture
        capture.release()
    return cv2.VideoCapture(source)


def _write_evidence_clip(
    cv2: Any,
    capture: EvidenceCapture[Any],
    *,
    output_directory: Path,
    fps: float,
) -> Path:
    if not capture.frames:
        raise ValueError("Cannot write an empty evidence capture.")
    output_directory.mkdir(parents=True, exist_ok=True)
    output_path = output_directory / f"{capture.event_id}.mp4"
    first = capture.frames[0].frame
    height, width = first.shape[:2]
    writer = cv2.VideoWriter(
        str(output_path),
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    if not writer.isOpened():
        writer.release()
        raise RuntimeError(f"Could not create evidence clip: {output_path}")
    try:
        for sample in capture.frames:
            frame = sample.frame
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, (width, height))
            writer.write(frame)
    finally:
        writer.release()
    return output_path


def run_live(
    capture_source: int | str,
    model_path: str | Path,
    *,
    sample_fps: float = 12.0,
    missing_pose_grace_seconds: float = 0.50,
    pre_event_seconds: float = 3.0,
    post_event_seconds: float = 3.0,
    events_directory: str | Path = "detector/events",
    source_id: str = "live-camera",
    preview: bool = True,
    mirror: bool = False,
    maximum_seconds: float | None = None,
) -> int:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be positive.")
    if missing_pose_grace_seconds < 0:
        raise ValueError("missing_pose_grace_seconds must be non-negative.")
    if maximum_seconds is not None and maximum_seconds <= 0:
        raise ValueError("maximum_seconds must be positive when supplied.")

    try:
        import cv2
    except ImportError as error:
        raise RuntimeError(
            'OpenCV is required. Install with: pip install -e "detector[video]"'
        ) from error

    capture = _open_capture(cv2, capture_source)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Could not open live camera source: {capture_source}")

    engine = DetectorEngine()
    evidence = EvidenceWindowBuffer[Any](
        pre_event_seconds=pre_event_seconds,
        maximum_frames=max(120, round(sample_fps * pre_event_seconds * 2)),
    )
    state = DetectorState.NO_PERSON
    started = perf_counter()
    next_sample_seconds = 0.0
    missing_since: float | None = None
    track_marked_missing = False
    alert_until = 0.0
    analyzed_frames = 0
    events = 0

    print(
        json.dumps(
            {
                "type": "live_started",
                "source": capture_source,
                "source_id": source_id,
                "sample_fps": sample_fps,
                "controls": (
                    "Press Q in the preview window to stop."
                    if preview
                    else "Press Ctrl+C to stop."
                ),
            }
        ),
        flush=True,
    )

    try:
        with MediaPipePoseProvider(model_path) as provider:
            while True:
                ok, frame = capture.read()
                if not ok or frame is None:
                    raise RuntimeError("Live camera stopped returning frames.")
                timestamp = perf_counter() - started
                if mirror:
                    frame = cv2.flip(frame, 1)

                if timestamp + 1e-9 >= next_sample_seconds:
                    next_sample_seconds += 1.0 / sample_fps
                    analyzed_frames += 1
                    evidence.add(timestamp, frame.copy())
                    observation = provider.detect(
                        frame,
                        timestamp_seconds=timestamp,
                        source_id=source_id,
                    )
                    result = None
                    if observation is None:
                        missing_since = timestamp if missing_since is None else missing_since
                        if (
                            not track_marked_missing
                            and timestamp - missing_since >= missing_pose_grace_seconds
                        ):
                            result = engine.mark_missing("person-1")
                            track_marked_missing = True
                    else:
                        missing_since = None
                        track_marked_missing = False
                        result = engine.process(observation)

                    if result is not None:
                        state = result.state
                        if result.state != result.previous_state:
                            print(
                                json.dumps(
                                    {
                                        "type": "state_transition",
                                        "timestamp_seconds": round(timestamp, 3),
                                        "previous_state": result.previous_state.value,
                                        "state": result.state.value,
                                        "reasons": list(result.reasons),
                                    }
                                ),
                                flush=True,
                            )
                        if result.event is not None:
                            events += 1
                            alert_until = timestamp + 5.0
                            evidence.start_capture(
                                event_id=result.event.event_id,
                                event_timestamp_seconds=timestamp,
                                post_event_seconds=post_event_seconds,
                            )
                            print(
                                json.dumps(
                                    {"type": "event", "event": result.event.to_dict()}
                                ),
                                flush=True,
                            )

                    while completed := evidence.pop_completed():
                        path = _write_evidence_clip(
                            cv2,
                            completed,
                            output_directory=Path(events_directory),
                            fps=sample_fps,
                        )
                        print(
                            json.dumps(
                                {
                                    "type": "evidence_saved",
                                    "event_id": completed.event_id,
                                    "path": str(path.resolve()),
                                }
                            ),
                            flush=True,
                        )

                if preview:
                    color = (0, 0, 255) if timestamp < alert_until else (0, 210, 255)
                    cv2.putText(
                        frame,
                        f"SafetyLens: {state.value}",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        color,
                        2,
                        cv2.LINE_AA,
                    )
                    if timestamp < alert_until:
                        cv2.putText(
                            frame,
                            "POSSIBLE PERSON DOWN",
                            (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            (0, 0, 255),
                            2,
                            cv2.LINE_AA,
                        )
                    cv2.imshow("SafetyLens Live - press Q to stop", frame)
                    if cv2.waitKey(1) & 0xFF in {ord("q"), ord("Q")}:
                        break
                if maximum_seconds is not None and timestamp >= maximum_seconds:
                    break
    except KeyboardInterrupt:
        pass
    finally:
        capture.release()
        if preview:
            cv2.destroyAllWindows()

    print(
        json.dumps(
            {
                "type": "live_stopped",
                "elapsed_seconds": round(perf_counter() - started, 3),
                "analyzed_frames": analyzed_frames,
                "events": events,
            }
        ),
        flush=True,
    )
    return events


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run SafetyLens fall detection on a webcam or phone stream."
    )
    parser.add_argument("--source", default="0", help="Camera index or stream URL")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--sample-fps", type=float, default=12.0)
    parser.add_argument("--source-id", default="live-camera")
    parser.add_argument("--events-dir", type=Path, default=Path("detector/events"))
    parser.add_argument("--pre-event-seconds", type=float, default=3.0)
    parser.add_argument("--post-event-seconds", type=float, default=3.0)
    parser.add_argument("--missing-pose-grace-seconds", type=float, default=0.50)
    parser.add_argument("--mirror", action="store_true")
    parser.add_argument("--no-preview", action="store_true")
    parser.add_argument("--max-seconds", type=float)
    args = parser.parse_args()

    run_live(
        parse_capture_source(args.source),
        args.model,
        sample_fps=args.sample_fps,
        missing_pose_grace_seconds=args.missing_pose_grace_seconds,
        pre_event_seconds=args.pre_event_seconds,
        post_event_seconds=args.post_event_seconds,
        events_directory=args.events_dir,
        source_id=args.source_id,
        preview=not args.no_preview,
        mirror=args.mirror,
        maximum_seconds=args.max_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

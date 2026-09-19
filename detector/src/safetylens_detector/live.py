from __future__ import annotations

import argparse
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .engine import DetectorEngine
from .evidence_buffer import EvidenceCapture, EvidenceWindowBuffer
from .mediapipe_provider import MediaPipePoseProvider
from .models import DetectorState, PoseObservation


REASON_PRESENTATION = {
    "rapid_drop": "rapid downward movement",
    "horizontal_posture": "low body posture",
    "wide_tilted_body_box": "low/wide body position",
    "downward_body_displacement": "body moved lower in frame",
    "low_motion": "limited movement",
    "low_motion_persistence": "limited movement sustained",
    "down_posture_persistence": "person-down posture sustained",
    "insufficient_pose_quality": "body partly out of view",
    "track_missing": "person left the camera view",
}

POSE_CONNECTIONS = (
    ("left_shoulder", "right_shoulder"),
    ("left_shoulder", "left_elbow"),
    ("left_elbow", "left_wrist"),
    ("right_shoulder", "right_elbow"),
    ("right_elbow", "right_wrist"),
    ("left_shoulder", "left_hip"),
    ("right_shoulder", "right_hip"),
    ("left_hip", "right_hip"),
    ("left_hip", "left_knee"),
    ("left_knee", "left_ankle"),
    ("right_hip", "right_knee"),
    ("right_knee", "right_ankle"),
)


def parse_capture_source(value: str) -> int | str:
    """Treat a decimal value as a camera index; preserve URLs and file paths."""

    stripped = value.strip()
    if not stripped:
        raise ValueError("Camera source must not be blank.")
    return int(stripped) if stripped.isdecimal() else stripped


def frame_has_visible_signal(frame: Any, *, minimum_peak: float = 8.0) -> bool:
    """Reject the all-black startup frames emitted by some virtual cameras."""

    if getattr(frame, "size", 1) == 0:
        return False
    try:
        return float(frame.max()) > minimum_peak
    except (AttributeError, TypeError, ValueError):
        # Unknown frame containers should remain compatible with custom sources.
        return True


def public_detection_status(fall_active: bool) -> tuple[str, str]:
    """Expose only the two outcomes that matter in the live demo."""

    if fall_active:
        return "Fall detected", "Person is down - human review required"
    return "Normal", "Person tracked - no confirmed fall"


def pose_is_fully_framed(
    observation: PoseObservation | None,
    *,
    minimum_visibility: float = 0.5,
) -> bool:
    """Require a useful single-person demo view before arming live alerts."""

    if observation is None:
        return False
    required = (
        "nose",
        "left_shoulder",
        "right_shoulder",
        "left_hip",
        "right_hip",
        "left_knee",
        "right_knee",
        "left_ankle",
        "right_ankle",
    )
    return all(
        (landmark := observation.landmarks.get(name)) is not None
        and landmark.visibility >= minimum_visibility
        for name in required
    )


def _pose_bounds(
    observation: PoseObservation | None,
    frame_shape: tuple[int, ...],
    *,
    minimum_visibility: float = 0.45,
) -> tuple[int, int, int, int] | None:
    if observation is None:
        return None
    height, width = frame_shape[:2]
    visible = [
        landmark
        for landmark in observation.landmarks.values()
        if landmark.visibility >= minimum_visibility
    ]
    if len(visible) < 4:
        return None
    padding = max(12, round(min(width, height) * 0.025))
    left = max(0, round(min(item.x for item in visible) * width) - padding)
    top = max(0, round(min(item.y for item in visible) * height) - padding)
    right = min(width - 1, round(max(item.x for item in visible) * width) + padding)
    bottom = min(height - 1, round(max(item.y for item in visible) * height) + padding)
    return left, top, right, bottom


def _draw_pose_overlay(
    cv2: Any,
    frame: Any,
    observation: PoseObservation | None,
    color: tuple[int, int, int],
    *,
    label: str = "PERSON TRACKED",
) -> None:
    bounds = _pose_bounds(observation, frame.shape)
    if bounds is None or observation is None:
        return
    height, width = frame.shape[:2]
    for start_name, end_name in POSE_CONNECTIONS:
        start = observation.landmarks.get(start_name)
        end = observation.landmarks.get(end_name)
        if start is None or end is None or min(start.visibility, end.visibility) < 0.45:
            continue
        cv2.line(
            frame,
            (round(start.x * width), round(start.y * height)),
            (round(end.x * width), round(end.y * height)),
            color,
            2,
            cv2.LINE_AA,
        )
    left, top, right, bottom = bounds
    cv2.rectangle(frame, (left, top), (right, bottom), color, 3, cv2.LINE_AA)
    label_top = max(112, top)
    label_bottom = min(bottom, label_top + 30)
    cv2.rectangle(
        frame,
        (left, label_top),
        (min(right, left + 190), label_bottom),
        color,
        -1,
    )
    cv2.putText(
        frame,
        label,
        (left + 8, label_top + 21),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )


def _draw_status_panel(
    cv2: Any,
    frame: Any,
    *,
    title: str,
    detail: str,
    color: tuple[int, int, int],
    reasons: tuple[str, ...],
    alert_active: bool,
    notice: str | None,
) -> None:
    height, width = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (width, 108), (16, 20, 28), -1)
    cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
    cv2.circle(frame, (28, 29), 8, color, -1, cv2.LINE_AA)
    cv2.putText(
        frame, "SAFETYLENS LIVE", (48, 36), cv2.FONT_HERSHEY_SIMPLEX,
        0.72, (245, 245, 245), 2, cv2.LINE_AA,
    )
    cv2.putText(
        frame, title.upper(), (20, 72), cv2.FONT_HERSHEY_SIMPLEX,
        0.78, color, 2, cv2.LINE_AA,
    )
    cv2.putText(
        frame, detail, (20, 98), cv2.FONT_HERSHEY_SIMPLEX,
        0.53, (220, 225, 232), 1, cv2.LINE_AA,
    )
    if reasons:
        readable = [REASON_PRESENTATION.get(reason, reason.replace("_", " ")) for reason in reasons]
        cv2.putText(
            frame,
            "Signals: " + " | ".join(readable[:2]),
            (20, height - 48),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (235, 235, 235),
            1,
            cv2.LINE_AA,
        )
    cv2.putText(
        frame,
        "Q: stop  |  Keep one full person and the floor in view",
        (20, height - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48,
        (210, 215, 225),
        1,
        cv2.LINE_AA,
    )
    if alert_active:
        banner_top = max(116, height // 2 - 42)
        alert_layer = frame.copy()
        cv2.rectangle(alert_layer, (0, banner_top), (width, banner_top + 84), (20, 20, 210), -1)
        cv2.addWeighted(alert_layer, 0.84, frame, 0.16, 0, frame)
        cv2.putText(
            frame,
            "FALL DETECTED - REVIEW NOW",
            (max(20, width // 2 - 270), banner_top + 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.92,
            (255, 255, 255),
            3,
            cv2.LINE_AA,
        )
    if notice:
        size, _ = cv2.getTextSize(notice, cv2.FONT_HERSHEY_SIMPLEX, 0.58, 2)
        box_left = max(16, width - size[0] - 38)
        cv2.rectangle(frame, (box_left, 16), (width - 16, 54), (50, 120, 50), -1)
        cv2.putText(
            frame, notice, (box_left + 12, 42), cv2.FONT_HERSHEY_SIMPLEX,
            0.58, (255, 255, 255), 2, cv2.LINE_AA,
        )


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
    camera_warmup_seconds: float = 15.0,
    arming_seconds: float = 1.5,
) -> int:
    if sample_fps <= 0:
        raise ValueError("sample_fps must be positive.")
    if missing_pose_grace_seconds < 0:
        raise ValueError("missing_pose_grace_seconds must be non-negative.")
    if maximum_seconds is not None and maximum_seconds <= 0:
        raise ValueError("maximum_seconds must be positive when supplied.")
    if camera_warmup_seconds <= 0:
        raise ValueError("camera_warmup_seconds must be positive.")
    if arming_seconds < 0:
        raise ValueError("arming_seconds must be non-negative.")

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

    started = perf_counter()
    next_sample_seconds = 0.0
    missing_since: float | None = None
    track_marked_missing = False
    notice_until = 0.0
    notice: str | None = None
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
        print(
            json.dumps(
                {
                    "type": "camera_warming_up",
                    "timeout_seconds": camera_warmup_seconds,
                }
            ),
            flush=True,
        )
        warmup_started = perf_counter()
        first_frame = None
        while first_frame is None:
            ok, candidate = capture.read()
            if not ok or candidate is None:
                raise RuntimeError("Live camera stopped returning frames during startup.")
            if frame_has_visible_signal(candidate):
                first_frame = candidate
                break
            warmup_elapsed = perf_counter() - warmup_started
            if preview:
                cv2.putText(
                    candidate,
                    "Waiting for Camo camera video...",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 210, 255),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow("SafetyLens Live - press Q to stop", candidate)
                if cv2.waitKey(1) & 0xFF in {ord("q"), ord("Q")}:
                    return events
            if warmup_elapsed >= camera_warmup_seconds:
                raise RuntimeError(
                    "Camera opened but only returned black frames. Confirm Camo Studio is "
                    "showing the phone feed, resume Camo output, and retry."
                )

        print(
            json.dumps(
                {
                    "type": "camera_ready",
                    "warmup_seconds": round(perf_counter() - warmup_started, 3),
                }
            ),
            flush=True,
        )
        started = perf_counter()
        engine = DetectorEngine()
        evidence = EvidenceWindowBuffer[Any](
            pre_event_seconds=pre_event_seconds,
            maximum_frames=max(120, round(sample_fps * pre_event_seconds * 2)),
        )
        state = DetectorState.NO_PERSON
        latest_observation: PoseObservation | None = None
        latest_reasons: tuple[str, ...] = ()
        detector_armed = False
        fall_active = False
        framing_ready_since: float | None = None
        pending_frame = first_frame
        with MediaPipePoseProvider(model_path) as provider:
            while True:
                if pending_frame is not None:
                    frame = pending_frame
                    pending_frame = None
                else:
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
                    latest_observation = observation
                    result = None
                    if not detector_armed:
                        if pose_is_fully_framed(observation):
                            framing_ready_since = (
                                timestamp
                                if framing_ready_since is None
                                else framing_ready_since
                            )
                            if timestamp - framing_ready_since >= arming_seconds:
                                detector_armed = True
                                notice = "Detector ready"
                                notice_until = timestamp + 3.0
                                print(
                                    json.dumps(
                                        {
                                            "type": "detector_ready",
                                            "timestamp_seconds": round(timestamp, 3),
                                        }
                                    ),
                                    flush=True,
                                )
                        else:
                            framing_ready_since = None

                    if detector_armed and observation is None:
                        missing_since = timestamp if missing_since is None else missing_since
                        if (
                            not track_marked_missing
                            and timestamp - missing_since >= missing_pose_grace_seconds
                        ):
                            result = engine.mark_missing("person-1")
                            track_marked_missing = True
                    elif detector_armed and observation is not None:
                        missing_since = None
                        track_marked_missing = False
                        result = engine.process(observation)

                    if result is not None:
                        state = result.state
                        if result.event is not None:
                            fall_active = True
                            latest_reasons = result.event.trigger_signals
                        elif (
                            fall_active
                            and result.previous_state == DetectorState.COOLDOWN
                            and result.state == DetectorState.MONITORING
                        ):
                            fall_active = False
                            latest_reasons = ()
                            notice = "Monitoring resumed"
                            notice_until = timestamp + 3.0
                        if result.state != result.previous_state:
                            print(
                                json.dumps(
                                    {
                                        "type": "state_transition",
                                        "timestamp_seconds": round(timestamp, 3),
                                        "previous_state": result.previous_state.value,
                                        "state": result.state.value,
                                        "display_state": public_detection_status(
                                            fall_active
                                        )[0],
                                        "reasons": list(result.reasons),
                                    }
                                ),
                                flush=True,
                            )
                        if result.event is not None:
                            events += 1
                            notice = "Incident recorded"
                            notice_until = timestamp + 4.0
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
                        notice = "Evidence clip saved"
                        notice_until = timestamp + 4.0

                if preview:
                    if detector_armed and fall_active:
                        title, detail = public_detection_status(True)
                        color = (40, 40, 235)
                        pose_label = "FALL DETECTED"
                    elif detector_armed and latest_observation is not None:
                        title, detail = public_detection_status(False)
                        color = (60, 210, 90)
                        pose_label = "NORMAL"
                    elif detector_armed:
                        title = "Waiting for person"
                        detail = "Return to the full-body camera view"
                        color = (150, 150, 150)
                        pose_label = "NORMAL"
                    elif latest_observation is None:
                        title = "Position one person"
                        detail = "Step into view with your head, ankles, and floor visible"
                        color = (0, 200, 255)
                        pose_label = "POSITION CHECK"
                    elif not pose_is_fully_framed(latest_observation):
                        title = "Adjust camera"
                        detail = "Show one person's head, both ankles, and the floor"
                        color = (0, 200, 255)
                        pose_label = "PARTIAL VIEW"
                    else:
                        ready_for = (
                            0.0
                            if framing_ready_since is None
                            else timestamp - framing_ready_since
                        )
                        remaining = max(0.0, arming_seconds - ready_for)
                        title = "Getting ready"
                        detail = f"Hold position - monitoring begins in {remaining:.1f}s"
                        color = (0, 200, 255)
                        pose_label = "FULL BODY VISIBLE"
                    _draw_pose_overlay(
                        cv2,
                        frame,
                        latest_observation,
                        color,
                        label=pose_label,
                    )
                    _draw_status_panel(
                        cv2,
                        frame,
                        title=title,
                        detail=detail,
                        color=color,
                        reasons=latest_reasons if detector_armed else (),
                        alert_active=fall_active,
                        notice=notice if timestamp < notice_until else None,
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
    parser.add_argument("--camera-warmup-seconds", type=float, default=15.0)
    parser.add_argument("--arming-seconds", type=float, default=1.5)
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
        camera_warmup_seconds=args.camera_warmup_seconds,
        arming_seconds=args.arming_seconds,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Bounded multi-camera CPU worker with reconnect, preview and durable delivery.

Run separately from the API. Sources/credentials remain server/device side.
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4
from .delivery import EventOutbox
from .enhanced import EnhancedDetectorEngine
from .evidence_buffer import EvidenceWindowBuffer
from .mediapipe_provider import MediaPipePoseProvider
from .live import _write_evidence_clip
from .ppe import OnnxPpeDetector, PpeTemporalMonitor, associate_ppe, draw_ppe_overlay


def run_camera(
    camera_id, backend, token, pose_model, ppe_manifest, root, stop, max_seconds=None
):
    import cv2
    import httpx

    outbox = EventOutbox(root / "outbox")
    headers = {"Authorization": "Bearer " + token}
    started = time.monotonic()
    backoff = 1
    state = {
        "status": "offline",
        "frames_processed": 0,
        "dropped_frames": None,
        "processing_fps": None,
        "preview": None,
    }
    lock = threading.Lock()

    def transport():
        with httpx.Client(timeout=5, follow_redirects=False) as client:
            while not stop.is_set():
                with lock:
                    snapshot = dict(state)
                try:
                    image = snapshot.pop("preview")
                    client.post(
                        backend + "/api/detector/heartbeat",
                        headers=headers,
                        json={"camera_id": camera_id, **snapshot},
                    ).raise_for_status()
                    if image is not None:
                        client.post(
                            backend + f"/api/detector/snapshot/{camera_id}",
                            headers=headers,
                            files={"image": ("preview.jpg", image, "image/jpeg")},
                        ).raise_for_status()
                    outbox.flush_once(backend, token, client=client)
                    outbox.prune(acknowledged_before=time.time() - 86400)
                except (httpx.HTTPError, ValueError, BufferError):
                    pass  # Outbox preserves evidence; transport failures do not block inference.
                stop.wait(2)

    buffer = None
    events = {}
    sender = threading.Thread(target=transport, daemon=True)
    sender.start()
    try:
        while not stop.is_set() and (
            max_seconds is None or time.monotonic() - started < max_seconds
        ):
            capture = None
            try:
                with httpx.Client(timeout=10) as client:
                    response = client.get(
                        backend + f"/api/detector/config/{camera_id}", headers=headers
                    )
                    response.raise_for_status()
                    config = response.json()["data"]
                if not config["enabled"]:
                    stop.wait(5)
                    continue
                policy = config["policy"]
                if "ppe" in policy.get("detectors", []):
                    raise RuntimeError("PPE deployment excluded; use offline evaluation until model validation and licensing are resolved")
                fps = policy.get("sample_fps", 8)
                source = config["source"]
                kind = config["source_kind"]
                if kind == "simulator":
                    source = None
                elif kind == "webcam":
                    source = int(source)
                capture = cv2.VideoCapture(source) if source is not None else None
                if capture is not None and not capture.isOpened():
                    raise RuntimeError("Camera unavailable")
                engine = EnhancedDetectorEngine()
                ppe = (
                    OnnxPpeDetector(
                        ppe_manifest, threshold=policy.get("confidence_threshold", 0.5)
                    )
                    if "ppe" in policy.get("detectors", []) and ppe_manifest
                    else None
                )
                monitor = PpeTemporalMonitor()
                buffer = EvidenceWindowBuffer(
                    pre_event_seconds=policy.get("pre_event_seconds", 3),
                    maximum_frames=round(fps * 32),
                )
                events = {}
                def enqueue_completed():
                    while completed := buffer.pop_completed():
                        path = _write_evidence_clip(
                            cv2, completed, output_directory=root / "clips", fps=fps
                        )
                        offset = (
                            sum(
                                x.timestamp_seconds
                                < completed.event_timestamp_seconds
                                for x in completed.frames
                            )
                            / fps
                        )
                        outbox.enqueue(
                            events.pop(completed.event_id),
                            path,
                            camera_id=camera_id,
                            location=config["location"],
                            clip_event_offset_seconds=offset,
                        )
                        path.unlink()  # Durable outbox owns its copy; no unbounded duplicate storage.

                notified = set()
                missing_since = None
                from .tracking import PoseTracker
                tracker = PoseTracker() if policy.get("maximum_pose_people",1)>1 else None
                frame_number = 0
                connection_started = time.monotonic()
                next_sample = connection_started
                last_config_check = time.monotonic()
                with MediaPipePoseProvider(pose_model, region=policy.get("pose_region"), num_poses=policy.get("maximum_pose_people",1)) as pose:
                    while not stop.is_set():
                        if (
                            max_seconds is not None
                            and time.monotonic() - started >= max_seconds
                        ):
                            return
                        if capture is None:
                            import numpy as np

                            frame = np.zeros((480, 640, 3), dtype=np.uint8)
                            cv2.putText(
                                frame,
                                "SIMULATED CAMERA - NO DETECTION",
                                (15, 240),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.6,
                                (255, 255, 255),
                                1,
                            )
                        else:
                            ok, frame = capture.read()
                            if not ok or frame is None:
                                for event_id in buffer.finish_pending():
                                    events[event_id].setdefault("limitations", []).append(
                                        "post_event_window_truncated_at_source_end"
                                    )
                                enqueue_completed()
                                if kind == "replay":
                                    with lock:
                                        state["status"] = "offline"
                                    return  # A finite replay is consumed once; do not emit new UUIDs forever.
                                raise RuntimeError("Frame unavailable")
                        now = time.monotonic()
                        if (
                            now - last_config_check > 30
                            and not buffer.active_capture_count
                        ):
                            with httpx.Client(timeout=5) as client:
                                update = client.get(
                                    backend + f"/api/detector/config/{camera_id}",
                                    headers=headers,
                                )
                                update.raise_for_status()
                                latest = update.json()["data"]
                            if any(
                                latest.get(k) != config.get(k)
                                for k in ("enabled", "source", "source_kind", "policy")
                            ):
                                break
                            last_config_check = now
                        # Replay uses source frame position; live input uses monotonic elapsed time.
                        source_fps = capture.get(cv2.CAP_PROP_FPS) if capture else fps
                        if kind == "replay" and source_fps > 0:
                            timestamp = frame_number / source_fps
                            frame_number += 1
                            if timestamp + 1e-9 < (next_sample - connection_started):
                                continue
                        else:
                            timestamp = now - connection_started
                        if kind != "replay" and now < next_sample:
                            stop.wait(min(0.01, next_sample - now))
                            continue
                        if kind == "replay":
                            next_sample += 1 / fps
                        else:
                            next_sample = connection_started + timestamp + 1 / fps
                        buffer.add(timestamp, frame.copy())
                        current = []
                        if kind != "simulator" and "fall" in policy.get(
                            "detectors", []
                        ):
                            if tracker:
                                observations = pose.detect_many(frame,timestamp_seconds=timestamp,source_id=camera_id)
                                linked, expired, _ = tracker.update(timestamp,observations)
                                for track_id in expired:
                                    engine.forget_track(track_id)
                                results = [engine.process(o) for o in linked]
                            else:
                                observation = pose.detect(
                                    frame, timestamp_seconds=timestamp, source_id=camera_id
                                )
                                if observation is not None:
                                    missing_since = None
                                    result = engine.process(observation)
                                else:
                                    missing_since = (
                                        timestamp
                                        if missing_since is None
                                        else missing_since
                                    )
                                    result = (
                                        engine.mark_missing("person-1")
                                        if timestamp - missing_since >= 0.5
                                        else None
                                    )
                                results = [result] if result else []
                            for result in results:
                                if result.event:
                                    current.append(result.event.to_dict())
                        preview = frame
                        if ppe and kind != "simulator":
                            boxes = ppe.detect(frame)
                            people = monitor.process(
                                timestamp,
                                associate_ppe(
                                    boxes,
                                    policy.get("required_ppe", []),
                                    threshold=policy.get("confidence_threshold", 0.5),
                                ),
                            )
                            preview = draw_ppe_overlay(frame, boxes, people)
                            for person in people:
                                if (
                                    person["review_required"]
                                    and person["track_id"] not in notified
                                ):
                                    notified.add(person["track_id"])
                                    current.append(
                                        {
                                            "schema_version": "1.0",
                                            "event_id": str(uuid4()),
                                            "event_type": "ppe_noncompliance",
                                            "source_id": camera_id,
                                            "track_id": person["track_id"],
                                            "occurred_at_seconds": timestamp,
                                            "trigger_signals": [
                                                "persistent_ppe_not_visible"
                                            ],
                                            "metrics": {
                                                "required_ppe": policy.get(
                                                    "required_ppe", []
                                                ),
                                                "observed_ppe": person["observed"],
                                                "possibly_missing_ppe": person[
                                                    "possibly_missing"
                                                ],
                                            },
                                            "limitations": [
                                                "Experimental ONNX detector",
                                                "PPE absence is unconfirmed; human review required",
                                            ],
                                        }
                                    )
                                    if len(notified) > 1000:
                                        notified = {person["track_id"]}
                        for event in current:
                            event["occurred_at"] = datetime.now(
                                timezone.utc
                            ).isoformat()
                            events[event["event_id"]] = event
                            buffer.start_capture(
                                event_id=event["event_id"],
                                event_timestamp_seconds=timestamp,
                                post_event_seconds=policy.get("post_event_seconds", 3),
                            )
                        enqueue_completed()
                        ok, jpeg = cv2.imencode(
                            ".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 70]
                        )
                        with lock:
                            state["status"] = "online"
                            state["frames_processed"] += 1
                            state["processing_fps"] = state["frames_processed"] / max(
                                0.001, now - started
                            )
                            state["preview"] = jpeg.tobytes() if ok else None
                        backoff = 1
                        if kind == "simulator":
                            stop.wait(1 / fps)
            except BufferError:
                with lock:
                    state["status"] = "degraded"
                print(
                    json.dumps(
                        {
                            "camera_id": camera_id,
                            "status": "halted",
                            "reason": "outbox_capacity; evidence retained; operator action required",
                        }
                    ),
                    flush=True,
                )
                return
            except Exception as exc:
                with lock:
                    state["status"] = "offline"
                print(
                    json.dumps(
                        {
                            "camera_id": camera_id,
                            "status": "reconnecting",
                            "error_type": type(exc).__name__,
                        }
                    ),
                    flush=True,
                )
                stop.wait(backoff)
                backoff = min(30, backoff * 2)
            finally:
                if capture:
                    capture.release()
    finally:
        if buffer is not None:
            try:
                for event_id in buffer.finish_pending():
                    events[event_id].setdefault("limitations", []).append("post_event_window_truncated_at_worker_shutdown")
                enqueue_completed()
            except (BufferError, OSError, ValueError):
                pass  # Original clip remains on disk if durable capacity is exhausted.
        # Short replays may finish before the periodic transport tick. Flush once
        # synchronously; failures remain durable for delivery CLI/restart recovery.
        try:
            outbox.flush_once(backend, token)
        except (httpx.HTTPError, ValueError, BufferError):
            pass
        stop.set()
        sender.join(timeout=6)
        elapsed=time.monotonic()-started
        with lock:
            summary={k:v for k,v in state.items() if k != "preview"}
        summary.update(kind="camera_worker_summary",camera_id=camera_id,wall_seconds=elapsed,
                       average_sampled_fps=summary["frames_processed"]/max(elapsed,.001))
        print(json.dumps(summary,allow_nan=False),flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--backend", default="http://127.0.0.1:8000")
    p.add_argument("--camera-ids", required=True)
    p.add_argument("--pose-model", required=True, type=Path)
    p.add_argument("--ppe-manifest", type=Path)
    p.add_argument("--state-dir", type=Path, default=Path("detector/events/worker"))
    p.add_argument("--max-seconds", type=float)
    a = p.parse_args()
    ids = list(dict.fromkeys(x.strip() for x in a.camera_ids.split(",") if x.strip()))
    if not 1 <= len(ids) <= 4:
        p.error("Configure one to four cameras per worker process")
    token = os.environ.get("DETECTOR_API_TOKEN", "")
    if not token:
        p.error("Set DETECTOR_API_TOKEN in the environment")
    from urllib.parse import urlparse

    url = urlparse(a.backend)
    if url.scheme != "https" and not (
        url.scheme == "http" and url.hostname in {"127.0.0.1", "localhost", "::1"}
    ):
        p.error("Remote backend requires HTTPS")
    threads = []
    stops = []
    for camera_id in ids:
        import hashlib

        stop = threading.Event()
        stops.append(stop)
        directory = a.state_dir / hashlib.sha256(camera_id.encode()).hexdigest()[:16]
        thread = threading.Thread(
            target=run_camera,
            args=(
                camera_id,
                a.backend.rstrip("/"),
                token,
                a.pose_model,
                a.ppe_manifest,
                directory,
                stop,
                a.max_seconds,
            ),
        )
        thread.start()
        threads.append(thread)
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        for stop in stops:
            stop.set()
        for thread in threads:
            thread.join(timeout=10)


if __name__ == "__main__":
    main()

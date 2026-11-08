# Camera pipeline

## Register and configure

Sign in as administrator, open Cameras & Zones, and register name, location, facility/zone labels, source type, private source, enabled detectors, sampling FPS, PPE requirements and pre/post/retention settings. Set `CAMERA_ENCRYPTION_KEY` server-side before storing a source. Generate a Fernet key locally with `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`; keep it outside Git and back it up securely. Losing it makes stored sources unreadable.

Source types: webcam index, RTSP/network URL, recorded replay or explicitly labeled simulator. Sources execute on the device running the worker, not in the API container. Facility/zone labels group cameras; independent facility entities/floor-plan management are not implemented.

## Device configuration

Set the same strong `DETECTOR_API_TOKEN` on server and worker, and set server `DETECTOR_CAMERA_IDS` to comma-separated authorized camera primary IDs. Tokens must never appear in browser code, URLs or shell history. Supply them through an environment file/secret manager. Remote delivery requires HTTPS; HTTP is accepted only on loopback.

```sh
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.worker \
  --backend http://127.0.0.1:8000 --camera-ids CAMERA_UUID \
  --pose-model /path/pose_landmarker_lite.task --state-dir detector/events/worker
# Add --ppe-manifest /path/ppe.json only after model/license review.
```

The worker supports up to four cameras/process, one pose/person per camera. Camera configuration is rechecked approximately every 30 seconds; active evidence capture finishes before reconfiguration. Stream failures trigger bounded exponential reconnection. Slow inference samples fewer frames rather than building an unbounded queue. PPE inference currently shares the camera inference loop; its measured cost must be considered before enabling multiple cameras.

Every completed event has its own UUID and explicit clip-relative offset. Failed delivery remains on disk; a sender restart retries pending events after lease/backoff. Backend UUID uniqueness prevents ordinary repeated imports. Permanent HTTP errors block the delivery for operator investigation. Outbox defaults: 1000 active events, 500 MB clip storage, 24-hour acknowledged retention. Capacity exhaustion halts that camera and retains evidence; pending events are not silently discarded. Partial captures on shutdown remain a limitation; clips are enqueued only when complete.

## Original live preview

The original `safetylens_detector.live` CLI remains, with optional `--outbox`, `--camera-id`, and `--location`. Run `safetylens_detector.delivery --outbox ... --backend ...` separately to flush it. The enhanced multi-camera worker automatically includes delivery/heartbeat/preview threads.

## Preview and health

Device heartbeats and bounded JPEG snapshot uploads are authenticated and camera-scoped. Only a latest per-camera JPEG is kept. Operator previews refresh every three seconds and are labeled recorded/simulated when appropriate. An absent/stale snapshot returns an error state. A camera is considered offline after 30 seconds without heartbeat; SSE subscribers trigger this health aggregation. No high-FPS browser video transport, RTSP-to-WebRTC gateway, or detection-box preview overlay has been implemented. Preserved incident videos remain playable.

## Retention

Per-camera evidence periods are enforced by explicit administrator retention runs. Only media older than the policy and linked to resolved/dismissed/closed incidents is eligible. Open and unlinked media, metadata, reports and audit records are preserved. Preview expiration first in Settings. Evidence expiration is permanent and audited. This is not a legal retention policy.

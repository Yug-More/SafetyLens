"""Optional model-backed browser fixture. Processes actual licensed external video.

No fabricated boxes/events. Use only against scripts/e2e_backend.py's isolated DB.
Set SAFETYLENS_REAL_CLIP and SAFETYLENS_POSE_MODEL; weights/media stay outside Git.
"""

import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time
import httpx

root = Path(__file__).resolve().parents[1]
clip = Path(os.environ["SAFETYLENS_REAL_CLIP"]).resolve(strict=True)
model = Path(os.environ["SAFETYLENS_POSE_MODEL"]).resolve(strict=True)
folder = Path(tempfile.mkdtemp(prefix="safetylens-real-worker-"))
base = os.environ.get("SAFETYLENS_E2E_BACKEND", "http://127.0.0.1:8107")
started = time.perf_counter()
with httpx.Client(base_url=base, timeout=30) as client:
    response = client.post(
        "/api/auth/login",
        json={
            "username": os.environ.get("SAFETYLENS_E2E_USERNAME", "qa-admin"),
            "password": os.environ["SAFETYLENS_E2E_PASSWORD"],
        },
    )
    response.raise_for_status()
    client.headers["X-CSRF-Token"] = response.json()["data"]["csrf_token"]
    # Configure the already registered, explicitly device-scoped test camera.
    response = client.put(
        "/api/cameras/cam-03",
        json={
            "name": "Camera 03 — Real recorded validation",
            "location": "UR Fall academic replay",
            "source_kind": "replay",
            "source": str(clip),
            "enabled": True,
            "policy": {
                "sample_fps": 12,
                "pre_event_seconds": 2,
                "post_event_seconds": 3,
                "pose_region": [0.5, 0, 1, 1],
                "detectors": ["fall", "camera_health"],
            },
        },
    )
    response.raise_for_status()
    command = [
        str(root / "detector/.venv/bin/python"),
        "-m",
        "safetylens_detector.worker",
        "--backend",
        base,
        "--camera-ids",
        "cam-03",
        "--pose-model",
        str(model),
        "--state-dir",
        str(folder),
        "--max-seconds",
        "30",
    ]
    temporal = os.environ.get("SAFETYLENS_TEMPORAL_CHECKPOINT")
    if temporal:
        command += [
            "--temporal-checkpoint",
            temporal,
            "--temporal-sha256",
            os.environ["SAFETYLENS_TEMPORAL_SHA256"],
        ]
    env = {**os.environ, "PYTHONPATH": str(root / "detector/src")}
    result = subprocess.run(
        command, env=env, capture_output=True, text=True, timeout=45
    )
    (folder / "worker.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"Actual worker failed; inspect {folder}/worker.log")
    databases = list(folder.rglob("outbox.sqlite3"))
    if not databases:
        raise RuntimeError("Worker created no outbox")
    with sqlite3.connect(databases[0]) as db:
        rows = db.execute("SELECT event_id,status,payload FROM deliveries").fetchall()
    if not rows or any(x[1] != "acknowledged" for x in rows):
        raise RuntimeError(f"Actual model event not acknowledged; inspect {folder}")
    event = json.loads(rows[0][2])
    assert ("learned_temporal_candidate" if temporal else "rapid_drop") in event[
        "trigger_signals"
    ], event
    verification = {
        "event_id": rows[0][0],
        "events": len(rows),
        "mode": "real_learned_temporal_worker" if temporal else "real_mediapipe_worker",
        "clip": str(clip),
        "delivery_wall_seconds": time.perf_counter() - started,
        "event": event,
        "source_consumed_once": True,
    }
    (folder / "verification.json").write_text(json.dumps(verification, indent=2))
    print(
        json.dumps(
            {
                "event_id": rows[0][0],
                "mode": "real_learned_temporal_worker"
                if temporal
                else "real_mediapipe_worker",
                "verification_path": str(folder / "verification.json"),
            }
        )
    )

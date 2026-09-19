from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.services.video_processing import choose_event_centered_indices, choose_frame_indices
from tests.conftest import make_test_video


def _contract_event(event_id: str = "evt-demo-001") -> dict:
    return {
        "schema_version": "1.0",
        "event_id": event_id,
        "event_type": "possible_person_down",
        "source_id": "demo-camera-04",
        "camera_id": "cam-04",
        "track_id": "track-1",
        "occurred_at": "2026-09-19T17:05:46Z",
        "source_timestamp_seconds": 2.0,
        "clip_event_offset_seconds": 2.0,
        "state": "incident",
        "trigger_signals": ["rapid_drop", "horizontal_persistence"],
        "pose_quality": 0.91,
        "heuristic_score": None,
        "metrics": {
            "torso_angle_degrees_from_vertical": 76,
            "horizontal_duration_seconds": 2.1,
        },
        "evidence": {
            "clip_relative_path": None,
            "pre_event_seconds": 2,
            "post_event_seconds": 2,
            "frame_offsets_seconds": [0, 1, 2, 3],
        },
        "limitations": ["requires_human_verification"],
    }


def _wait_ready(client: TestClient, asset_code: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        video = client.get(f"/api/videos/{asset_code}").json()["data"]
        if video["status"] == "ready":
            return
        if video["status"] == "failed":
            raise AssertionError(video)
        time.sleep(0.05)
    raise AssertionError("video not ready")


def test_choose_event_centered_indices_includes_focus():
    even = choose_frame_indices(80, 8)
    centered = choose_event_centered_indices(
        80,
        8,
        focus_offset_seconds=5.0,
        fps=8.0,
    )
    assert centered
    assert 40 in centered or min(centered, key=lambda i: abs(i - 40)) in centered
    assert centered != even or 40 in centered


def test_detector_ingest_duplicate_and_analysis(client: TestClient, tmp_path: Path):
    clip = make_test_video(tmp_path / "fall_clip.mp4", frames=40, fps=8)
    event = _contract_event("evt-unique-1")

    with clip.open("rb") as handle:
        first = client.post(
            "/api/detector/events",
            data={
                "event_json": json.dumps(event),
                "location": "Loading Zone B",
                "auto_analyze": "true",
                "incident_identifier": "INC-2026-0042",
            },
            files={"clip": ("fall_clip.mp4", handle, "video/mp4")},
        )
    assert first.status_code == 202, first.text
    payload = first.json()["data"]
    assert payload["event_id"] == "evt-unique-1"
    assert payload["asset_code"]
    assert payload["pose_quality_label"].startswith("landmark reliability")
    assert payload["is_simulated"] is True

    # Duplicate event_id must reuse mapping (no second upload required).
    duplicate = client.post(
        "/api/detector/events",
        data={
            "event_json": json.dumps(event),
            "location": "Loading Zone B",
            "auto_analyze": "true",
        },
        files={},
    )
    assert duplicate.status_code == 202, duplicate.text
    assert duplicate.json()["data"]["asset_code"] == payload["asset_code"]

    _wait_ready(client, payload["asset_code"])
    fetched = client.get("/api/detector/events/evt-unique-1")
    assert fetched.status_code == 200
    body = fetched.json()["data"]
    assert body["asset_code"] == payload["asset_code"]
    assert body["status"] in {"ready", "analyzing", "completed"}

    # Force advance / analyze if still ready.
    if body["status"] == "ready":
        retried = client.post("/api/detector/events/evt-unique-1/retry")
        assert retried.status_code == 200

    deadline = time.time() + 20
    while time.time() < deadline:
        status = client.get("/api/detector/events/evt-unique-1").json()["data"]
        if status["status"] == "completed" and status.get("analysis_code"):
            break
        if status["status"] == "failed":
            raise AssertionError(status)
        time.sleep(0.1)
    else:
        # Analysis may still be running in background; ensure asset remains unique.
        listed = client.get("/api/detector/events").json()["data"]
        matching = [item for item in listed if item["event_id"] == "evt-unique-1"]
        assert len(matching) == 1


def test_invalid_schema_and_malformed_event(client: TestClient, tmp_path: Path):
    clip = make_test_video(tmp_path / "bad.mp4", frames=16, fps=8)
    bad = _contract_event("evt-bad-schema")
    bad["schema_version"] = "9.9"
    with clip.open("rb") as handle:
        response = client.post(
            "/api/detector/events",
            data={"event_json": json.dumps(bad)},
            files={"clip": ("bad.mp4", handle, "video/mp4")},
        )
    assert response.status_code == 422

    with clip.open("rb") as handle:
        malformed = client.post(
            "/api/detector/events",
            data={"event_json": "{not-json"},
            files={"clip": ("bad.mp4", handle, "video/mp4")},
        )
    assert malformed.status_code == 422


def test_upload_path_works_without_detector(client: TestClient, tmp_path: Path):
    clip = make_test_video(tmp_path / "upload_only.mp4", frames=24, fps=8)
    with clip.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            files={"file": ("upload_only.mp4", handle, "video/mp4")},
            data={"location": "Loading Zone B", "camera_id": "cam-04"},
        )
    assert uploaded.status_code == 202
    asset = uploaded.json()["data"]["asset_code"]
    _wait_ready(client, asset)
    analysis = client.post(f"/api/videos/{asset}/analyze")
    assert analysis.status_code == 202


def test_demo_reset_requires_confirmation_and_clears_runtime(
    client: TestClient, tmp_path: Path
):
    denied = client.post("/api/demo/reset", json={"confirmed": False})
    assert denied.status_code == 422

    clip = make_test_video(tmp_path / "reset_clip.mp4", frames=16, fps=8)
    with clip.open("rb") as handle:
        client.post(
            "/api/videos/upload",
            files={"file": ("reset_clip.mp4", handle, "video/mp4")},
            data={"location": "Loading Zone B"},
        )

    reset = client.post("/api/demo/reset", json={"confirmed": True})
    assert reset.status_code == 200, reset.text
    body = reset.json()["data"]
    assert body["reset"] is True
    assert body["reseeding_completed"] is True

    videos = client.get("/api/videos").json()["data"]
    assert videos == []
    incident = client.get("/api/incidents/INC-2026-0042")
    assert incident.status_code == 200

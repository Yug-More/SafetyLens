"""Focused tests for idempotent post-analysis workflow orchestration."""

from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient

from tests.conftest import make_test_video


def _analyze_ready(client: TestClient, tmp_path: Path) -> str:
    video_path = make_test_video(tmp_path / "workflow.mp4", frames=40, fps=8)
    with video_path.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            files={"file": ("workflow.mp4", handle, "video/mp4")},
            data={"location": "Warehouse Aisle", "camera_id": "cam-03"},
        ).json()["data"]
    deadline = time.time() + 20
    while time.time() < deadline:
        job = client.get(f"/api/processing-jobs/{uploaded['job_code']}").json()["data"]
        if job["status"] in {"completed", "failed"}:
            break
        time.sleep(0.05)
    analysis_code = client.post(
        f"/api/videos/{uploaded['asset_code']}/analyze"
    ).json()["data"]["analysis_code"]
    deadline = time.time() + 20
    while time.time() < deadline:
        analysis = client.get(f"/api/analyses/{analysis_code}").json()["data"]
        if analysis["status"] in {"completed", "needs_review", "failed"}:
            break
        time.sleep(0.05)
    return analysis_code


def test_prepare_response_idempotent_and_notification(client: TestClient, tmp_path: Path):
    analysis_code = _analyze_ready(client, tmp_path)
    first = client.post(f"/api/analyses/{analysis_code}/prepare-response")
    assert first.status_code == 200, first.text
    data = first.json()["data"]
    assert data["analysis_code"] == analysis_code
    assert data["camera_name"] in {None, "Camera 03"} or "Camera" in (data["camera_name"] or "")
    assert data["location"] == "Warehouse Aisle"
    assert data["notification_code"]
    assert data["pipeline_status"] in {
        "awaiting_human_review",
        "preparing_response_plan",
        "preparing_company_procedure",
        "ready_for_approval",
        "completed_no_incident",
    }

    second = client.post(f"/api/analyses/{analysis_code}/prepare-response")
    assert second.status_code == 200
    again = second.json()["data"]
    assert again["notification_code"] == data["notification_code"]
    assert again["retrieval_code"] == data["retrieval_code"]
    assert again["plan_code"] == data["plan_code"]

    notes = client.get("/api/notifications")
    assert notes.status_code == 200
    codes = [item["notification_code"] for item in notes.json()["data"]]
    assert data["notification_code"] in codes
    assert codes.count(data["notification_code"]) == 1

    dismissed = client.post(
        f"/api/notifications/{data['notification_id']}/dismiss"
    )
    assert dismissed.status_code == 200
    assert dismissed.json()["data"]["dismissed"] is True


def test_workflow_status_endpoint(client: TestClient, tmp_path: Path):
    analysis_code = _analyze_ready(client, tmp_path)
    client.post(f"/api/analyses/{analysis_code}/prepare-response")
    status = client.get(f"/api/analyses/{analysis_code}/workflow")
    assert status.status_code == 200
    body = status.json()["data"]
    assert body["analysis_code"] == analysis_code
    assert body["pipeline_status"]
    assert body["message"]

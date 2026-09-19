from __future__ import annotations

import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import make_test_video


def _ready_plan(client: TestClient, tmp_path: Path) -> str:
    video_path = make_test_video(tmp_path / "fall.mp4", frames=40, fps=8)
    with video_path.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            files={"file": ("fall.mp4", handle, "video/mp4")},
            data={"location": "Loading Zone B"},
        ).json()["data"]

    deadline = time.time() + 20
    while time.time() < deadline:
        job = client.get(f"/api/processing-jobs/{uploaded['job_code']}").json()["data"]
        if job["status"] == "completed":
            break
        if job["status"] == "failed":
            raise AssertionError(job)
        time.sleep(0.05)
    else:
        raise AssertionError("processing timed out")

    analysis_code = client.post(
        f"/api/videos/{uploaded['asset_code']}/analyze"
    ).json()["data"]["analysis_code"]
    deadline = time.time() + 20
    while time.time() < deadline:
        analysis = client.get(f"/api/analyses/{analysis_code}").json()["data"]
        if analysis["status"] in {"completed", "needs_review"}:
            break
        if analysis["status"] == "failed":
            raise AssertionError(analysis)
        time.sleep(0.05)
    else:
        raise AssertionError("analysis timed out")

    client.post(f"/api/analyses/{analysis_code}/retrieve-procedures", json={})
    plan = client.post(f"/api/analyses/{analysis_code}/response-plan", json={})
    assert plan.status_code == 201, plan.text
    data = plan.json()["data"]
    assert data["status"] == "completed"
    return data["plan_code"]


def test_approve_execute_idempotent_and_report(client: TestClient, tmp_path: Path):
    plan_code = _ready_plan(client, tmp_path)
    plan = client.get(f"/api/response-plans/{plan_code}").json()["data"]
    action_ids = [action["id"] for action in plan["actions"]]
    assert action_ids

    # Cannot execute before approval.
    blocked = client.post(
        f"/api/response-plans/{plan_code}/execute",
        json={"confirmed": True},
    )
    assert blocked.status_code == 409

    # Confirmation required for approval.
    unconfirmed = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "selected_action_ids": action_ids,
            "confirmed": False,
            "reviewer_name": "Yug Supervisor",
        },
    )
    assert unconfirmed.status_code == 422

    approved = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "selected_action_ids": action_ids,
            "confirmed": True,
            "reviewer_name": "Yug Supervisor",
            "notes": "Demo approval for Stage 6",
            "incident_identifier": "INC-2026-0042",
        },
    )
    assert approved.status_code == 200, approved.text
    approval = approved.json()["data"]
    assert approval["status"] == "approved"
    assert approval["reviewer_name"] == "Yug Supervisor"
    assert set(approval["selected_action_ids"]) == set(action_ids)

    # Double approval blocked.
    again = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "selected_action_ids": action_ids,
            "confirmed": True,
            "reviewer_name": "Yug Supervisor",
        },
    )
    assert again.status_code == 409

    executed = client.post(
        f"/api/response-plans/{plan_code}/execute",
        json={"confirmed": True},
    )
    assert executed.status_code == 200, executed.text
    payload = executed.json()["data"]
    assert payload["simulation"] is True
    assert payload["execution_status"] in {"executed", "partially_failed"}
    assert len(payload["executions"]) == len(action_ids)
    for item in payload["executions"]:
        assert item["simulation"] is True
        assert "Simulated" in item["message"] or "simulated" in item["message"].lower()

    # Idempotent repeat.
    repeated = client.post(
        f"/api/response-plans/{plan_code}/execute",
        json={"confirmed": True},
    )
    assert repeated.status_code == 200
    assert len(repeated.json()["data"]["executions"]) == len(payload["executions"])
    assert "idempotent" in repeated.json()["data"]["message"].lower()

    audit = client.get("/api/incidents/INC-2026-0042/audit")
    assert audit.status_code == 200
    events = audit.json()["data"]
    types = [event["event_type"] for event in events]
    assert "plan_approved" in types or "plan_partially_approved" in types
    assert "execution_requested" in types
    assert all(event["simulation"] is True for event in events)

    report = client.post(
        "/api/incidents/INC-2026-0042/reports",
        json={"plan_identifier": plan_code},
    )
    assert report.status_code == 201, report.text
    report_data = report.json()["data"]
    assert report_data["simulation"] is True
    assert report_data["download_url"]

    download = client.get(f"/api/reports/{report_data['report_code']}/download")
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("application/pdf")
    assert download.content[:4] == b"%PDF"


def test_partial_approval_and_rejection(client: TestClient, tmp_path: Path):
    plan_code = _ready_plan(client, tmp_path)
    plan = client.get(f"/api/response-plans/{plan_code}").json()["data"]
    first = plan["actions"][0]["id"]

    partial = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "selected_action_ids": [first],
            "confirmed": True,
            "reviewer_name": "demo-reviewer",
            "incident_identifier": "INC-2026-0042",
        },
    )
    assert partial.status_code == 200
    assert partial.json()["data"]["status"] == "partially_approved"

    executed = client.post(
        f"/api/response-plans/{plan_code}/execute",
        json={"confirmed": True},
    )
    assert executed.status_code == 200
    assert len(executed.json()["data"]["executions"]) == 1

    # New plan for rejection path.
    plan_code_2 = _ready_plan(client, tmp_path)
    rejected = client.post(
        f"/api/response-plans/{plan_code_2}/reject",
        json={"reviewer_name": "demo-reviewer", "reason": "Not needed"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rejected"
    blocked = client.post(
        f"/api/response-plans/{plan_code_2}/execute",
        json={"confirmed": True},
    )
    assert blocked.status_code == 409


def test_invalid_action_selection_and_insufficient_plan(
    client: TestClient, tmp_path: Path, db_session: Session
):
    from app.models.procedure import SafetyProcedure

    plan_code = _ready_plan(client, tmp_path)
    bad = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "selected_action_ids": ["not-a-real-action"],
            "confirmed": True,
            "reviewer_name": "demo-reviewer",
        },
    )
    assert bad.status_code == 422

    # Force insufficient policy plan.
    for procedure in db_session.query(SafetyProcedure).all():
        procedure.is_active = False
    db_session.commit()

    video_path = make_test_video(tmp_path / "other.mp4", frames=24, fps=8)
    with video_path.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            files={"file": ("other.mp4", handle, "video/mp4")},
            data={"location": "Loading Zone B"},
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
    plan = client.post(f"/api/analyses/{analysis_code}/response-plan", json={}).json()["data"]
    assert plan["status"] == "insufficient_policy"
    denied = client.post(
        f"/api/response-plans/{plan['plan_code']}/approve",
        json={
            "selected_action_ids": ["x"],
            "confirmed": True,
            "reviewer_name": "demo-reviewer",
        },
    )
    assert denied.status_code == 409


def test_simulated_failure_and_retry(client: TestClient, tmp_path: Path, db_session: Session):
    from app.services import approval_execution as approval_service

    plan_code = _ready_plan(client, tmp_path)
    plan = client.get(f"/api/response-plans/{plan_code}").json()["data"]
    action_ids = [action["id"] for action in plan["actions"]]
    fail_id = action_ids[0]

    client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "selected_action_ids": action_ids[:1],
            "confirmed": True,
            "reviewer_name": "demo-reviewer",
            "incident_identifier": "INC-2026-0042",
        },
    )

    result = approval_service.execute_plan(
        db_session,
        plan_code,
        fail_action_ids={fail_id},
    )
    assert result.executions[0].status.value == "failed"
    assert result.executions[0].simulation is True
    execution_code = result.executions[0].execution_code

    retried = approval_service.retry_execution(
        db_session,
        execution_code,
        fail_action_ids=set(),
    )
    assert retried.status.value == "completed"
    assert retried.attempt_number >= 2

    again = client.post(f"/api/executions/{execution_code}/retry")
    assert again.status_code == 409

"""PPE-compliance workflow tests — preserve person-down regression coverage."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.schemas import AnalysisEvidenceItem, IncidentAnalysisResult
from app.core.enums import AnalysisSeverity
from app.core.incident_types import (
    normalize_incident_type,
    is_ppe_incident,
    is_person_down_incident,
)
from app.models.ppe_policy import CameraPpePolicy
from app.services.retrieval import build_query_text, retrieve_chunks
from tests.conftest import make_test_video


def _wait_job(client: TestClient, job_code: str, timeout: float = 25.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        job = client.get(f"/api/processing-jobs/{job_code}").json()["data"]
        if job["status"] in {"completed", "failed"}:
            return job
        time.sleep(0.05)
    raise AssertionError(f"processing timed out for {job_code}")


def _wait_analysis(client: TestClient, analysis_code: str, timeout: float = 25.0) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        analysis = client.get(f"/api/analyses/{analysis_code}").json()["data"]
        if analysis["status"] in {"completed", "needs_review", "failed"}:
            return analysis
        time.sleep(0.05)
    raise AssertionError(f"analysis timed out for {analysis_code}")


def _upload_and_analyze(
    client: TestClient,
    tmp_path: Path,
    *,
    camera_id: str,
    location: str,
    demo_scenario: str,
    demo_ppe_observation: str | None = None,
    filename: str = "clip.mp4",
) -> tuple[dict, dict]:
    video_path = make_test_video(tmp_path / filename, frames=40, fps=8)
    data = {
        "location": location,
        "camera_id": camera_id,
        "demo_scenario": demo_scenario,
    }
    if demo_ppe_observation:
        data["demo_ppe_observation"] = demo_ppe_observation
    with video_path.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            files={"file": (filename, handle, "video/mp4")},
            data=data,
        ).json()["data"]
    job = _wait_job(client, uploaded["job_code"])
    assert job["status"] == "completed", job

    analyze = client.post(f"/api/videos/{uploaded['asset_code']}/analyze")
    assert analyze.status_code in {200, 202}, analyze.text
    analysis_code = analyze.json()["data"]["analysis_code"]
    analysis = _wait_analysis(client, analysis_code)
    assert analysis["status"] in {"completed", "needs_review"}, analysis
    return uploaded, analysis


def test_camera_ppe_requirements_seeded(client: TestClient, db_session: Session):
    policies = client.get("/api/ppe-policies")
    assert policies.status_code == 200
    rows = policies.json()["data"]
    by_camera = {row["camera_id"]: row for row in rows}
    assert "cam-04" in by_camera
    assert "cam-02" in by_camera
    assert set(by_camera["cam-04"]["required_ppe"]) == {
        "hard_hat",
        "high_visibility_vest",
    }
    assert by_camera["cam-04"]["procedure_code"] == "SOP-PPE-3.4"
    assert by_camera["cam-04"]["is_active"] is True

    entrance = client.get("/api/cameras/cam-01/ppe-policy")
    assert entrance.status_code == 404

    floor = client.get("/api/cameras/cam-04/ppe-policy")
    assert floor.status_code == 200
    assert floor.json()["data"]["zone_label"] == "Production Floor"

    from sqlalchemy import select

    db_count = len(db_session.scalars(select(CameraPpePolicy)).all())
    assert db_count >= 2


def test_canonical_incident_type_mapping():
    assert normalize_incident_type("ppe_violation") == "ppe_noncompliance"
    assert normalize_incident_type("PPE Non-Compliance") == "ppe_noncompliance"
    assert normalize_incident_type("person_down") == "possible_person_down"
    assert is_ppe_incident("ppe_violation")
    assert is_ppe_incident("ppe_noncompliance")
    assert not is_person_down_incident("ppe_noncompliance")
    assert is_person_down_incident("possible_person_down")
    assert not is_ppe_incident("possible_person_down")


def test_configured_ppe_demo_result(client: TestClient, tmp_path: Path):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-04",
        location="Production Floor",
        demo_scenario="ppe_compliance",
        demo_ppe_observation="hard_hat_not_visible",
        filename="ppe.mp4",
    )
    assert analysis["incident_detected"] is True
    assert analysis["incident_type"] == "ppe_noncompliance"
    assert analysis["analysis_mode"] == "configured_demo"
    assert analysis["confidence"] is None
    assert "hard_hat" in analysis["possibly_missing_ppe"]
    assert "hard_hat" in analysis["required_ppe"]
    assert "high_visibility_vest" in analysis["required_ppe"]
    assert analysis["human_review_required"] is True
    assert "configured" in (analysis["summary"] or "").lower()


def test_no_ppe_inference_without_camera_policy(client: TestClient, tmp_path: Path):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-01",
        location="Main Entrance",
        demo_scenario="ppe_compliance",
        demo_ppe_observation="hard_hat_not_visible",
        filename="entrance.mp4",
    )
    assert analysis["incident_detected"] is False
    assert analysis["incident_type"] in {"no_incident", "insufficient_evidence"}
    assert analysis["possibly_missing_ppe"] == []


def test_real_provider_schema_validation_and_insufficient_evidence():
    valid = IncidentAnalysisResult(
        incident_detected=True,
        incident_type="ppe_noncompliance",
        summary="Hard hat is not visible in the selected evidence.",
        detailed_analysis="Worker torso visible; hard hat not clearly visible.",
        severity=AnalysisSeverity.MEDIUM,
        confidence=0.62,
        evidence=[
            AnalysisEvidenceItem(
                frame_id="frm-1",
                timestamp_seconds=1.2,
                observation="Hard hat is not visible in the selected evidence.",
                relevance="supporting",
            )
        ],
        required_ppe=["hard_hat", "high_visibility_vest"],
        observed_ppe=["high_visibility_vest"],
        possibly_missing_ppe=["hard_hat"],
        analysis_mode="multimodal",
        human_review_required=True,
    )
    assert valid.incident_type == "ppe_noncompliance"

    insufficient = IncidentAnalysisResult(
        incident_detected=False,
        incident_type="insufficient_evidence",
        summary="Angle and occlusion prevent a reliable PPE determination.",
        detailed_analysis="Worker is partially occluded; PPE cannot be confirmed.",
        severity=AnalysisSeverity.NONE,
        confidence=0.2,
        evidence=[],
        inconclusive=True,
        analysis_mode="multimodal",
        human_review_required=False,
    )
    assert insufficient.inconclusive is True

    with pytest.raises(Exception):
        IncidentAnalysisResult(
            incident_detected=True,
            incident_type="ppe_noncompliance",
            summary="",
            detailed_analysis="x",
            severity=AnalysisSeverity.MEDIUM,
            confidence=0.5,
            analysis_mode="multimodal",
        )


def test_one_notification_per_ppe_analysis(client: TestClient, tmp_path: Path):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-04",
        location="Production Floor",
        demo_scenario="ppe_compliance",
        demo_ppe_observation="both_not_visible",
        filename="ppe-note.mp4",
    )
    first = client.post(f"/api/analyses/{analysis['analysis_code']}/prepare-response")
    assert first.status_code == 200, first.text
    note_code = first.json()["data"]["notification_code"]
    assert note_code

    second = client.post(f"/api/analyses/{analysis['analysis_code']}/prepare-response")
    assert second.status_code == 200
    assert second.json()["data"]["notification_code"] == note_code

    notes = client.get("/api/notifications").json()["data"]
    matching = [n for n in notes if n["notification_code"] == note_code]
    assert len(matching) == 1
    assert "PPE" in matching[0]["title"]
    assert matching[0]["confidence"] is None


def test_ppe_retrieval_selects_ppe_sop(client: TestClient, tmp_path: Path, db_session: Session):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-04",
        location="Production Floor",
        demo_scenario="ppe_compliance",
        demo_ppe_observation="hard_hat_not_visible",
        filename="ppe-ret.mp4",
    )
    prepared = client.post(f"/api/analyses/{analysis['analysis_code']}/prepare-response")
    assert prepared.status_code == 200, prepared.text
    workflow = prepared.json()["data"]
    assert workflow["retrieval_code"]
    assert workflow["plan_code"]

    query = build_query_text(
        incident_type="ppe_noncompliance",
        title="ppe_noncompliance",
        summary="Configured PPE demo: hard hat not visible",
        severity="medium",
        location="Production Floor",
        evidence_descriptions=["hard hat not visible"],
    )
    ranked = retrieve_chunks(db_session, query_text=query)
    assert ranked
    top_codes = [item.procedure.procedure_code for item in ranked[:3]]
    assert any(code.startswith("SOP-PPE") for code in top_codes)
    assert not any(code.startswith("SOP-FALL") for code in top_codes[:1])


def test_ppe_plan_uses_verified_citations_and_blocks_before_confirm(
    client: TestClient, tmp_path: Path
):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-04",
        location="Production Floor",
        demo_scenario="ppe_compliance",
        demo_ppe_observation="high_visibility_vest_not_visible",
        filename="ppe-plan.mp4",
    )
    prepared = client.post(f"/api/analyses/{analysis['analysis_code']}/prepare-response")
    assert prepared.status_code == 200, prepared.text
    plan_code = prepared.json()["data"]["plan_code"]
    assert plan_code

    plan = client.get(f"/api/response-plans/{plan_code}").json()["data"]
    assert plan["status"] == "completed"
    assert plan["actions"]
    for action in plan["actions"]:
        assert action["citations"], action
        assert all(
            (c.get("procedure_code") or "").startswith("SOP-PPE")
            for c in action["citations"]
        )
        assert "medical" not in action["title"].lower()
        assert "emergency" not in action["title"].lower()

    blocked = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "reviewer_name": "Test Reviewer",
            "selected_action_ids": [plan["actions"][0]["id"]],
            "notes": "should be blocked",
            "confirmed": True,
        },
    )
    assert blocked.status_code in {400, 409}, blocked.text


def test_ppe_execution_idempotency_and_report(client: TestClient, tmp_path: Path):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-04",
        location="Production Floor",
        demo_scenario="ppe_compliance",
        demo_ppe_observation="hard_hat_not_visible",
        filename="ppe-exec.mp4",
    )
    prepared = client.post(f"/api/analyses/{analysis['analysis_code']}/prepare-response")
    workflow = prepared.json()["data"]
    plan_code = workflow["plan_code"]
    incident_code = workflow["incident_code"]
    assert plan_code and incident_code

    review = client.post(
        f"/api/analyses/{analysis['analysis_code']}/review",
        json={
            "decision": "confirmed",
            "reviewer_name": "PPE Supervisor",
            "notes": "Confirmed PPE noncompliance for demo",
        },
    )
    assert review.status_code == 200, review.text

    plan = client.get(f"/api/response-plans/{plan_code}").json()["data"]
    action_ids = [a["id"] for a in plan["actions"]]
    approved = client.post(
        f"/api/response-plans/{plan_code}/approve",
        json={
            "reviewer_name": "PPE Supervisor",
            "selected_action_ids": action_ids,
            "notes": "Approve simulated PPE actions",
            "confirmed": True,
        },
    )
    assert approved.status_code == 200, approved.text

    first_exec = client.post(
        f"/api/response-plans/{plan_code}/execute",
        json={"confirmed": True},
    )
    assert first_exec.status_code == 200, first_exec.text
    second_exec = client.post(
        f"/api/response-plans/{plan_code}/execute",
        json={"confirmed": True},
    )
    assert second_exec.status_code == 200, second_exec.text

    execs = client.get(f"/api/response-plans/{plan_code}/executions").json()["data"]
    assert execs
    assert all(item.get("simulation") is True for item in execs)

    report = client.post(
        f"/api/incidents/{incident_code}/reports",
        json={"plan_identifier": plan_code},
    )
    assert report.status_code in {200, 201}, report.text
    report_body = report.json()["data"]
    summary = report_body.get("summary") or {}
    analysis_summary = summary.get("analysis") or {}
    assert analysis_summary.get("incident_type") == "ppe_noncompliance"
    assert "hard_hat" in (analysis_summary.get("required_ppe") or [])
    assert "hard_hat" in (analysis_summary.get("possibly_missing_ppe") or [])
    cite_codes = {
        c.get("procedure_code")
        for action in (summary.get("actions") or [])
        for c in (action.get("citations") or [])
    }
    assert any(code and code.startswith("SOP-PPE") for code in cite_codes)
    procedure = summary.get("procedure") or {}
    assert (procedure.get("procedure_code") or "").startswith("SOP-PPE")
    assert not any(
        code and code.startswith("SOP-FALL") for code in cite_codes
    )
    assert all(
        item.get("simulation") is True
        for item in (summary.get("executions") or [])
    )


def test_person_down_regression(client: TestClient, tmp_path: Path):
    _, analysis = _upload_and_analyze(
        client,
        tmp_path,
        camera_id="cam-03",
        location="Warehouse Aisle",
        demo_scenario="person_down",
        filename="fall.mp4",
    )
    assert analysis["incident_detected"] is True
    assert analysis["incident_type"] in {
        "possible_person_down",
        "person_down",
    }
    assert analysis["analysis_mode"] != "configured_demo"

    prepared = client.post(f"/api/analyses/{analysis['analysis_code']}/prepare-response")
    assert prepared.status_code == 200, prepared.text
    workflow = prepared.json()["data"]
    assert workflow["notification_code"]
    assert workflow["plan_code"]

    plan = client.get(f"/api/response-plans/{workflow['plan_code']}").json()["data"]
    cite_codes = {
        c.get("procedure_code")
        for action in plan["actions"]
        for c in action["citations"]
    }
    assert any(code and code.startswith("SOP-FALL") for code in cite_codes)
    assert not any(code and code.startswith("SOP-PPE") for code in cite_codes)

    notes = client.get("/api/notifications").json()["data"]
    titles = [n["title"] for n in notes if n["notification_code"] == workflow["notification_code"]]
    assert titles
    assert "PPE" not in titles[0]

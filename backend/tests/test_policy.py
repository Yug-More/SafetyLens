from __future__ import annotations

import io
import time
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.enums import AnalysisStatus
from app.models.incident_analysis import IncidentAnalysis
from tests.conftest import make_test_video


def _ready_video_and_analysis(client: TestClient, tmp_path: Path) -> str:
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
        raise AssertionError("video processing timed out")

    started = client.post(f"/api/videos/{uploaded['asset_code']}/analyze").json()["data"]
    deadline = time.time() + 20
    while time.time() < deadline:
        analysis = client.get(f"/api/analyses/{started['analysis_code']}").json()["data"]
        if analysis["status"] in {"completed", "needs_review"}:
            return started["analysis_code"]
        if analysis["status"] == "failed":
            raise AssertionError(analysis)
        time.sleep(0.05)
    raise AssertionError("analysis timed out")


def _make_simple_pdf(text: str) -> bytes:
    """Build a minimal PDF containing extractable text."""
    content = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 40 700 Td ({content}) Tj ET"
    stream_bytes = stream.encode("latin-1", errors="replace")
    objects = []
    objects.append(b"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n")
    objects.append(b"2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj\n")
    objects.append(
        b"3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources<< /Font<< /F1 5 0 R >> >> >>endobj\n"
    )
    objects.append(
        b"4 0 obj<< /Length "
        + str(len(stream_bytes)).encode()
        + b" >>stream\n"
        + stream_bytes
        + b"\nendstream\nendobj\n"
    )
    objects.append(b"5 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(out))
        out.extend(obj)
    xref_pos = len(out)
    out.extend(f"xref\n0 {len(offsets)}\n".encode())
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode())
    out.extend(
        f"trailer<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode()
    )
    return bytes(out)


def test_upload_txt_markdown_and_pdf(client: TestClient):
    txt = client.post(
        "/api/procedures/upload",
        files={
            "file": (
                "site-rule.txt",
                io.BytesIO(b"1. Lock out equipment.\n2. Verify zero energy.\n"),
                "text/plain",
            )
        },
        data={
            "procedure_code": "SOP-LOTO-1.0",
            "title": "Lockout Tagout",
            "category": "Maintenance",
            "version": "1.0",
        },
    )
    assert txt.status_code == 201, txt.text
    assert txt.json()["data"]["chunk_count"] >= 1

    md = client.post(
        "/api/procedures/upload",
        files={
            "file": (
                "spill.md",
                io.BytesIO(b"# Spill Response\n\n1. Contain the spill.\n2. Notify EHS.\n"),
                "text/markdown",
            )
        },
        data={
            "procedure_code": "SOP-SPILL-1.0",
            "title": "Spill Response",
            "category": "Environmental",
            "version": "1.0",
        },
    )
    assert md.status_code == 201, md.text

    pdf_bytes = _make_simple_pdf(
        "Notify supervisor for medical assessment and preserve footage."
    )
    pdf = client.post(
        "/api/procedures/upload",
        files={"file": ("fall-notes.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        data={
            "procedure_code": "SOP-PDF-1.0",
            "title": "PDF Notes",
            "category": "Emergency Response",
            "version": "1.0",
        },
    )
    assert pdf.status_code == 201, pdf.text


def test_upload_rejects_bad_inputs(client: TestClient):
    bad_type = client.post(
        "/api/procedures/upload",
        files={"file": ("x.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        data={
            "procedure_code": "SOP-X",
            "title": "Bad",
            "category": "X",
            "version": "1",
        },
    )
    assert bad_type.status_code == 415

    empty = client.post(
        "/api/procedures/upload",
        files={"file": ("empty.txt", io.BytesIO(b""), "text/plain")},
        data={
            "procedure_code": "SOP-EMPTY",
            "title": "Empty",
            "category": "X",
            "version": "1",
        },
    )
    assert empty.status_code == 422

    traversal = client.post(
        "/api/procedures/upload",
        files={
            "file": (
                "../../etc/passwd.txt",
                io.BytesIO(b"1. Keep area clear.\n"),
                "text/plain",
            )
        },
        data={
            "procedure_code": "SOP-TRAV",
            "title": "Trav",
            "category": "X",
            "version": "1",
        },
    )
    assert traversal.status_code in {201, 422, 409}
    if traversal.status_code == 201:
        assert ".." not in traversal.json()["data"]["source_filename"]

    corrupt = client.post(
        "/api/procedures/upload",
        files={"file": ("bad.pdf", io.BytesIO(b"%PDF-1.4 corrupt"), "application/pdf")},
        data={
            "procedure_code": "SOP-BADPDF",
            "title": "Bad PDF",
            "category": "X",
            "version": "1",
        },
    )
    assert corrupt.status_code == 422
    assert corrupt.json()["error"]["code"] in {
        "CORRUPT_DOCUMENT",
        "EMPTY_DOCUMENT",
        "UNREADABLE_DOCUMENT",
    }


def test_duplicate_ingestion_rejected(client: TestClient):
    payload = {
        "procedure_code": "SOP-DUP-1.0",
        "title": "Duplicate Test",
        "category": "General",
        "version": "1.0",
    }
    body = b"## Section\n1. Do the safe thing.\n2. Document the event.\n"
    first = client.post(
        "/api/procedures/upload",
        files={"file": ("dup.txt", io.BytesIO(body), "text/plain")},
        data=payload,
    )
    assert first.status_code == 201
    second = client.post(
        "/api/procedures/upload",
        files={"file": ("dup.txt", io.BytesIO(body), "text/plain")},
        data=payload,
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "DUPLICATE_PROCEDURE"


def test_oversized_procedure_rejected(client: TestClient, monkeypatch):
    from app.core.config import get_settings

    monkeypatch.setenv("MAX_PROCEDURE_SIZE_MB", "1")
    get_settings.cache_clear()
    huge = b"a" * (1024 * 1024 + 10)
    response = client.post(
        "/api/procedures/upload",
        files={"file": ("huge.txt", io.BytesIO(huge), "text/plain")},
        data={
            "procedure_code": "SOP-HUGE",
            "title": "Huge",
            "category": "X",
            "version": "1",
        },
    )
    assert response.status_code == 413
    get_settings.cache_clear()


def test_fall_retrieval_and_response_plan(client: TestClient, tmp_path: Path):
    analysis_code = _ready_video_and_analysis(client, tmp_path)

    retrieval = client.post(
        f"/api/analyses/{analysis_code}/retrieve-procedures", json={}
    )
    assert retrieval.status_code == 200, retrieval.text
    data = retrieval.json()["data"]
    assert data["method"] == "lexical"
    assert data["status"] == "completed"
    assert data["match_count"] >= 1
    codes = {item["procedure_code"] for item in data["matches"]}
    assert "SOP-FALL-4.2" in codes
    for match in data["matches"]:
        assert match["excerpt"]
        assert match["chunk_id"]
        assert match["score"] > 0

    plan = client.post(
        f"/api/analyses/{analysis_code}/response-plan",
        json={"retrieval_id": data["retrieval_code"]},
    )
    assert plan.status_code == 201, plan.text
    plan_data = plan.json()["data"]
    assert plan_data["status"] == "completed"
    assert plan_data["recommendations_executed"] is False
    assert plan_data["is_demo"] is True
    assert "Demo" in plan_data["provider_label"]
    assert len(plan_data["actions"]) >= 5
    for action in plan_data["actions"]:
        assert action["requires_human_approval"] is True
        if action["is_policy_grounded"]:
            assert len(action["citations"]) >= 1
            for cite in action["citations"]:
                assert cite["excerpt"]
                assert cite["chunk_id"]

    fetched = client.get(f"/api/response-plans/{plan_data['plan_code']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["plan_code"] == plan_data["plan_code"]


def test_insufficient_retrieval_and_policy(
    client: TestClient, db_session: Session, tmp_path: Path
):
    from app.models.procedure import SafetyProcedure

    analysis_code = _ready_video_and_analysis(client, tmp_path)
    for procedure in db_session.query(SafetyProcedure).all():
        procedure.is_active = False
    db_session.commit()

    retrieval = client.post(
        f"/api/analyses/{analysis_code}/retrieve-procedures",
        json={"query": "zzzz-no-match-token"},
    )
    assert retrieval.status_code == 200
    assert retrieval.json()["data"]["status"] == "insufficient"

    plan = client.post(f"/api/analyses/{analysis_code}/response-plan", json={})
    assert plan.status_code == 201
    assert plan.json()["data"]["status"] == "insufficient_policy"
    assert plan.json()["data"]["actions"] == []


def test_failed_analysis_rejected(
    client: TestClient, db_session: Session, tmp_path: Path
):
    analysis_code = _ready_video_and_analysis(client, tmp_path)
    row = (
        db_session.query(IncidentAnalysis)
        .filter_by(analysis_code=analysis_code)
        .one()
    )
    row.status = AnalysisStatus.FAILED.value
    db_session.commit()

    response = client.post(
        f"/api/analyses/{analysis_code}/retrieve-procedures", json={}
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ANALYSIS_FAILED"


def test_citation_verification_rejects_unknown_chunk(
    client: TestClient, tmp_path: Path, monkeypatch
):
    analysis_code = _ready_video_and_analysis(client, tmp_path)
    retrieval = client.post(
        f"/api/analyses/{analysis_code}/retrieve-procedures", json={}
    ).json()["data"]

    from app.core.enums import ActionPriority
    from app.services.planner import PlannedActionDraft, ResponsePlanDraft

    class BadPlanner:
        name = "demo"
        is_demo = True
        is_simulated = True
        model = "bad"

        def generate(self, **_kwargs):
            return ResponsePlanDraft(
                status="completed",
                summary="bad",
                rationale="bad",
                actions=[
                    PlannedActionDraft(
                        title="Invented",
                        description="Should fail",
                        priority=ActionPriority.HIGH,
                        responsible_role="Nobody",
                        requires_human_approval=True,
                        is_policy_grounded=True,
                        citation_chunk_ids=["does-not-exist"],
                    )
                ],
                limitations=[],
                provider_name="demo",
                provider_model="bad",
                is_demo=True,
                is_simulated=True,
            )

    monkeypatch.setattr(
        "app.services.procedures.get_response_planner",
        lambda settings=None: BadPlanner(),
    )
    response = client.post(
        f"/api/analyses/{analysis_code}/response-plan",
        json={"retrieval_id": retrieval["id"]},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_CITATION"


def test_planner_failure_persists_failed_plan(
    client: TestClient, tmp_path: Path, monkeypatch
):
    analysis_code = _ready_video_and_analysis(client, tmp_path)

    class BoomPlanner:
        name = "demo"
        is_demo = True
        is_simulated = True
        model = "boom"

        def generate(self, **_kwargs):
            raise RuntimeError("provider down")

    monkeypatch.setattr(
        "app.services.procedures.get_response_planner",
        lambda settings=None: BoomPlanner(),
    )
    response = client.post(f"/api/analyses/{analysis_code}/response-plan", json={})
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "failed"
    assert response.json()["data"]["error_code"] == "PLANNER_FAILED"

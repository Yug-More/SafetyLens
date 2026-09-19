from __future__ import annotations

import time

from fastapi.testclient import TestClient

from tests.conftest import make_test_video


def _upload_ready_video(client: TestClient, tmp_path) -> dict:
    video_path = make_test_video(tmp_path / "clip.mp4", frames=32, fps=8)
    with video_path.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            files={"file": ("clip.mp4", handle, "video/mp4")},
            data={"location": "Loading Zone B"},
        )
    assert response.status_code == 202, response.text
    payload = response.json()["data"]

    deadline = time.time() + 20
    while time.time() < deadline:
        job = client.get(f"/api/processing-jobs/{payload['job_code']}")
        assert job.status_code == 200
        status = job.json()["data"]["status"]
        if status == "completed":
            break
        if status == "failed":
            raise AssertionError(job.json())
        time.sleep(0.1)
    else:
        raise AssertionError("processing timed out")

    video = client.get(f"/api/videos/{payload['asset_code']}")
    assert video.status_code == 200
    assert video.json()["data"]["status"] == "ready"
    return payload


def test_ai_provider_info_defaults_to_demo(client: TestClient):
    response = client.get("/api/ai/provider")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["provider_name"] == "demo"
    assert data["is_demo"] is True
    assert data["is_simulated"] is True
    assert "Demo" in data["label"]


def test_analyze_requires_ready_video(client: TestClient, tmp_path):
    video_path = make_test_video(tmp_path / "early.mp4", frames=16, fps=8)
    with video_path.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            files={"file": ("early.mp4", handle, "video/mp4")},
            data={"location": "Aisle 3"},
        ).json()["data"]

    # Immediately request analysis — should conflict while still processing/uploaded.
    response = client.post(f"/api/videos/{uploaded['asset_code']}/analyze")
    assert response.status_code in {409, 202}
    if response.status_code == 409:
        assert response.json()["error"]["code"] in {
            "VIDEO_NOT_READY",
            "FRAMES_REQUIRED",
        }


def test_demo_analysis_produces_structured_result(client: TestClient, tmp_path):
    uploaded = _upload_ready_video(client, tmp_path)

    response = client.post(f"/api/videos/{uploaded['asset_code']}/analyze")
    assert response.status_code == 202, response.text
    started = response.json()["data"]
    assert started["provider_name"] == "demo"
    assert started["is_demo"] is True
    assert started["is_simulated"] is True
    analysis_code = started["analysis_code"]

    deadline = time.time() + 20
    analysis = None
    while time.time() < deadline:
        result = client.get(f"/api/analyses/{analysis_code}")
        assert result.status_code == 200
        analysis = result.json()["data"]
        if analysis["status"] in {"completed", "needs_review", "failed"}:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("analysis timed out")

    assert analysis is not None
    assert analysis["status"] in {"completed", "needs_review"}
    assert analysis["error_code"] is None
    assert analysis["summary"]
    assert analysis["detailed_analysis"]
    assert analysis["provider_label"]
    assert analysis["human_approval_required"] is True
    assert isinstance(analysis["evidence"], list)
    assert len(analysis["evidence"]) >= 1
    for item in analysis["evidence"]:
        assert item["frame_code"]
        assert item["timestamp_seconds"] >= 0
        assert item["observation"]
        assert item["content_url"].startswith("/api/frames/")

    listed = client.get(f"/api/videos/{uploaded['asset_code']}/analyses")
    assert listed.status_code == 200
    codes = [row["analysis_code"] for row in listed.json()["data"]]
    assert analysis_code in codes


def test_human_review_can_be_saved(client: TestClient, tmp_path):
    uploaded = _upload_ready_video(client, tmp_path)
    started = client.post(f"/api/videos/{uploaded['asset_code']}/analyze").json()["data"]
    analysis_code = started["analysis_code"]

    deadline = time.time() + 20
    while time.time() < deadline:
        analysis = client.get(f"/api/analyses/{analysis_code}").json()["data"]
        if analysis["status"] in {"completed", "needs_review"}:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("analysis timed out")

    review = client.post(
        f"/api/analyses/{analysis_code}/review",
        json={
            "decision": "confirmed",
            "reviewer_name": "Yug Reviewer",
            "notes": "Confirmed person-down for demo rehearsal.",
        },
    )
    assert review.status_code == 200, review.text
    payload = review.json()["data"]
    assert payload["review"]["decision"] == "confirmed"
    assert payload["review"]["reviewer_name"] == "Yug Reviewer"
    assert "Confirmed" in (payload["review"]["notes"] or "")


def test_duplicate_active_analysis_rejected(client: TestClient, tmp_path, monkeypatch):
    # Stall analysis so the auto pipeline leaves an active analysis after upload.
    monkeypatch.setattr(
        "app.services.analysis.run_analysis_job",
        lambda *_args, **_kwargs: None,
    )
    uploaded = _upload_ready_video(client, tmp_path)

    first = client.post(f"/api/videos/{uploaded['asset_code']}/analyze")
    assert first.status_code == 202
    first_code = first.json()["data"]["analysis_code"]

    # Idempotent retry reuses the active analysis.
    second = client.post(f"/api/videos/{uploaded['asset_code']}/analyze")
    assert second.status_code == 202
    assert second.json()["data"]["analysis_code"] == first_code

    # Forced new analysis is blocked while one is active.
    forced = client.post(
        f"/api/videos/{uploaded['asset_code']}/analyze?force_new=true"
    )
    assert forced.status_code == 409
    assert forced.json()["error"]["code"] == "ANALYSIS_IN_PROGRESS"


def test_openai_provider_is_mocked_and_validated(client: TestClient, tmp_path, monkeypatch):
    from app.ai.schemas import AnalysisEvidenceItem, IncidentAnalysisResult
    from app.core.config import get_settings
    from app.core.enums import AnalysisSeverity

    uploaded = _upload_ready_video(client, tmp_path)

    class FakeOpenAIProvider:
        name = "openai"
        is_demo = False
        is_simulated = False

        def analyze_frames(self, **kwargs):
            frames = kwargs["frames"]
            first = frames[0]
            return IncidentAnalysisResult(
                incident_detected=True,
                incident_type="possible_person_down",
                summary="Mocked OpenAI summary",
                detailed_analysis="Mocked detailed analysis from fake provider.",
                severity=AnalysisSeverity.HIGH,
                confidence=0.91,
                evidence=[
                    AnalysisEvidenceItem(
                        frame_id=first.frame_code,
                        timestamp_seconds=first.timestamp_seconds,
                        observation="Mock observation",
                        relevance="supporting",
                    )
                ],
                recommended_actions=["Notify supervisor"],
                limitations=["Mocked provider — no paid API call"],
                inconclusive=False,
            )

    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("VISION_MODEL", "gpt-4o-mini")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.analysis.get_ai_provider",
        lambda settings=None: FakeOpenAIProvider(),
    )

    started = client.post(
        f"/api/videos/{uploaded['asset_code']}/analyze?force_new=true"
    ).json()["data"]
    assert started["provider_name"] == "openai"
    assert started["is_demo"] is False

    deadline = time.time() + 20
    while time.time() < deadline:
        analysis = client.get(f"/api/analyses/{started['analysis_code']}").json()["data"]
        if analysis["status"] in {"completed", "needs_review", "failed"}:
            break
        time.sleep(0.1)
    else:
        raise AssertionError("mocked openai analysis timed out")

    assert analysis["summary"] == "Mocked OpenAI summary"
    assert analysis["is_demo"] is False
    assert analysis["provider_name"] == "openai"
    get_settings.cache_clear()

"""Authenticated platform tests; historical demo fixtures remain intact."""

import json
from datetime import timedelta
from uuid import uuid4
import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select
from app.core.config import get_settings
from app.database.base import utc_now
from app.models.platform import UserSession, CameraConfiguration, StreamEvent
from app.services.auth import create_user, hash_password, verify_password
from tests.conftest import make_test_video
from tests.test_execution import _ready_plan


def enable_auth(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()


def sign_in(client, db, monkeypatch, role="administrator"):
    create_user(db, "operator", "a-safe-test-password", role)
    enable_auth(monkeypatch)
    result = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "a-safe-test-password"},
    )
    assert result.status_code == 200, result.text
    client.headers["X-CSRF-Token"] = result.json()["data"]["csrf_token"]
    return result


def test_password_hash():
    encoded = hash_password("a-long-test-password")
    assert "a-long-test-password" not in encoded
    assert verify_password("a-long-test-password", encoded)
    assert not verify_password("wrong", encoded)
    with pytest.raises(ValueError):
        hash_password("short")


def test_session_csrf_and_logout(client, db_session, monkeypatch):
    enable_auth(monkeypatch)
    assert client.get("/api/cameras").status_code == 401
    assert client.get("/api/frames/unknown/content").status_code == 401
    create_user(db_session, "operator", "a-safe-test-password", "administrator")
    assert (
        client.post(
            "/api/auth/login", json={"username": "operator", "password": "wrong"}
        ).status_code
        == 401
    )
    response = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "a-safe-test-password"},
    )
    assert response.status_code == 200
    assert (
        "HttpOnly" in response.headers["set-cookie"]
        and "SameSite=strict" in response.headers["set-cookie"]
    )
    assert client.get("/api/cameras").status_code == 200
    assert (
        client.post(
            "/api/cameras", json={"name": "Test", "location": "Test"}
        ).status_code
        == 403
    )
    client.headers["X-CSRF-Token"] = response.json()["data"]["csrf_token"]
    assert (
        client.post(
            "/api/auth/logout", headers={"Origin": "https://attacker.example"}
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/cameras").status_code == 401


def test_viewer_and_expiration(client, db_session, monkeypatch):
    sign_in(client, db_session, monkeypatch, "viewer")
    assert client.get("/api/analytics").status_code == 200
    assert (
        client.post(
            "/api/cameras", json={"name": "Illegal", "location": "Zone"}
        ).status_code
        == 403
    )
    session = db_session.scalar(select(UserSession))
    session.expires_at = utc_now() - timedelta(seconds=1)
    db_session.commit()
    assert client.get("/api/cameras").status_code == 401


def test_login_rate_limit(client, monkeypatch):
    enable_auth(monkeypatch)
    for _ in range(10):
        assert (
            client.post(
                "/api/auth/login", json={"username": "unknown", "password": "wrong"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            "/api/auth/login", json={"username": "unknown", "password": "wrong"}
        ).status_code
        == 429
    )


def test_camera_encryption_and_lifecycle(client, db_session, monkeypatch):
    monkeypatch.setenv("CAMERA_ENCRYPTION_KEY", Fernet.generate_key().decode())
    sign_in(client, db_session, monkeypatch)
    body = {
        "name": "Connected camera",
        "location": "Dock",
        "source_kind": "rtsp",
        "source": "rtsp://user:secret@localhost/video",
        "enabled": True,
        "policy": {"required_ppe": ["hard_hat"]},
    }
    response = client.post("/api/cameras", json=body)
    assert response.status_code == 201, response.text
    camera_id = response.json()["data"]["id"]
    assert "secret" not in response.text and "rtsp://" not in response.text
    assert (
        "secret" not in db_session.get(CameraConfiguration, camera_id).source_ciphertext
    )
    assert (
        client.get(f"/api/detector/config/{camera_id}").json()["data"]["source"]
        == body["source"]
    )
    body["name"] = "Renamed"
    body["source"] = None
    assert client.put(f"/api/cameras/{camera_id}", json=body).status_code == 200
    assert (
        client.post(
            "/api/detector/heartbeat", json={"camera_id": camera_id, "status": "online"}
        ).status_code
        == 200
    )
    assert client.delete(f"/api/cameras/{camera_id}").status_code == 200
    assert client.get(f"/api/cameras/{camera_id}").status_code == 404


def test_device_scope_real_cv_and_idempotency(
    client, db_session, tmp_path, monkeypatch
):
    enable_auth(monkeypatch)
    monkeypatch.setenv("DETECTOR_API_TOKEN", "test-device-token")
    monkeypatch.setenv("DETECTOR_CAMERA_IDS", "cam-03")
    get_settings.cache_clear()
    client.headers["Authorization"] = "Bearer test-device-token"
    event = {
        "schema_version": "1.0",
        "event_id": str(uuid4()),
        "event_type": "possible_person_down",
        "source_id": "worker",
        "camera_id": "cam-04",
        "clip_event_offset_seconds": 1.0,
    }
    path = make_test_video(tmp_path / "evidence.mp4", frames=40)

    def submit():
        with path.open("rb") as f:
            return client.post(
                "/api/detector/events",
                data={
                    "event_json": json.dumps(event),
                    "location": "Actual Dock",
                    "auto_analyze": "false",
                },
                files={"clip": ("evidence.mp4", f, "video/mp4")},
            )

    assert submit().status_code == 403
    event["camera_id"] = "cam-03"
    response = submit()
    assert response.status_code == 202, response.text
    again = submit()
    assert again.status_code == 202
    assert response.json()["data"]["asset_code"] == again.json()["data"]["asset_code"]
    client.headers.pop("Authorization")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    get_settings.cache_clear()
    asset = response.json()["data"]["asset_code"]
    analysis = client.get(f"/api/videos/{asset}/analyses").json()["data"][0]
    assert (
        analysis["provider_name"] == "local_cv"
        and analysis["is_simulated"] is False
        and analysis["confidence"] is None
    )
    workflow = client.get(f"/api/analyses/{analysis['analysis_code']}/workflow").json()[
        "data"
    ]
    assert (
        workflow["incident_code"] != "INC-2026-0042"
        and workflow["camera_id"] == "cam-03"
    )
    assert db_session.scalar(select(StreamEvent)) is not None


def test_stale_incident_operations(client, db_session, monkeypatch):
    sign_in(client, db_session, monkeypatch)
    path = "/api/incidents/inc-2026-0042/operations"
    body = {"version": 1, "notes": "Checked", "acknowledge": True}
    response = client.put(path, json=body)
    assert response.status_code == 200, response.text
    assert response.json()["data"]["version"] == 2
    assert client.put(path, json=body).status_code == 409
    assert client.get(path).json()["data"]["notes"] == "Checked"


def test_retry_rechecks_review_and_refreshes_report(client, db_session, tmp_path):
    from app.services.approval_execution import execute_plan

    plan_code, analysis_code, incident_code = _ready_plan(client, tmp_path)
    plan = client.get(f"/api/response-plans/{plan_code}").json()["data"]
    action_id = plan["actions"][0]["id"]
    assert (
        client.post(
            f"/api/response-plans/{plan_code}/approve",
            json={"selected_action_ids": [action_id], "confirmed": True},
        ).status_code
        == 200
    )
    execution = execute_plan(
        db_session, plan_code, fail_action_ids={action_id}
    ).executions[0]
    client.post(
        f"/api/analyses/{analysis_code}/review",
        json={"decision": "rejected", "reviewer_name": "reviewer"},
    )
    assert (
        client.post(f"/api/executions/{execution.execution_code}/retry").status_code
        == 409
    )
    client.post(
        f"/api/analyses/{analysis_code}/review",
        json={"decision": "confirmed", "reviewer_name": "reviewer"},
    )
    before = client.post(
        f"/api/incidents/{incident_code}/reports", json={"plan_identifier": plan_code}
    ).json()["data"]
    assert (
        client.post(f"/api/executions/{execution.execution_code}/retry").status_code
        == 200
    )
    after = client.post(
        f"/api/incidents/{incident_code}/reports", json={"plan_identifier": plan_code}
    ).json()["data"]
    assert before["id"] != after["id"]


def test_viewer_logout_and_access_revocation(client, db_session, monkeypatch):
    sign_in(client, db_session, monkeypatch, "viewer")
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_camera_source_guard_and_last_admin(client, db_session, monkeypatch):
    sign_in(client, db_session, monkeypatch)
    assert (
        client.post(
            "/api/cameras",
            json={
                "name": "Unsafe configuration",
                "location": "Dock",
                "source_kind": "rtsp",
                "source": "rtsp://user:secret@host/video",
            },
        ).status_code
        == 409
    )
    user = client.get("/api/users").json()["data"][0]
    assert (
        client.patch(
            f"/api/users/{user['id']}", json={"role": "viewer", "active": True}
        ).status_code
        == 409
    )


def test_retention_preserves_open_evidence_and_audit(client, db_session, tmp_path):
    from app.services.retention import expire_evidence
    from app.models.video import VideoAsset
    from app.models.notification import OperatorNotification
    from app.models.incident import Incident
    from app.models.execution import AuditEvent

    plan_code, analysis_code, incident_code = _ready_plan(client, tmp_path)
    video = db_session.scalar(select(VideoAsset))
    video.created_at = utc_now() - timedelta(days=40)
    db_session.commit()
    assert expire_evidence(db_session)["candidate_asset_codes"] == []
    note = db_session.scalar(
        select(OperatorNotification).where(
            OperatorNotification.video_asset_id == video.id
        )
    )
    incident = db_session.get(Incident, note.incident_id)
    incident.status = "resolved"
    db_session.commit()
    before = len(db_session.scalars(select(AuditEvent)).all())
    result = expire_evidence(db_session, apply=False)
    assert (
        video.asset_code in result["candidate_asset_codes"] and video.status == "ready"
    )
    result = expire_evidence(db_session, apply=True)
    db_session.commit()
    assert result["removed_files"] > 0 and video.status == "expired"
    assert len(db_session.scalars(select(AuditEvent)).all()) == before

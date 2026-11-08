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


def test_pose_region_policy_validation():
    from app.api.routes.platform import DetectionPolicy
    assert DetectionPolicy(pose_region=[.5, 0, 1, 1]).pose_region == (.5, 0, 1, 1)
    for value in ([1, 0, .5, 1], [0, 0, float('nan'), 1], [0, 0, 2, 1]):
        with pytest.raises(ValueError):
            DetectionPolicy(pose_region=value)


def test_local_ppe_deployment_is_explicitly_disabled(client, db_session, monkeypatch):
    sign_in(client, db_session, monkeypatch)
    response = client.post('/api/cameras', json={'name':'Excluded PPE','location':'Test',
        'policy':{'detectors':['ppe'],'required_ppe':['hard_hat']}})
    assert response.status_code == 409
    assert response.json()['error']['code'] == 'PPE_DEPLOYMENT_DISABLED'


def test_device_cannot_enumerate_events_or_rebind_an_event_id(client, db_session, tmp_path, monkeypatch):
    import hashlib
    enable_auth(monkeypatch)
    monkeypatch.setenv('DETECTOR_API_TOKEN','scoped-test-device')
    monkeypatch.setenv('DETECTOR_CAMERA_IDS','cam-03,cam-04')
    get_settings.cache_clear()
    client.headers['Authorization']='Bearer scoped-test-device'
    assert client.get('/api/detector/events').status_code == 401
    path=make_test_video(tmp_path/'hashed.mp4',frames=40)
    payload={'schema_version':'1.0','event_id':str(uuid4()),'source_id':'actual-worker','camera_id':'cam-03',
        'evidence':{'clip_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}}
    def submit():
        return client.post('/api/detector/events',data={'event_json':json.dumps(payload)},
            files={'clip':('hashed.mp4',path.read_bytes(),'video/mp4')})
    first=submit()
    assert first.status_code == 202,first.text
    payload['camera_id']='cam-04'
    assert submit().status_code == 409
    payload['camera_id']='cam-03'
    payload['evidence']['clip_sha256']='0'*64
    assert submit().status_code == 409
    payload['event_id']=str(uuid4())
    mismatch=submit()
    assert mismatch.status_code == 422
    assert mismatch.json()['error']['code']=='EVIDENCE_HASH_MISMATCH'


def test_interrupted_detector_job_recovers_from_persisted_media(client, db_session, tmp_path):
    import asyncio
    from fastapi import BackgroundTasks, UploadFile
    from starlette.datastructures import Headers
    from app.schemas.detector import DetectorEventIngestRequest
    from app.services.detector_ingestion import ingest_detector_event, get_ingestion
    from app.services.recovery import snapshot_interrupted_events, recover_events
    path=make_test_video(tmp_path/'interrupted.mp4',frames=40)
    event_id=str(uuid4())
    payload=DetectorEventIngestRequest(event={'schema_version':'1.0','event_id':event_id,
        'source_id':'recovery-regression-fixture','camera_id':'cam-03','trigger_signals':['rapid_drop']},
        incident_identifier=None,auto_analyze=False)
    # Real validation/storage/commit, deliberately stop before executing background tasks.
    with path.open('rb') as handle:
        upload=UploadFile(file=handle,filename='interrupted.mp4',headers=Headers({'content-type':'video/mp4'}))
        response=asyncio.run(ingest_detector_event(db_session,payload,clip=upload,background_tasks=BackgroundTasks()))
    assert response.status.value=='processing'
    pending=snapshot_interrupted_events()
    assert event_id in pending
    result=recover_events(pending)
    assert result['recovered']==1,result
    assert event_id not in snapshot_interrupted_events()
    db_session.expire_all()
    recovered=get_ingestion(db_session,event_id)
    assert recovered.status=='completed'
    assert recovered.analysis.provider_name=='local_cv'
    assert recovered.incident_id is not None

    from app.services.videos import process_video_job
    from app.models.video_frame import VideoFrame
    before=list(db_session.scalars(select(VideoFrame.id).where(VideoFrame.video_asset_id==recovered.video_asset_id)))
    process_video_job(recovered.video_asset_id,recovered.processing_job_id)
    after=list(db_session.scalars(select(VideoFrame.id).where(VideoFrame.video_asset_id==recovered.video_asset_id)))
    assert before==after  # A queued retry cannot rewrite already completed evidence.

    from app.seed.seed_data import seed_database
    from app.models.procedure_policy import ProcedureChunk, ProcedureRetrievalMatch
    from app.models.camera import Camera
    assert db_session.scalar(select(ProcedureRetrievalMatch.id).limit(1)) is not None
    chunks=list(db_session.scalars(select(ProcedureChunk.id)))
    camera=db_session.get(Camera,'cam-03');camera.name='Operator camera configuration preserved';db_session.commit()
    seed_database(db_session)
    assert list(db_session.scalars(select(ProcedureChunk.id)))==chunks
    assert db_session.get(Camera,'cam-03').name=='Operator camera configuration preserved'

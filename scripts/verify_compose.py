"""Verify a dedicated local Compose installation; never sends external actions.

Requires already running, migrated services and explicit private env file. Creates
one QA user/camera test plus an offline retry of a real detector event. Secrets
and database backups stay outside Git. Run only on an isolated verification stack.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time
import uuid
import httpx

p = argparse.ArgumentParser()
p.add_argument("--env-file", required=True, type=Path)
p.add_argument("--project", default="safetylens-hardening")
p.add_argument("--clip", required=True, type=Path)
p.add_argument("--pose-model", required=True, type=Path)
p.add_argument("--output-directory", required=True, type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
a.output_directory.mkdir(parents=True, exist_ok=True)
values = dict(
    line.split("=", 1)
    for line in a.env_file.read_text().splitlines()
    if "=" in line and not line.startswith("#")
)
password = secrets.token_urlsafe(24)
username = "qa-" + uuid.uuid4().hex[:8]
compose = [
    "docker",
    "compose",
    "--env-file",
    str(a.env_file),
    "-p",
    a.project,
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.postgres.yml",
]


def command(args, **kwargs):
    return subprocess.run(args, cwd=root, check=True, capture_output=True, **kwargs)


def container(code, payload):
    return (
        command(
            compose + ["exec", "-T", "backend", "python", "-c", code],
            input=json.dumps(payload).encode(),
        )
        .stdout.decode()
        .strip()
    )


def healthy(client):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if client.get("/api/health").status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    raise RuntimeError("API did not become healthy")


container(
    'import json,sys; from app.database.session import SessionLocal; from app.services.auth import create_user; x=json.load(sys.stdin); db=SessionLocal(); create_user(db,x["username"],x["password"],"administrator"); db.close()',
    {"username": username, "password": password},
)
with httpx.Client(base_url="http://localhost:8000", timeout=30) as client:
    healthy(client)
    response = client.post(
        "/api/auth/login", json={"username": username, "password": password}
    )
    response.raise_for_status()
    client.headers["X-CSRF-Token"] = response.json()["data"]["csrf_token"]
    env = {
        **os.environ,
        "SAFETYLENS_E2E_USERNAME": username,
        "SAFETYLENS_E2E_PASSWORD": password,
        "SAFETYLENS_E2E_BACKEND": "http://localhost:8000",
        "SAFETYLENS_REAL_CLIP": str(a.clip.resolve()),
        "SAFETYLENS_POSE_MODEL": str(a.pose_model.resolve()),
        "DETECTOR_API_TOKEN": values["DETECTOR_API_TOKEN"],
    }
    fixture = command(
        [
            str(root / "backend/.venv/bin/python"),
            str(root / "scripts/e2e_real_detector.py"),
        ],
        env=env,
    )
    model_result = json.loads(fixture.stdout)
    verification = json.loads(Path(model_result["verification_path"]).read_text())
    event_id = model_result["event_id"]
    deadline = time.monotonic() + 30
    while True:
        event = client.get("/api/detector/events/" + event_id).json()["data"]
        if event.get("analysis_code") and event.get("incident_code"):
            break
        if time.monotonic() > deadline:
            raise RuntimeError("Actual event did not complete analysis/incident")
        time.sleep(0.1)
    notifications = client.get("/api/notifications").json()["data"]
    assert any(x["analysis_code"] == event["analysis_code"] for x in notifications)
    storage_hash = container(
        'import sys,json,hashlib; from sqlalchemy import select; from app.models.video import VideoAsset; from app.database.session import SessionLocal; from app.services.storage import resolve_upload_path; x=json.load(sys.stdin); db=SessionLocal(); v=db.scalar(select(VideoAsset).where(VideoAsset.asset_code==x["asset"])); print(hashlib.sha256(resolve_upload_path(v.stored_filename).read_bytes()).hexdigest())',
        {"asset": event["asset_code"]},
    )
    from_dir = Path(model_result["verification_path"]).parent
    import sqlite3

    original_db = next(from_dir.rglob("outbox.sqlite3"))
    with sqlite3.connect(original_db) as db:
        payload, clipname = db.execute(
            "SELECT payload,clip FROM deliveries WHERE event_id=?", (event_id,)
        ).fetchone()
    payload = json.loads(payload)
    assert storage_hash == payload["evidence"]["clip_sha256"]
    # Browser drives the actual production standalone frontend, not the dev server.
    browser_code = r"""
const {chromium}=require('./frontend/node_modules/@playwright/test');
(async()=>{const browser=await chromium.launch({headless:true});const page=await browser.newPage({viewport:{width:1440,height:1000}});const base='http://localhost:8000';
await page.goto('http://localhost:3000');await page.getByLabel('Username',{exact:true}).fill(process.env.SAFETYLENS_E2E_USERNAME);await page.getByLabel('Password',{exact:true}).fill(process.env.SAFETYLENS_E2E_PASSWORD);await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByRole('heading',{name:'Operations overview',exact:true}).waitFor();
await page.goto('http://localhost:3000/response?analysis_id='+process.env.QA_ANALYSIS+'&video_id='+process.env.QA_ASSET);await page.getByRole('button',{name:'Confirm Incident',exact:true}).click();await page.getByRole('button',{name:'Approve selected actions',exact:true}).click();await page.getByRole('button',{name:'Confirm approval',exact:true}).click();await page.getByRole('button',{name:'Run approved actions',exact:true}).click();await page.getByRole('button',{name:'Execute simulated actions',exact:true}).click();await page.getByText(/simulated action results recorded/).waitFor();const link=page.getByRole('link',{name:'Download PDF',exact:true});await link.waitFor();const response=await page.request.get(await link.getAttribute('href'));const body=await response.body();if(!response.ok()||body.subarray(0,4).toString()!=='%PDF')throw Error('Invalid PDF');
const v=page.locator('video').first();await v.evaluate(async v=>{v.muted=true;await v.play()});await page.waitForTimeout(250);if(await v.evaluate(v=>v.currentTime)<=0)throw Error('Playback did not advance');await page.evaluate(()=>scrollTo(0,0));await page.screenshot({path:process.env.QA_SCREENSHOT,fullPage:true});await browser.close();console.log(JSON.stringify({login:true,actualEvidencePlayback:true,approval:true,simulatedExecution:true,pdfBytes:body.length}));})().catch(e=>{console.error(e);process.exit(1)})
"""
    env.update(
        QA_ANALYSIS=event["analysis_code"],
        QA_ASSET=event["asset_code"],
        QA_SCREENSHOT=str((a.output_directory / "compose-response.png").resolve()),
    )
    browser = command(["node", "-e", browser_code], env=env)
    browser_result = json.loads(browser.stdout)
    audit = client.get("/api/incidents/" + event["incident_code"] + "/audit").json()[
        "data"
    ]
    assert len(audit) >= 4
    # Two independently authenticated operators submit the same version together.
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    manager = "manager-" + uuid.uuid4().hex[:8]
    manager_password = secrets.token_urlsafe(24)
    client.post(
        "/api/users",
        json={
            "username": manager,
            "password": manager_password,
            "role": "safety_manager",
        },
    ).raise_for_status()
    incident_detail = client.get("/api/incidents/" + event["incident_code"])
    incident_detail.raise_for_status()
    incident_id = incident_detail.json()["data"]["incident"]["id"]
    operation_response = client.get("/api/incidents/" + incident_id + "/operations")
    operation_response.raise_for_status()
    operation = operation_response.json()["data"]
    barrier = Barrier(2)

    def concurrent_note(account, secret):
        with httpx.Client(base_url="http://localhost:8000", timeout=20) as operator:
            auth = operator.post(
                "/api/auth/login", json={"username": account, "password": secret}
            )
            auth.raise_for_status()
            barrier.wait(timeout=10)
            response = operator.put(
                "/api/incidents/" + incident_id + "/operations",
                headers={"X-CSRF-Token": auth.json()["data"]["csrf_token"]},
                json={
                    "version": operation["version"],
                    "notes": "Concurrent verification " + account,
                    "acknowledge": True,
                },
            )
            return response.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(concurrent_note, username, password),
            pool.submit(concurrent_note, manager, manager_password),
        ]
        concurrent_statuses = sorted(f.result() for f in futures)
    assert concurrent_statuses == [200, 409], concurrent_statuses
    # Take API down. A reopened durable outbox must retain the already real event,
    # then recover to the original backend asset without duplicate incident creation.
    sys.path.insert(0, str(root / "detector/src"))
    from safetylens_detector.delivery import EventOutbox

    retry = EventOutbox(a.output_directory / "interruption-outbox")
    retry.enqueue(
        payload,
        original_db.parent / clipname,
        camera_id="cam-03",
        location="Controlled restart test",
        clip_event_offset_seconds=payload["clip_event_offset_seconds"],
    )
    command(compose + ["stop", "backend"])
    assert not retry.flush_once("http://localhost:8000", values["DETECTOR_API_TOKEN"])
    retry = EventOutbox(a.output_directory / "interruption-outbox")
    command(compose + ["start", "backend"])
    healthy(client)
    deadline = time.monotonic() + 15
    while not retry.flush_once("http://localhost:8000", values["DETECTOR_API_TOKEN"]):
        if time.monotonic() > deadline:
            raise RuntimeError("Outbox did not recover")
        time.sleep(0.25)
    duplicate = client.get("/api/detector/events/" + event_id)
    duplicate.raise_for_status()
    assert duplicate.json()["data"]["asset_code"] == event["asset_code"]
    command(compose + ["restart", "postgres"])
    healthy(client)
    assert client.get("/api/auth/me").status_code == 200
    assert (
        client.get("/api/detector/events/" + event_id).json()["data"]["asset_code"]
        == event["asset_code"]
    )
    # Backup is private and never staged; restore into a brand-new isolated DB.
    backup = a.output_directory / "verification.dump"
    dump = command(
        compose
        + [
            "exec",
            "-T",
            "postgres",
            "pg_dump",
            "-U",
            "safetylens",
            "-d",
            "safetylens",
            "--format=custom",
            "--no-owner",
        ]
    ).stdout
    with os.fdopen(
        os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), "wb"
    ) as file:
        file.write(dump)
    restore_db = "verify_" + uuid.uuid4().hex[:12]
    command(
        compose + ["exec", "-T", "postgres", "createdb", "-U", "safetylens", restore_db]
    )
    command(
        compose
        + [
            "exec",
            "-T",
            "postgres",
            "pg_restore",
            "-U",
            "safetylens",
            "-d",
            restore_db,
            "--no-owner",
        ],
        input=dump,
    )
    restored = (
        command(
            compose
            + [
                "exec",
                "-T",
                "postgres",
                "psql",
                "-U",
                "safetylens",
                "-d",
                restore_db,
                "-Atc",
                "SELECT count(*) FROM detector_event_ingestions",
            ]
        )
        .stdout.decode()
        .strip()
    )
    assert int(restored) >= 1
    timings = []
    for _ in range(30):
        t = time.perf_counter()
        client.get("/api/camera-management").raise_for_status()
        timings.append((time.perf_counter() - t) * 1000)
    result = {
        "stack": "documented Compose; PostgreSQL17; frontend standalone; backend Python3.12",
        "model_event_id": event_id,
        "model_source_seconds": verification["event"]["occurred_at_seconds"],
        "worker_offline_wall_seconds": verification["delivery_wall_seconds"],
        "clip_sha256_verified": storage_hash,
        "operator_notification": True,
        "concurrent_operator_statuses": concurrent_statuses,
        "browser": browser_result,
        "audit_events": len(audit),
        "offline_outbox_restart_and_duplicate_reuse": True,
        "postgres_restart_session_and_evidence_mapping": True,
        "backup_restore_detector_records": int(restored),
        "backup_sha256": hashlib.sha256(dump).hexdigest(),
        "warm_camera_inventory_30_requests_ms": {
            "minimum": min(timings),
            "mean": sum(timings) / len(timings),
            "maximum": max(timings),
        },
        "limitations": [
            "Offline replay wall time is not physical fall-to-alert latency",
            "Local HTTP profile; HTTPS and physical camera fleet not tested",
            "Snapshot/page render are not PPE validation",
        ],
    }
    (a.output_directory / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

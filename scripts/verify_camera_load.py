"""Isolated recorded-camera load and MJPEG disconnect/reconnect verification.

Needs dedicated Compose stack and an explicit private QA credential file. Does
not prove sustained hardware performance or new detector accuracy.
"""

import argparse, json, os, time, subprocess, threading, uuid, re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import httpx

p = argparse.ArgumentParser()
p.add_argument("--credentials", required=True, type=Path)
p.add_argument("--env-file", required=True, type=Path)
p.add_argument("--clip", required=True, type=Path)
p.add_argument("--model", required=True, type=Path)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
a.output.mkdir(parents=True, exist_ok=True)
credentials = json.loads(a.credentials.read_text())
settings = dict(
    line.split("=", 1)
    for line in a.env_file.read_text().splitlines()
    if "=" in line and not line.startswith("#")
)
compose = [
    "docker",
    "compose",
    "--env-file",
    str(a.env_file),
    "-p",
    "safetylens-hardening",
    "-f",
    "docker-compose.yml",
    "-f",
    "docker-compose.postgres.yml",
]
env = {
    **os.environ,
    "PYTHONPATH": str(root / "detector/src"),
    "DETECTOR_API_TOKEN": settings["DETECTOR_API_TOKEN"],
}


def run_worker(ids, seconds):
    command = [
        "/usr/bin/time",
        "-l",
        str(root / "detector/.venv/bin/python"),
        "-m",
        "safetylens_detector.worker",
        "--backend",
        "http://localhost:8000",
        "--camera-ids",
        ",".join(ids),
        "--pose-model",
        str(a.model.resolve()),
        "--state-dir",
        str(a.output / ("worker-" + str(len(ids)))),
        "--max-seconds",
        str(seconds),
    ]
    return command


pause = threading.Event()
shutdown = threading.Event()


class Stream(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        import cv2

        if pause.is_set():
            self.send_error(503)
            return
        self.send_response(200)
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
        self.end_headers()
        capture = cv2.VideoCapture(str(a.clip))
        try:
            while not shutdown.is_set() and not pause.is_set():
                ok, frame = capture.read()
                if not ok:
                    capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                ok, image = cv2.imencode(".jpg", frame)
                if ok:
                    body = image.tobytes()
                    self.wfile.write(
                        b"--frame\r\nContent-Type: image/jpeg\r\nContent-Length: "
                        + str(len(body)).encode()
                        + b"\r\n\r\n"
                        + body
                        + b"\r\n"
                    )
                    self.wfile.flush()
                time.sleep(1 / 15)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            capture.release()
            self.close_connection = True


server = ThreadingHTTPServer(("127.0.0.1", 8123), Stream)
threading.Thread(target=server.serve_forever, daemon=True).start()
with httpx.Client(base_url="http://localhost:8000", timeout=15) as client:
    r = client.post("/api/auth/login", json=credentials)
    r.raise_for_status()
    client.headers["X-CSRF-Token"] = r.json()["data"]["csrf_token"]
    cameras = []
    for i in range(5):
        r = client.post(
            "/api/cameras",
            json={
                "name": f"Controlled replay {uuid.uuid4().hex[:8]}",
                "location": "Recorded test only",
                "source_kind": "network" if i == 4 else "replay",
                "source": "http://127.0.0.1:8123/stream"
                if i == 4
                else str(a.clip.resolve()),
                "enabled": True,
                "policy": {
                    "sample_fps": 12,
                    "pose_region": [0.5, 0, 1, 1],
                    "pre_event_seconds": 1,
                    "post_event_seconds": 1,
                },
            },
        )
        r.raise_for_status()
        cameras.append(r.json()["data"]["id"])
    with a.env_file.open("a") as file:
        file.write("DETECTOR_CAMERA_IDS=cam-03," + ",".join(cameras) + "\n")
    subprocess.run(
        compose + ["up", "-d", "backend"], cwd=root, check=True, capture_output=True
    )
    for _ in range(120):
        try:
            if client.get("/api/health").status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(0.25)
    else:
        raise RuntimeError("Reconfigured backend not ready")
    started = time.perf_counter()
    load = subprocess.run(
        run_worker(cameras[:4], 30),
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=45,
    )
    elapsed = time.perf_counter() - started
    (a.output / "four-camera.log").write_text(load.stdout + load.stderr)
    summaries = [
        json.loads(line)
        for line in load.stdout.splitlines()
        if line.startswith("{")
        and json.loads(line).get("kind") == "camera_worker_summary"
    ]
    assert len(summaries) == 4 and all(x["frames_processed"] > 0 for x in summaries), (
        summaries
    )
    import sqlite3

    delivered = []
    for database in (a.output / "worker-4").rglob("outbox.sqlite3"):
        with sqlite3.connect(database) as db:
            delivered.extend(
                db.execute("SELECT event_id,status FROM deliveries").fetchall()
            )
    assert len(delivered) == 4 and all(x[1] == "acknowledged" for x in delivered), (
        delivered
    )
    with (
        (a.output / "network-camera.stdout").open("w") as stdout,
        (a.output / "network-camera.stderr").open("w") as stderr,
    ):
        process = subprocess.Popen(
            run_worker(cameras[4:], 20), cwd=root, env=env, stdout=stdout, stderr=stderr
        )
        start = time.monotonic()
        states = []
        while process.poll() is None:
            elapsed_network = time.monotonic() - start
            if 4 <= elapsed_network < 8:
                pause.set()
            elif elapsed_network >= 8:
                pause.clear()
            response = client.get("/api/camera-management")
            response.raise_for_status()
            status = next(
                x["status"] for x in response.json()["data"] if x["id"] == cameras[4]
            )
            if not states or states[-1]["status"] != status:
                states.append({"seconds": elapsed_network, "status": status})
            time.sleep(0.25)
    shutdown.set()
    server.shutdown()
    labels = [x["status"] for x in states]
    first = labels.index("online")
    lost = labels.index("offline", first + 1)
    recovered = labels.index("online", lost + 1)
    result = {
        "recorded_replay_cameras": 4,
        "four_camera_summaries": summaries,
        "total_sampled_frames": sum(x["frames_processed"] for x in summaries),
        "wall_seconds_including_process_start": elapsed,
        "aggregate_offline_sampled_fps": sum(x["frames_processed"] for x in summaries)
        / elapsed,
        "acknowledged_real_model_events": len(delivered),
        "network_camera_health_transitions": states,
        "disconnect_then_reconnect_verified": recovered > lost,
        "limitations": [
            "Same recorded clip replayed four times; not four independent scenes",
            "Offline processing, not sustained live-camera capacity",
            "MJPEG server interruption is controlled local simulation, not physical RTSP hardware",
            "GPU utilization and dropped frames unmeasured",
        ],
    }
    (a.output / "verification.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))

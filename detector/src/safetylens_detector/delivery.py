"""Durable bounded SQLite outbox. Transport is at-least-once; backend deduplicates UUIDs."""

from __future__ import annotations
import json
import random
import shutil
import sqlite3
import time
from pathlib import Path
from uuid import UUID


class EventOutbox:
    def __init__(
        self,
        directory: str | Path,
        *,
        maximum_bytes: int = 500_000_000,
        maximum_events: int = 1000,
    ):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.maximum_bytes, self.maximum_events = maximum_bytes, maximum_events
        self.database = self.root / "outbox.sqlite3"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS deliveries (
                event_id TEXT PRIMARY KEY, payload TEXT NOT NULL, clip TEXT NOT NULL,
                location TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL DEFAULT 0,
                last_error TEXT, acknowledged_at REAL)""")

    def connect(self):
        return sqlite3.connect(self.database, timeout=10)

    def enqueue(
        self,
        event: dict,
        clip: str | Path,
        *,
        camera_id: str,
        location: str,
        clip_event_offset_seconds: float,
    ):
        event_id = str(UUID(event["event_id"]))
        source = Path(clip)
        if not source.is_file() or source.stat().st_size <= 0:
            raise ValueError("Completed nonempty evidence clip is required")
        if not camera_id or clip_event_offset_seconds < 0:
            raise ValueError(
                "Camera and non-negative clip-relative offset are required"
            )
        payload = {
            **event,
            "camera_id": camera_id,
            "clip_event_offset_seconds": clip_event_offset_seconds,
        }
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if db.execute(
                "SELECT 1 FROM deliveries WHERE event_id=?", (event_id,)
            ).fetchone():
                return event_id
            count = db.execute(
                "SELECT count(*) FROM deliveries WHERE status != 'acknowledged'"
            ).fetchone()[0]
            total = sum(p.stat().st_size for p in self.root.glob("*.mp4"))
            if (
                count >= self.maximum_events
                or total + source.stat().st_size > self.maximum_bytes
            ):
                raise BufferError(
                    "Outbox capacity reached; operator intervention required, original evidence retained"
                )
            destination = self.root / f"{event_id}.mp4"
            temporary = destination.with_suffix(".partial")
            shutil.copyfile(source, temporary)
            temporary.replace(destination)
            db.execute(
                "INSERT INTO deliveries(event_id,payload,clip,location) VALUES(?,?,?,?)",
                (
                    event_id,
                    json.dumps(payload, allow_nan=False),
                    destination.name,
                    location,
                ),
            )
        return event_id

    def flush_once(
        self, base_url: str, token: str, *, client=None, now: float | None = None
    ) -> bool:
        import httpx
        from urllib.parse import urlparse

        parsed = urlparse(base_url)
        if parsed.scheme != "https" and not (
            parsed.scheme == "http"
            and parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        ):
            raise ValueError("Remote delivery requires HTTPS")
        if not token:
            raise ValueError("Detector credential is required")
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT event_id,payload,clip,location,attempts FROM deliveries WHERE status='pending' AND next_attempt<=? ORDER BY rowid LIMIT 1",
                (now,),
            ).fetchone()
            if not row:
                return False
            # Lease survives a sender crash and permits recovery after 60 seconds.
            db.execute(
                "UPDATE deliveries SET next_attempt=? WHERE event_id=?",
                (now + 60, row[0]),
            )
        event_id, payload, filename, location, attempts = row
        own_client = client is None
        client = client or httpx.Client(timeout=30, follow_redirects=False)
        try:
            with (self.root / filename).open("rb") as handle:
                response = client.post(
                    base_url.rstrip("/") + "/api/detector/events",
                    headers={"Authorization": "Bearer " + token},
                    data={
                        "event_json": payload,
                        "location": location,
                        "auto_analyze": "false",
                    },
                    files={"clip": (filename, handle, "video/mp4")},
                )
            if response.status_code in {200, 202}:
                data = response.json().get("data", {})
                if (
                    data.get("event_id") != event_id
                    or not data.get("asset_code")
                    or data.get("status") == "failed"
                ):
                    raise ValueError("Backend did not acknowledge stored evidence")
                with self.connect() as db:
                    db.execute(
                        "UPDATE deliveries SET status='acknowledged', acknowledged_at=?, attempts=?, last_error=NULL WHERE event_id=?",
                        (now, attempts + 1, event_id),
                    )
                return True
            retryable = response.status_code >= 500 or response.status_code in {
                408,
                429,
            }
            self._failure(
                event_id, attempts, now, f"HTTP {response.status_code}", retryable
            )
        except (httpx.HTTPError, OSError, ValueError):
            # Do not persist exception URLs, bearer tokens or response bodies.
            self._failure(
                event_id, attempts, now, "Transport or acknowledgement failure", True
            )
        finally:
            if own_client:
                client.close()
        return False

    def _failure(self, event_id, attempts, now, error, retryable):
        delay = min(300, 2 ** min(attempts + 1, 8)) + random.random()
        with self.connect() as db:
            db.execute(
                "UPDATE deliveries SET status=?,attempts=?,next_attempt=?,last_error=? WHERE event_id=?",
                (
                    "pending" if retryable else "blocked",
                    attempts + 1,
                    now + delay,
                    error,
                    event_id,
                ),
            )

    def prune(self, *, acknowledged_before: float):
        with self.connect() as db:
            rows = db.execute(
                "SELECT event_id,clip FROM deliveries WHERE status='acknowledged' AND acknowledged_at<?",
                (acknowledged_before,),
            ).fetchall()
            for event_id, filename in rows:
                (self.root / Path(filename).name).unlink(missing_ok=True)
                db.execute("DELETE FROM deliveries WHERE event_id=?", (event_id,))
        return len(rows)


def main():
    import argparse, os

    parser = argparse.ArgumentParser(
        description="Retry durable detector deliveries; token comes from DETECTOR_API_TOKEN"
    )
    parser.add_argument("--outbox", required=True, type=Path)
    parser.add_argument("--backend", required=True)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    token = os.environ.get("DETECTOR_API_TOKEN", "")
    outbox = EventOutbox(args.outbox)
    while True:
        outbox.flush_once(args.backend, token)
        if args.once:
            break
        outbox.prune(acknowledged_before=time.time() - 86400)
        time.sleep(1)


if __name__ == "__main__":
    main()

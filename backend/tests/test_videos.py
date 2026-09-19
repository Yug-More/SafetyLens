from __future__ import annotations

import time
from pathlib import Path

from app.services.storage import resolve_frame_path, resolve_upload_path
from app.services.video_processing import choose_frame_indices
from tests.conftest import make_test_video


def _wait_for_job(client, job_code: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        response = client.get(f"/api/processing-jobs/{job_code}")
        assert response.status_code == 200
        last = response.json()["data"]
        if last["status"] in {"completed", "failed"}:
            return last
        time.sleep(0.2)
    raise AssertionError(f"Job did not finish in time: {last}")


def test_valid_video_upload_and_processing(client, tmp_path: Path):
    video_path = make_test_video(tmp_path / "sample.mp4", frames=32, fps=8)
    with video_path.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B", "camera_id": "cam-04"},
            files={"file": ("demo.mp4", handle, "video/mp4")},
        )
    assert response.status_code == 202
    payload = response.json()["data"]
    assert payload["asset_code"].startswith("VID-")
    assert payload["job_code"].startswith("JOB-")
    assert payload["status"] == "uploaded"

    job = _wait_for_job(client, payload["job_code"])
    assert job["status"] == "completed"
    assert job["progress"] == 100
    assert "Ready for AI analysis" in job["current_step"]

    detail = client.get(f"/api/videos/{payload['asset_code']}")
    assert detail.status_code == 200
    video = detail.json()["data"]
    assert video["status"] == "ready"
    assert video["duration_seconds"] is not None and video["duration_seconds"] > 0
    assert video["width"] == 320
    assert video["height"] == 240

    frames = client.get(f"/api/videos/{payload['asset_code']}/frames")
    assert frames.status_code == 200
    frame_data = frames.json()["data"]
    assert len(frame_data) >= 2
    numbers = [item["frame_number"] for item in frame_data]
    assert len(numbers) == len(set(numbers))

    content = client.get(f"/api/videos/{payload['asset_code']}/content")
    assert content.status_code == 200
    assert content.headers["content-type"].startswith("video/")

    frame_content = client.get(frame_data[0]["content_url"])
    assert frame_content.status_code == 200
    assert frame_content.headers["content-type"] == "image/jpeg"


def test_unsupported_extension(client, tmp_path: Path):
    path = tmp_path / "bad.avi"
    path.write_bytes(b"not-a-video")
    with path.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B"},
            files={"file": ("bad.avi", handle, "video/avi")},
        )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_unsupported_mime_type(client, tmp_path: Path):
    video_path = make_test_video(tmp_path / "sample.mp4")
    with video_path.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B"},
            files={"file": ("sample.mp4", handle, "application/octet-stream")},
        )
    assert response.status_code == 415


def test_empty_upload(client, tmp_path: Path):
    path = tmp_path / "empty.mp4"
    path.write_bytes(b"")
    with path.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B"},
            files={"file": ("empty.mp4", handle, "video/mp4")},
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "EMPTY_UPLOAD"


def test_file_size_limit(client, tmp_path: Path, monkeypatch):
    monkeypatch.setenv("MAX_VIDEO_SIZE_MB", "1")
    from app.core.config import get_settings

    get_settings.cache_clear()
    # Create a file larger than 1MB without needing a valid video decode first.
    # Validation order: extension/mime first, then stream size, then OpenCV.
    big = tmp_path / "big.mp4"
    big.write_bytes(b"0" * (1024 * 1024 + 50))
    with big.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B"},
            files={"file": ("big.mp4", handle, "video/mp4")},
        )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    get_settings.cache_clear()


def test_corrupt_video(client, tmp_path: Path):
    path = tmp_path / "corrupt.mp4"
    path.write_bytes(b"not-really-mp4-content")
    with path.open("rb") as handle:
        response = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B"},
            files={"file": ("corrupt.mp4", handle, "video/mp4")},
        )
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {
        "UNREADABLE_VIDEO",
        "INVALID_VIDEO_DIMENSIONS",
        "INVALID_VIDEO_DURATION",
        "FRAME_EXTRACTION_FAILED",
    }


def test_video_listing_and_missing(client, tmp_path: Path):
    video_path = make_test_video(tmp_path / "list.mp4", frames=16)
    with video_path.open("rb") as handle:
        uploaded = client.post(
            "/api/videos/upload",
            data={"location": "Loading Zone B", "camera_id": "cam-04"},
            files={"file": ("list.mp4", handle, "video/mp4")},
        ).json()["data"]
    _wait_for_job(client, uploaded["job_code"])

    listing = client.get("/api/videos?status=ready")
    assert listing.status_code == 200
    codes = {item["asset_code"] for item in listing.json()["data"]}
    assert uploaded["asset_code"] in codes

    missing = client.get("/api/videos/VID-DOES-NOT-EXIST")
    assert missing.status_code == 404


def test_path_traversal_resistance(client):
    response = client.get("/api/frames/../../etc/passwd/content")
    assert response.status_code in {404, 400, 422}


def test_choose_frame_indices_no_duplicates():
    indices = choose_frame_indices(100, 10)
    assert len(indices) == len(set(indices))
    assert indices[0] == 0
    assert indices[-1] == 99


def test_safe_media_paths(temp_media: Path):
    upload = resolve_upload_path("abc123.mp4")
    frame = resolve_frame_path("frame123.jpg")
    assert str(upload).startswith(str(temp_media / "uploads"))
    assert str(frame).startswith(str(temp_media / "frames"))

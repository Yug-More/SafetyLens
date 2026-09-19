from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings, get_settings
from app.core.errors import AppError

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")

ALLOWED_EXTENSIONS = {".mp4", ".mov", ".webm"}
ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/webm",
    "application/mp4",
}


def ensure_storage_directories(settings: Settings | None = None) -> None:
    cfg = settings or get_settings()
    cfg.upload_path.mkdir(parents=True, exist_ok=True)
    cfg.frame_path.mkdir(parents=True, exist_ok=True)


def sanitize_original_filename(filename: str | None) -> str:
    raw = (filename or "").strip()
    if not raw:
        raise AppError("VALIDATION_ERROR", "Original filename cannot be blank", status_code=422)
    name = Path(raw).name
    if not name or name in {".", ".."}:
        raise AppError("VALIDATION_ERROR", "Original filename is invalid", status_code=422)
    return name


def extension_for_filename(filename: str) -> str:
    return Path(filename).suffix.lower()


def validate_extension(filename: str) -> str:
    ext = extension_for_filename(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError(
            "UNSUPPORTED_MEDIA_TYPE",
            "Unsupported video format. Allowed formats: MP4, MOV, WebM.",
            status_code=415,
        )
    return ext


def validate_mime_type(content_type: str | None) -> str:
    mime = (content_type or "").split(";")[0].strip().lower()
    if not mime:
        raise AppError(
            "UNSUPPORTED_MEDIA_TYPE",
            "Missing content type for uploaded video.",
            status_code=415,
        )
    if mime not in ALLOWED_MIME_TYPES:
        raise AppError(
            "UNSUPPORTED_MEDIA_TYPE",
            "Unsupported video content type. Allowed types: video/mp4, video/quicktime, video/webm.",
            status_code=415,
        )
    return mime


def generate_stored_filename(extension: str) -> str:
    safe_ext = extension if extension.startswith(".") else f".{extension}"
    return f"{uuid4().hex}{safe_ext}"


def generate_frame_filename() -> str:
    return f"{uuid4().hex}.jpg"


def resolve_upload_path(stored_filename: str, settings: Settings | None = None) -> Path:
    return _resolve_under_root(stored_filename, (settings or get_settings()).upload_path)


def resolve_frame_path(stored_filename: str, settings: Settings | None = None) -> Path:
    return _resolve_under_root(stored_filename, (settings or get_settings()).frame_path)


def _resolve_under_root(stored_filename: str, root: Path) -> Path:
    name = Path(stored_filename).name
    if not name or name != stored_filename or ".." in stored_filename or "/" in stored_filename or "\\" in stored_filename:
        raise AppError("INVALID_PATH", "Invalid media reference.", status_code=400)
    root_resolved = root.resolve()
    candidate = (root_resolved / name).resolve()
    if not str(candidate).startswith(str(root_resolved)):
        raise AppError("INVALID_PATH", "Invalid media reference.", status_code=400)
    return candidate


def delete_file_quietly(path: Path) -> None:
    try:
        if path.exists() and path.is_file():
            path.unlink()
    except OSError:
        pass

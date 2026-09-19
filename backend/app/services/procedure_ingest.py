"""Procedure text extraction, chunking, and storage helpers."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.core.config import Settings, get_settings
from app.core.enums import ProcedureSourceFormat
from app.core.errors import AppError

ALLOWED_PROCEDURE_EXTENSIONS = {".pdf", ".txt", ".md", ".markdown"}
ALLOWED_PROCEDURE_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/octet-stream",  # browsers sometimes omit precise types
}

HEADING_RE = re.compile(r"^(#{1,6}\s+.+|[A-Z][A-Za-z0-9 /&\-]{3,80}:?\s*)$")
NUMBERED_RE = re.compile(r"^\d+\.\s+\S")


@dataclass(frozen=True)
class ChunkDraft:
    chunk_order: int
    section_heading: str | None
    page_number: int | None
    content: str


def content_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def format_from_extension(extension: str) -> ProcedureSourceFormat:
    ext = extension.lower()
    if ext == ".pdf":
        return ProcedureSourceFormat.PDF
    if ext in {".md", ".markdown"}:
        return ProcedureSourceFormat.MARKDOWN
    if ext == ".txt":
        return ProcedureSourceFormat.TXT
    raise AppError(
        "UNSUPPORTED_MEDIA_TYPE",
        "Unsupported procedure format. Allowed: PDF, TXT, Markdown.",
        status_code=415,
    )


def validate_procedure_upload(
    *,
    filename: str | None,
    content_type: str | None,
    size_bytes: int,
    settings: Settings | None = None,
) -> tuple[str, ProcedureSourceFormat]:
    cfg = settings or get_settings()
    from app.services import storage

    safe_name = storage.sanitize_original_filename(filename)
    extension = Path(safe_name).suffix.lower()
    if extension not in ALLOWED_PROCEDURE_EXTENSIONS:
        raise AppError(
            "UNSUPPORTED_MEDIA_TYPE",
            "Unsupported procedure format. Allowed: PDF, TXT, Markdown.",
            status_code=415,
        )
    mime = (content_type or "").split(";")[0].strip().lower()
    if mime and mime not in ALLOWED_PROCEDURE_MIME_TYPES:
        # Allow text/* for markdown variants when extension is valid.
        if not (mime.startswith("text/") and extension in {".txt", ".md", ".markdown"}):
            raise AppError(
                "UNSUPPORTED_MEDIA_TYPE",
                "Unsupported procedure content type.",
                status_code=415,
            )
    if size_bytes <= 0:
        raise AppError("EMPTY_DOCUMENT", "Uploaded procedure is empty.", status_code=422)
    if size_bytes > cfg.max_procedure_size_bytes:
        raise AppError(
            "FILE_TOO_LARGE",
            f"Procedure exceeds the {cfg.max_procedure_size_mb} MB limit.",
            status_code=413,
        )
    return safe_name, format_from_extension(extension)


def extract_text_from_bytes(
    raw: bytes,
    *,
    source_format: ProcedureSourceFormat,
    settings: Settings | None = None,
) -> tuple[str, list[tuple[int | None, str]]]:
    """Return full text and optional page-aware segments [(page, text)]."""
    cfg = settings or get_settings()
    if source_format == ProcedureSourceFormat.PDF:
        return _extract_pdf(raw, cfg)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise AppError(
            "UNREADABLE_DOCUMENT",
            "Procedure text could not be decoded as UTF-8.",
            status_code=422,
        ) from exc
    cleaned = _normalize_text(text)
    _ensure_non_empty(cleaned)
    if len(cleaned) > cfg.max_procedure_text_chars:
        raise AppError(
            "DOCUMENT_TOO_LONG",
            "Extracted procedure text exceeds the configured character limit.",
            status_code=422,
        )
    return cleaned, [(None, cleaned)]


def _extract_pdf(raw: bytes, cfg: Settings) -> tuple[str, list[tuple[int | None, str]]]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover
        raise AppError(
            "DEPENDENCY_MISSING",
            "PDF support requires the pypdf package.",
            status_code=500,
        ) from exc
    try:
        from io import BytesIO

        reader = PdfReader(BytesIO(raw))
        if getattr(reader, "is_encrypted", False):
            raise AppError(
                "UNREADABLE_DOCUMENT",
                "Encrypted PDFs are not supported.",
                status_code=422,
            )
        pages: list[tuple[int | None, str]] = []
        parts: list[str] = []
        for index, page in enumerate(reader.pages, start=1):
            page_text = _normalize_text(page.extract_text() or "")
            if page_text:
                pages.append((index, page_text))
                parts.append(page_text)
        full = _normalize_text("\n\n".join(parts))
    except AppError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise AppError(
            "CORRUPT_DOCUMENT",
            "The PDF could not be parsed. The file may be corrupt.",
            status_code=422,
        ) from exc
    _ensure_non_empty(full)
    if len(full) > cfg.max_procedure_text_chars:
        raise AppError(
            "DOCUMENT_TOO_LONG",
            "Extracted procedure text exceeds the configured character limit.",
            status_code=422,
        )
    return full, pages


def _ensure_non_empty(text: str) -> None:
    if not text.strip():
        raise AppError(
            "EMPTY_DOCUMENT",
            "No readable text was found in the procedure document.",
            status_code=422,
        )


def _normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_procedure_text(
    segments: list[tuple[int | None, str]],
    *,
    max_chars: int,
) -> list[ChunkDraft]:
    """Deterministic chunking by headings / numbered steps / length."""
    drafts: list[ChunkDraft] = []
    order = 0
    current_heading: str | None = None
    buffer = ""
    buffer_page: int | None = None

    def flush() -> None:
        nonlocal order, buffer, buffer_page
        cleaned = buffer.strip()
        if not cleaned:
            buffer = ""
            return
        order += 1
        drafts.append(
            ChunkDraft(
                chunk_order=order,
                section_heading=current_heading,
                page_number=buffer_page,
                content=cleaned,
            )
        )
        buffer = ""

    for page_number, segment in segments:
        for line in segment.splitlines():
            stripped = line.strip()
            if not stripped:
                if len(buffer) >= max_chars * 0.7:
                    flush()
                continue
            is_heading = bool(HEADING_RE.match(stripped)) and not NUMBERED_RE.match(stripped)
            if is_heading:
                flush()
                current_heading = stripped.lstrip("#").strip().rstrip(":")
                buffer_page = page_number
                continue
            candidate = f"{buffer}\n{stripped}".strip() if buffer else stripped
            if len(candidate) > max_chars and buffer:
                flush()
                buffer = stripped
                buffer_page = page_number
            else:
                buffer = candidate
                if buffer_page is None:
                    buffer_page = page_number
                if NUMBERED_RE.match(stripped) and len(buffer) >= max_chars * 0.5:
                    flush()
                    buffer_page = page_number
        flush()
        buffer_page = page_number

    flush()
    if not drafts:
        raise AppError(
            "EMPTY_DOCUMENT",
            "Procedure text could not be split into chunks.",
            status_code=422,
        )
    return drafts


def resolve_procedure_path(stored_filename: str, settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    name = Path(stored_filename).name
    if name != stored_filename or ".." in stored_filename or "/" in stored_filename or "\\" in stored_filename:
        raise AppError("INVALID_PATH", "Invalid procedure media reference.", status_code=400)
    root = cfg.procedure_path
    root.mkdir(parents=True, exist_ok=True)
    candidate = (root / name).resolve()
    if not str(candidate).startswith(str(root.resolve())):
        raise AppError("INVALID_PATH", "Invalid procedure media reference.", status_code=400)
    return candidate

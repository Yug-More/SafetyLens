"""Deterministic local procedure retrieval (no paid APIs required)."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import Settings, get_settings
from app.core.enums import RetrievalMethod
from app.models.procedure import SafetyProcedure
from app.models.procedure_policy import ProcedureChunk

TOKEN_RE = re.compile(r"[a-z0-9]+")

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are",
    "be", "by", "at", "as", "from", "that", "this", "it", "into", "was", "were",
}

DOMAIN_WEIGHTS = {
    "fall": 3.0,
    "fallen": 3.0,
    "falling": 3.0,
    "person": 1.5,
    "down": 2.0,
    "worker": 2.0,
    "medical": 2.5,
    "supervisor": 2.5,
    "emergency": 2.0,
    "evidence": 2.0,
    "footage": 2.0,
    "incident": 1.5,
    "area": 1.2,
    "isolate": 2.0,
    "isolation": 2.0,
    "machinery": 1.8,
    "report": 1.5,
    "documentation": 1.5,
    "assessment": 1.5,
}


@dataclass(frozen=True)
class RankedChunk:
    chunk: ProcedureChunk
    procedure: SafetyProcedure
    score: float
    method: str


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_RE.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def build_query_text(
    *,
    incident_type: str | None,
    title: str | None,
    summary: str | None,
    severity: str | None,
    location: str | None,
    evidence_descriptions: list[str],
    user_query: str | None = None,
) -> str:
    parts = [
        incident_type or "",
        title or "",
        summary or "",
        f"severity {severity}" if severity else "",
        f"location {location}" if location else "",
        " ".join(evidence_descriptions),
        user_query or "",
    ]
    return " ".join(part for part in parts if part).strip()


def score_chunk(query_tokens: list[str], chunk: ProcedureChunk, procedure: SafetyProcedure) -> float:
    if not query_tokens:
        return 0.0
    haystack = " ".join(
        [
            procedure.procedure_code,
            procedure.title,
            procedure.category,
            chunk.section_heading or "",
            chunk.content,
        ]
    )
    doc_tokens = tokenize(haystack)
    if not doc_tokens:
        return 0.0
    doc_counts = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    query_counts = Counter(query_tokens)
    score = 0.0
    for token, q_count in query_counts.items():
        tf = doc_counts.get(token, 0) / doc_len
        if tf <= 0:
            continue
        weight = DOMAIN_WEIGHTS.get(token, 1.0)
        # Mild IDF-style boost for rarer query terms within the query itself.
        idf = 1.0 + math.log(1.0 + len(query_counts) / q_count)
        score += tf * weight * idf
    # Code/title exact-ish boosts for the primary demo path.
    joined_query = " ".join(query_tokens)
    if "fall" in joined_query and "fall" in procedure.procedure_code.lower():
        score += 0.35
    if "fall" in joined_query and "fall" in procedure.title.lower():
        score += 0.25
    if "person" in joined_query and "down" in joined_query and "person" in chunk.content.lower():
        score += 0.15
    return min(score, 1.0)


def retrieve_chunks(
    db: Session,
    *,
    query_text: str,
    settings: Settings | None = None,
    method: RetrievalMethod = RetrievalMethod.LEXICAL,
) -> list[RankedChunk]:
    cfg = settings or get_settings()
    query_tokens = tokenize(query_text)
    procedures = db.scalars(
        select(SafetyProcedure)
        .where(SafetyProcedure.is_active.is_(True))
        .options(selectinload(SafetyProcedure.chunks))
    ).all()

    ranked: list[RankedChunk] = []
    for procedure in procedures:
        chunks = list(procedure.chunks)
        if not chunks and procedure.content:
            # Fallback: treat whole content as one ephemeral ranking unit is not allowed —
            # only stored chunks are retrievable for citations.
            continue
        for chunk in chunks:
            score = score_chunk(query_tokens, chunk, procedure)
            if score >= cfg.retrieval_min_score:
                ranked.append(
                    RankedChunk(
                        chunk=chunk,
                        procedure=procedure,
                        score=score,
                        method=method.value,
                    )
                )

    ranked.sort(
        key=lambda item: (
            -item.score,
            item.procedure.procedure_code,
            item.chunk.chunk_order,
        )
    )
    return ranked[: cfg.retrieval_top_k]

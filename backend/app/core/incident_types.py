"""Canonical incident-type helpers for SafetyLens analyses."""

from __future__ import annotations

PPE_ALIASES = {
    "ppe_violation",
    "ppe_non_compliance",
    "ppe_noncompliance",
    "missing_ppe",
}

PERSON_DOWN_ALIASES = {
    "possible_person_down",
    "person_down",
    "worker_fall",
}

ALLOWED_ANALYSIS_TYPES = {
    "possible_person_down",
    "ppe_noncompliance",
    "no_incident",
    "insufficient_evidence",
}

SUPPORTED_PPE_ITEMS = ("hard_hat", "high_visibility_vest")


def _slug(raw: str) -> str:
    return raw.strip().lower().replace("-", "_").replace(" ", "_")


def normalize_incident_type(raw: str | None) -> str | None:
    if not raw:
        return None
    cleaned = _slug(raw)
    if cleaned in PPE_ALIASES or cleaned.startswith("ppe_"):
        return "ppe_noncompliance"
    if cleaned in PERSON_DOWN_ALIASES or "person_down" in cleaned:
        return "possible_person_down"
    if cleaned in ALLOWED_ANALYSIS_TYPES:
        return cleaned
    return cleaned


def is_ppe_incident(incident_type: str | None, summary: str | None = None) -> bool:
    if normalize_incident_type(incident_type) == "ppe_noncompliance":
        return True
    text = f"{incident_type or ''} {summary or ''}".lower()
    return "ppe" in text and "person_down" not in text and "fall" not in text


def is_person_down_incident(incident_type: str | None, summary: str | None = None) -> bool:
    if is_ppe_incident(incident_type, summary):
        return False
    if normalize_incident_type(incident_type) == "possible_person_down":
        return True
    text = f"{incident_type or ''} {summary or ''}".lower()
    return any(token in text for token in ("person_down", "person-down", "fall"))


def ppe_item_label(item: str) -> str:
    mapping = {
        "hard_hat": "hard hat",
        "high_visibility_vest": "high-visibility vest",
    }
    return mapping.get(item, item.replace("_", " "))

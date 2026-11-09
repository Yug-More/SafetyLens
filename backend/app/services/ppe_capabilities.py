"""Explicit PPE requirements and per-class deployment gates.

Policy configuration is not visual validation. Role/activity/time are supplied
operational context, never inferred worker identity or productivity signals.
"""

from typing import Literal
import json
from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field, field_validator

PpeCategory = Literal[
    "hard_hat",
    "high_visibility_vest",
    "safety_goggles",
    "protective_footwear",
    "protective_gloves",
    "face_shield",
    "hearing_protection",
    "respiratory_protection",
]
PPE_LABELS = {
    "hard_hat": "Hard hat",
    "high_visibility_vest": "High-visibility vest",
    "safety_goggles": "Protective eyewear",
    "protective_footwear": "Protective footwear",
    "protective_gloves": "Protective gloves",
    "face_shield": "Face shield",
    "hearing_protection": "Hearing protection",
    "respiratory_protection": "Respiratory protection",
}


def capability_catalog():
    evidence = json.loads(
        (Path(__file__).parents[1] / "data/ppe-capabilities.json").read_text()
    )
    return [
        dict(
            category=key,
            label=label,
            deployment_enabled=False,
            model_status="experimental_offline_appearance",
            evaluation_artifact=evidence["evaluation_artifact"],
            licensing_status="research_restrictions_not_cleared_for_deployment",
            observed_object_is_certified_equipment=False,
            reason="Appearance diagnostic only; protective rating and wearer compliance remain unvalidated.",
            metrics={
                **evidence["categories"][key],
                "scope": evidence["evaluation_scope"],
            },
        )
        for key, label in PPE_LABELS.items()
    ]


class PpeContextRule(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=100)
    required_ppe: list[PpeCategory] = Field(min_length=1, max_length=8)
    activity: str | None = Field(default=None, min_length=1, max_length=100)
    worker_role: str | None = Field(default=None, min_length=1, max_length=100)
    minute_range: tuple[int, int] | None = None

    @field_validator("minute_range")
    @classmethod
    def valid_range(cls, value):
        if value is not None and (
            not all(0 <= x < 1440 for x in value) or value[0] == value[1]
        ):
            raise ValueError(
                "Minutes must be 0–1439 with distinct start/end; overnight supported"
            )
        return value


def resolve_requirements(
    base, rules, *, activity=None, worker_role=None, minute_of_day=None
):
    required = set(base)
    unknown = set()
    applied = []
    pending = []
    for rule in rules:
        statuses = []
        for field, value in [("activity", activity), ("worker_role", worker_role)]:
            expected = getattr(rule, field)
            if expected is not None:
                statuses.append(None if value is None else value == expected)
        if rule.minute_range is not None:
            start, end = rule.minute_range
            statuses.append(
                None
                if minute_of_day is None
                else (
                    start <= minute_of_day < end
                    if start < end
                    else minute_of_day >= start or minute_of_day < end
                )
            )
        if False in statuses:
            continue
        if None in statuses:
            unknown.update(rule.required_ppe)
            pending.append(rule.label)
        else:
            required.update(rule.required_ppe)
            applied.append(rule.label)
    return dict(
        required_ppe=sorted(required),
        context_unknown_ppe=sorted(unknown - required),
        applied_rules=applied,
        pending_rules=pending,
        context_source="Explicit operator-supplied context; no identity/activity inference",
        deployment_enabled=False,
    )

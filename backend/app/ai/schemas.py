"""Structured multimodal incident analysis contracts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import AnalysisSeverity


class AnalysisEvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frame_id: str = Field(min_length=1)
    timestamp_seconds: float = Field(ge=0)
    observation: str = Field(min_length=1)
    relevance: Literal["supporting", "contradicting", "context"] = "supporting"

    @field_validator("frame_id", "observation")
    @classmethod
    def strip_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned


class IncidentAnalysisResult(BaseModel):
    """Validated structured output from an AI provider."""

    model_config = ConfigDict(extra="forbid")

    incident_detected: bool
    incident_type: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    detailed_analysis: str = Field(min_length=1)
    severity: AnalysisSeverity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[AnalysisEvidenceItem] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    inconclusive: bool = False
    required_ppe: list[str] = Field(default_factory=list)
    observed_ppe: list[str] = Field(default_factory=list)
    possibly_missing_ppe: list[str] = Field(default_factory=list)
    analysis_mode: Literal["configured_demo", "multimodal", "demo_heuristic"] = (
        "demo_heuristic"
    )
    human_review_required: bool = True

    @field_validator("incident_type", "summary", "detailed_analysis")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("recommended_actions", "limitations", "required_ppe", "observed_ppe", "possibly_missing_ppe")
    @classmethod
    def strip_list_items(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            text = item.strip()
            if text:
                cleaned.append(text)
        return cleaned


class FrameAnalysisInput(BaseModel):
    frame_code: str
    timestamp_seconds: float
    absolute_path: str
    content_url: str

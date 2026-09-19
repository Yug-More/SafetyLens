from __future__ import annotations

from abc import ABC, abstractmethod

from app.ai.schemas import FrameAnalysisInput, IncidentAnalysisResult


class AIProvider(ABC):
    """Provider abstraction for multimodal incident analysis."""

    name: str
    is_demo: bool
    is_simulated: bool

    @abstractmethod
    def analyze_frames(
        self,
        *,
        frames: list[FrameAnalysisInput],
        location: str,
        camera_name: str | None,
        video_asset_code: str,
        duration_seconds: float | None,
        camera_id: str | None = None,
        demo_scenario: str | None = None,
        demo_ppe_observation: str | None = None,
        required_ppe: list[str] | None = None,
    ) -> IncidentAnalysisResult:
        """Analyze selected frames and return validated structured output."""


class AIProviderError(Exception):
    """Raised when a provider cannot complete analysis."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable

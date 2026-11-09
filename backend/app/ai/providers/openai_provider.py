"""Optional OpenAI multimodal provider — requires credentials via environment."""

from __future__ import annotations

import base64
import json
import logging
from pathlib import Path
from typing import Any

from app.ai.base import AIProvider, AIProviderError
from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.ai.schemas import FrameAnalysisInput, IncidentAnalysisResult
from app.core.config import Settings
from app.core.enums import AnalysisSeverity

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    name = "openai"
    is_demo = False
    is_simulated = False

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key or not settings.vision_model:
            raise AIProviderError(
                "OPENAI_API_KEY and VISION_MODEL are required for the OpenAI provider",
                retryable=False,
            )
        self._api_key = settings.openai_api_key
        self._model = settings.vision_model
        self._timeout = settings.ai_request_timeout_seconds
        self._max_retries = settings.ai_max_retries
        self._max_dimension = settings.ai_max_image_dimension

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
        if not frames:
            raise AIProviderError(
                "No frames available for OpenAI analysis",
                retryable=False,
            )

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - dependency missing
            raise AIProviderError(
                "openai package is not installed",
                retryable=False,
            ) from exc

        unsupported = sorted(
            set(required_ppe or []) - {"hard_hat", "high_visibility_vest"}
        )
        required_ppe = [
            x for x in (required_ppe or []) if x in {"hard_hat", "high_visibility_vest"}
        ]
        client = OpenAI(api_key=self._api_key, timeout=self._timeout)
        user_text = build_user_prompt(
            frames=frames,
            location=location,
            camera_name=camera_name,
            video_asset_code=video_asset_code,
            duration_seconds=duration_seconds,
            required_ppe=required_ppe,
        )

        content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
        for frame in frames:
            data_url = self._encode_frame(frame.absolute_path)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_url, "detail": "low"},
                }
            )

        last_error: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self._model,
                    temperature=0.1,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": content},
                    ],
                )
                raw = response.choices[0].message.content or ""
                payload = json.loads(raw)
                result = IncidentAnalysisResult.model_validate(payload)
                if unsupported:
                    result = result.model_copy(
                        update={
                            "limitations": [
                                *result.limitations,
                                "Unassessable configured PPE: "
                                + ", ".join(unsupported),
                            ]
                        }
                    )
                self._validate_frame_references(result, frames)
                from app.core.incident_types import (
                    ALLOWED_ANALYSIS_TYPES,
                    normalize_incident_type,
                )

                normalized = (
                    normalize_incident_type(result.incident_type)
                    or result.incident_type
                )
                if normalized not in ALLOWED_ANALYSIS_TYPES:
                    raise AIProviderError(
                        "Provider returned unsupported incident type", retryable=False
                    )
                supported = {"hard_hat", "high_visibility_vest"}
                if (
                    not (
                        set(result.observed_ppe)
                        | set(result.possibly_missing_ppe)
                        | set(result.required_ppe)
                    )
                    <= supported
                ):
                    raise AIProviderError(
                        "Provider returned unsupported PPE class", retryable=False
                    )
                if set(result.observed_ppe) & set(result.possibly_missing_ppe):
                    raise AIProviderError(
                        "Provider returned contradictory PPE observations",
                        retryable=False,
                    )
                if set(result.possibly_missing_ppe) - set(required_ppe or []):
                    raise AIProviderError(
                        "Provider inferred missing PPE outside camera policy",
                        retryable=False,
                    )
                # Never claim PPE noncompliance without a configured camera policy.
                if normalized == "ppe_noncompliance" and not required_ppe:
                    normalized = "insufficient_evidence"
                    return result.model_copy(
                        update={
                            "incident_detected": False,
                            "incident_type": normalized,
                            "severity": AnalysisSeverity.NONE,
                            "inconclusive": True,
                            "analysis_mode": "multimodal",
                            "required_ppe": [],
                            "possibly_missing_ppe": [],
                            "summary": (
                                "No PPE requirement is configured for this camera, "
                                "so PPE noncompliance was not inferred."
                            ),
                            "human_review_required": False,
                        }
                    )
                return result.model_copy(
                    update={
                        "incident_type": normalized,
                        "analysis_mode": "multimodal",
                        "required_ppe": list(required_ppe or result.required_ppe),
                        "human_review_required": True
                        if result.incident_detected
                        else result.human_review_required,
                    }
                )
            except AIProviderError:
                raise
            except Exception as exc:  # noqa: BLE001 - normalize provider failures
                last_error = exc
                logger.warning(
                    "OpenAI analysis attempt %s failed (%s)",
                    attempt + 1,
                    type(exc).__name__,
                )

        raise AIProviderError(
            f"OpenAI analysis failed after retries ({type(last_error).__name__})",
            retryable=True,
        ) from None

    def _encode_frame(self, absolute_path: str) -> str:
        path = Path(absolute_path)
        if not path.is_file():
            raise AIProviderError(
                f"Frame file missing: {path.name}",
                retryable=False,
            )
        # Prefer JPEG bytes as stored; optionally downscale via OpenCV if large.
        raw = path.read_bytes()
        try:
            import cv2
            import numpy as np

            array = np.frombuffer(raw, dtype=np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            if image is not None:
                height, width = image.shape[:2]
                longest = max(height, width)
                if longest > self._max_dimension:
                    scale = self._max_dimension / float(longest)
                    resized = cv2.resize(
                        image,
                        (int(width * scale), int(height * scale)),
                        interpolation=cv2.INTER_AREA,
                    )
                    ok, encoded = cv2.imencode(
                        ".jpg", resized, [int(cv2.IMWRITE_JPEG_QUALITY), 85]
                    )
                    if ok:
                        raw = encoded.tobytes()
        except Exception:  # noqa: BLE001 - fall back to original bytes
            pass

        b64 = base64.b64encode(raw).decode("ascii")
        return f"data:image/jpeg;base64,{b64}"

    @staticmethod
    def _validate_frame_references(
        result: IncidentAnalysisResult,
        frames: list[FrameAnalysisInput],
    ) -> None:
        allowed = {frame.frame_code for frame in frames}
        for item in result.evidence:
            if item.frame_id not in allowed:
                raise AIProviderError(
                    f"Provider returned unknown frame_id '{item.frame_id}'",
                    retryable=False,
                )

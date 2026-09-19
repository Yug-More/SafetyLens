"""Lightweight temporal person-down detection for SafetyLens."""

from .engine import DetectorEngine
from .evidence_buffer import EvidenceCapture, EvidenceWindowBuffer, FrameSample
from .metrics import derive_pose_metrics
from .models import (
    DetectionEvent,
    DetectorConfig,
    DetectorResult,
    DetectorState,
    Landmark,
    PoseMetrics,
    PoseObservation,
)

__all__ = [
    "DetectionEvent",
    "DetectorConfig",
    "DetectorEngine",
    "DetectorResult",
    "DetectorState",
    "Landmark",
    "EvidenceCapture",
    "EvidenceWindowBuffer",
    "FrameSample",
    "PoseMetrics",
    "PoseObservation",
    "derive_pose_metrics",
]

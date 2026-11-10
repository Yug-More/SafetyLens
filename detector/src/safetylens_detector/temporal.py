"""Causal, CPU-only temporal pose classifier for research, never a fall probability.

JSON checkpoints contain numbers and provenance, not executable/pickled objects.
No model is shipped or silently substituted for the deployed temporal rules.
"""

from collections import deque
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from .metrics import derive_pose_metrics
from .models import DetectionEvent, DetectorResult, DetectorState

FEATURE_VERSION = "causal-pose-summary-v1"
BASE_FEATURES = (
    "quality",
    "angle",
    "body_ratio",
    "shoulder_y",
    "hip_velocity",
    "motion",
)
FEATURE_NAMES = (
    tuple(BASE_FEATURES)
    + tuple(
        f"{window}s_{stat}_{name}"
        for window in (0.5, 1.0, 2.0)
        for stat in ("mean", "range", "change")
        for name in BASE_FEATURES
    )
    + ("window_coverage", "observation_density")
)


class CausalFeatures:
    def __init__(self):
        self.history = deque(maxlen=128)
        self.previous = None

    def reset(self):
        self.history.clear()
        self.previous = None

    def process(self, observation):
        import numpy as np

        t = observation.timestamp_seconds
        if self.previous and t <= self.previous.timestamp_seconds:
            raise ValueError("Temporal timestamps must strictly increase")
        if self.previous and t - self.previous.timestamp_seconds > 0.75:
            self.reset()
        m = derive_pose_metrics(observation, self.previous)
        if m.pose_quality < 0.6 or m.torso_angle_degrees_from_vertical is None:
            self.reset()
            return None, m
        values = np.array(
            [
                m.pose_quality,
                (m.torso_angle_degrees_from_vertical or 0) / 90,
                min(m.bbox_width_height_ratio or 0, 4) / 4,
                m.shoulder_center_y or 0,
                max(-4, min(4, m.downward_hip_velocity_body_lengths_per_second or 0))
                / 4,
                min(m.mean_landmark_motion_body_lengths_per_second or 0, 4) / 4,
            ],
            dtype=float,
        )
        self.history.append((t, values))
        while self.history and t - self.history[0][0] > 2:
            self.history.popleft()
        output = list(values)
        for window in (0.5, 1.0, 2.0):
            rows = np.array([v for stamp, v in self.history if t - stamp <= window])
            output.extend(rows.mean(axis=0))
            output.extend(np.ptp(rows, axis=0))
            output.extend(rows[-1] - rows[0])
        coverage = t - self.history[0][0]
        output.extend([min(coverage / 2, 1), min(len(self.history) / 25, 1)])
        self.previous = observation
        return np.asarray(output), m


class TemporalModel:
    def __init__(self, checkpoint):
        import numpy as np

        self.checkpoint = checkpoint
        if checkpoint.get("feature_version") != FEATURE_VERSION or checkpoint.get(
            "feature_names"
        ) != list(FEATURE_NAMES):
            raise ValueError("Incompatible temporal features")
        self.mean, self.scale = (
            np.asarray(checkpoint[k], dtype=float) for k in ("mean", "scale")
        )
        self.w1, self.b1, self.w2, self.b2 = (
            np.asarray(checkpoint[k], dtype=float) for k in ("w1", "b1", "w2", "b2")
        )
        n = len(FEATURE_NAMES)
        if (
            self.mean.shape != (n,)
            or self.scale.shape != (n,)
            or (self.scale <= 0).any()
        ):
            raise ValueError("Invalid normalization")
        h = self.b1.size
        if (
            self.w1.shape != (n, h)
            or self.b1.shape != (h,)
            or self.w2.shape != (h,)
            or self.b2.shape != ()
        ):
            raise ValueError("Invalid network dimensions")
        if not 1 <= h <= 64 or not all(
            np.isfinite(a).all()
            for a in (self.mean, self.scale, self.w1, self.b1, self.w2, self.b2)
        ):
            raise ValueError("Invalid network values")
        self.linear = bool(checkpoint.get("linear", False))
        threshold = checkpoint.get("threshold", 0.5)
        if not isinstance(threshold, (int, float)) or not 0 < threshold < 1:
            raise ValueError("Invalid score threshold")
        self.threshold = threshold

    @classmethod
    def load(cls, path, *, expected_sha256):
        with Path(path).open("rb") as handle:
            raw = handle.read(2_000_001)
        if len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise ValueError("Temporal checkpoint size/hash mismatch")
        return cls(json.loads(raw))

    def score(self, features):
        import numpy as np

        x = np.asarray(features, dtype=float)
        if x.shape[-1] != len(FEATURE_NAMES) or not np.isfinite(x).all():
            raise ValueError("Invalid input features")
        z = np.clip((x - self.mean) / self.scale, -8, 8)
        hidden = z @ self.w1 + self.b1
        if not self.linear:
            hidden = np.tanh(hidden)
        logits = hidden @ self.w2 + self.b2
        return 1 / (1 + np.exp(-np.clip(logits, -30, 30)))


DECISION_VERSION = "temporal-decision-v2"


class TemporalDecision:
    """Shared runtime/evaluation decision state; no invisible recovery credit."""

    def __init__(self, threshold):
        self.threshold = threshold
        self.since = None
        self.latched = False
        self.recovery = None
        self.last_timestamp = None
        self.state = DetectorState.MONITORING

    def update(self, timestamp, score, metrics, coverage):
        import math

        if (
            not math.isfinite(timestamp)
            or timestamp < 0
            or (self.last_timestamp is not None and timestamp <= self.last_timestamp)
        ):
            raise ValueError("Decision timestamps must strictly increase")
        if self.last_timestamp is not None and timestamp - self.last_timestamp > 0.75:
            self.since = self.recovery = None
        self.last_timestamp = timestamp
        if score is None:
            self.since = self.recovery = None
            self.state = DetectorState.LOW_VISIBILITY
            return self.state, False
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Invalid temporal score")
        if self.latched:
            upright = (
                metrics.torso_angle_degrees_from_vertical < 35
                and (metrics.bbox_width_height_ratio or 10) < 1.2
            )
            self.recovery = (
                (timestamp if self.recovery is None else self.recovery)
                if upright
                else None
            )
            if self.recovery is not None and timestamp - self.recovery >= 1:
                self.latched = False
                self.since = self.recovery = None
            self.state = DetectorState.COOLDOWN
            return self.state, False
        if score >= self.threshold:
            self.since = timestamp if self.since is None else self.since
            self.state = DetectorState.CONFIRMING
            if timestamp - self.since >= 0.083 and coverage >= 0.25:
                self.latched = True
                self.state = DetectorState.INCIDENT
                return self.state, True
        else:
            self.since = None
            self.state = DetectorState.MONITORING
        return self.state, False


class TemporalDetectorEngine:
    """Bounded per-track inference using exactly the evaluator's decision state."""

    def __init__(self, model):
        self.model = model
        self.tracks = {}

    def _track(self, key):
        if key not in self.tracks and len(self.tracks) >= 64:
            self.tracks.pop(next(iter(self.tracks)))
        return self.tracks.setdefault(
            key,
            {
                "features": CausalFeatures(),
                "decision": TemporalDecision(self.model.threshold),
            },
        )

    def forget_track(self, track_id):
        self.tracks.pop(track_id, None)

    def mark_missing(self, track_id, *, timestamp_seconds=None):
        track = self._track(track_id)
        decision = track["decision"]
        previous = decision.state
        if timestamp_seconds is None:
            # Legacy callers may not provide time; never fabricate a recovery.
            decision.since = decision.recovery = None
            decision.state = DetectorState.LOW_VISIBILITY
        else:
            decision.update(timestamp_seconds, None, None, 0)
        return DetectorResult(
            track_id, previous, decision.state, None, reasons=("track_missing",)
        )

    def process(self, observation):
        key = observation.track_id
        track = self._track(key)
        features, metrics = track["features"].process(observation)
        decision = track["decision"]
        previous = decision.state
        score = float(self.model.score(features)) if features is not None else None
        state, triggered = decision.update(
            observation.timestamp_seconds,
            score,
            metrics,
            features[-2] if features is not None else 0,
        )
        event = None
        if triggered:
            event = DetectionEvent(
                "1.0",
                str(uuid4()),
                "possible_person_down",
                observation.source_id,
                key,
                observation.timestamp_seconds,
                observation.source_timestamp_seconds,
                state,
                ("learned_temporal_candidate",),
                metrics.pose_quality,
                metrics,
                (
                    "experimental_learned_pose_classifier",
                    "score_is_not_calibrated_fall_probability",
                    "requires_human_verification",
                    DECISION_VERSION,
                ),
            )
        return DetectorResult(
            key,
            previous,
            state,
            metrics,
            event,
            (f"temporal_score={score:.4f}",)
            if score is not None
            else ("insufficient_pose_quality",),
        )

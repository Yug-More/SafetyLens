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
        raw = Path(path).read_bytes()
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


class TemporalDetectorEngine:
    """Opt-in research event engine: bounded per-track history and abstention."""

    def __init__(self, model):
        self.model = model
        self.tracks = {}

    def forget_track(self, track_id):
        self.tracks.pop(track_id, None)

    def mark_missing(self, track_id):
        self.forget_track(track_id)
        return DetectorResult(
            track_id,
            DetectorState.MONITORING,
            DetectorState.LOW_VISIBILITY,
            None,
            reasons=("track_missing",),
        )

    def process(self, observation):
        key = observation.track_id
        # Callers expire tracks, but also impose an independent resource bound.
        if key not in self.tracks and len(self.tracks) >= 64:
            self.tracks.pop(next(iter(self.tracks)))
        track = self.tracks.setdefault(
            key,
            {
                "features": CausalFeatures(),
                "since": None,
                "latched": False,
                "recovery": None,
            },
        )
        prior = track["features"].previous
        if prior and observation.timestamp_seconds - prior.timestamp_seconds > 0.75:
            track["since"] = None
        features, metrics = track["features"].process(observation)
        t = observation.timestamp_seconds
        if features is None:
            track["since"] = None
            return DetectorResult(
                key,
                DetectorState.MONITORING,
                DetectorState.LOW_VISIBILITY,
                metrics,
                reasons=("insufficient_pose_quality",),
            )
        score = float(self.model.score(features))
        event = None
        state = DetectorState.MONITORING
        if track["latched"]:
            # Sustained upright posture, rather than score noise, rearms the track.
            upright = (
                metrics.torso_angle_degrees_from_vertical < 35
                and (metrics.bbox_width_height_ratio or 10) < 1.2
            )
            track["recovery"] = (
                (track["recovery"] if track["recovery"] is not None else t)
                if upright
                else None
            )
            if track["recovery"] is not None and t - track["recovery"] >= 1:
                track["latched"] = False
                track["since"] = None
            state = DetectorState.COOLDOWN
        elif score >= self.model.threshold:
            track["since"] = t if track["since"] is None else track["since"]
            state = DetectorState.CONFIRMING
            if t - track["since"] >= 0.083 and features[-2] >= 0.25:
                track["latched"] = True
                state = DetectorState.INCIDENT
                event = DetectionEvent(
                    "1.0",
                    str(uuid4()),
                    "possible_person_down",
                    observation.source_id,
                    key,
                    t,
                    observation.source_timestamp_seconds,
                    state,
                    ("learned_temporal_candidate",),
                    metrics.pose_quality,
                    metrics,
                    (
                        "experimental_learned_pose_classifier",
                        "score_is_not_calibrated_fall_probability",
                        "requires_human_verification",
                    ),
                )
        else:
            track["since"] = None
        return DetectorResult(
            key,
            DetectorState.MONITORING,
            state,
            metrics,
            event,
            (f"temporal_score={score:.4f}",),
        )

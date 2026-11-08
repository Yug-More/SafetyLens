"""Short-lived geometric pose tracks; no identity/biometric recognition.

Mutual unambiguous matches preserve temporal state. Crossings abstain rather
than combining two people's motion; expired tracks must discard detector state.
"""

from dataclasses import replace
from math import hypot, isfinite
from .ppe import iou


class PoseTracker:
    def __init__(self, *, maximum_gap_seconds=0.5, ambiguity_margin=0.10):
        self.maximum_gap = maximum_gap_seconds
        self.margin = ambiguity_margin
        self.tracks = {}
        self.sequence = 0
        self.last_timestamp = None

    @staticmethod
    def box(observation):
        points = [p for p in observation.landmarks.values() if p.visibility >= 0.5]
        if len(points) < 4:
            return None
        x, y = [p.x for p in points], [p.y for p in points]
        box = (min(x), min(y), max(x), max(y))
        return box if box[2] > box[0] and box[3] > box[1] else None

    @staticmethod
    def similarity(a, b):
        scale = max(
            hypot(a[2] - a[0], a[3] - a[1]), hypot(b[2] - b[0], b[3] - b[1]), 0.01
        )
        distance = (
            hypot((a[0] + a[2] - b[0] - b[2]) / 2, (a[1] + a[3] - b[1] - b[3]) / 2)
            / scale
        )
        overlap = iou(a, b)
        if overlap < 0.1 and distance > 0.35:
            return 0
        return 0.7 * overlap + 0.3 * max(0, 1 - distance)

    def update(self, timestamp, observations):
        if (
            not isfinite(timestamp)
            or timestamp < 0
            or (self.last_timestamp is not None and timestamp <= self.last_timestamp)
        ):
            raise ValueError("Track timestamps must strictly increase")
        if len(observations) > 4:
            raise ValueError("At most four poses supported")
        self.last_timestamp = timestamp
        expired = [
            key
            for key, item in self.tracks.items()
            if timestamp - item["time"] > self.maximum_gap
        ]
        for key in expired:
            del self.tracks[key]
        boxes = [self.box(o) for o in observations]
        scores = {
            (i, key): self.similarity(box, item["box"])
            for i, box in enumerate(boxes)
            if box
            for key, item in self.tracks.items()
        }
        candidates = {
            i: sorted(
                ((v, key) for (idx, key), v in scores.items() if idx == i and v > 0),
                reverse=True,
            )
            for i in range(len(observations))
        }
        tracked = []
        ambiguous = 0
        for i, observation in enumerate(observations):
            if boxes[i] is None:
                continue  # Insufficient geometry never inherits another person's history.
            choices = candidates[i]
            key = None
            if choices:
                best, proposed = choices[0]
                rivals = sorted(
                    (v for (idx, k), v in scores.items() if k == proposed and idx != i),
                    reverse=True,
                )
                unambiguous = (
                    len(choices) < 2 or best - choices[1][0] > self.margin
                ) and (not rivals or best - rivals[0] > self.margin)
                if unambiguous:
                    key = proposed
                else:
                    ambiguous += 1
            if key is None:
                self.sequence += 1
                key = f"pose-{self.sequence}"
            self.tracks[key] = {"time": timestamp, "box": boxes[i]}
            tracked.append(replace(observation, track_id=key))
        # Also bound memory under arbitrarily dense caller timestamps.
        while len(self.tracks) > 64:
            oldest = min(self.tracks, key=lambda key: self.tracks[key]["time"])
            del self.tracks[oldest]
            expired.append(oldest)
        # Old ambiguous associations expire without bridging histories.
        return tracked, expired, ambiguous

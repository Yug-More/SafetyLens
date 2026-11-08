"""Real ONNX PPE inference and conservative, exclusive per-person association.

Only manifest-declared person/hard_hat/high_visibility_vest classes are used.
No detected PPE is treated as evidence of absence: missing observations stay uncertain.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Box:
    label: str
    score: float
    xyxy: tuple[float, float, float, float]

    def __post_init__(self):
        if not 0 <= self.score <= 1 or not all(math.isfinite(x) for x in self.xyxy):
            raise ValueError("Invalid box values")
        x1, y1, x2, y2 = self.xyxy
        if x2 <= x1 or y2 <= y1:
            raise ValueError("Box must have positive area")


def iou(a, b):
    left, top, right, bottom = (
        max(a[0], b[0]),
        max(a[1], b[1]),
        min(a[2], b[2]),
        min(a[3], b[3]),
    )
    area = max(0, right - left) * max(0, bottom - top)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - area
    return area / union if union else 0


def associate_ppe(
    boxes: list[Box], required: list[str], *, threshold: float = 0.5
) -> list[dict]:
    people = [b for b in boxes if b.label == "person" and b.score >= threshold]
    assignments = {i: {} for i in range(len(people))}
    ambiguous = set()
    for item in boxes:
        if (
            item.label not in {"hard_hat", "high_visibility_vest"}
            or item.score < threshold
        ):
            continue
        x1, y1, x2, y2 = item.xyxy
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        candidates = []
        for i, person in enumerate(people):
            px, py, qx, qy = person.xyxy
            region = (0, 0.38) if item.label == "hard_hat" else (0.18, 0.78)
            if px <= cx <= qx and py + region[0] * (qy - py) <= cy <= py + region[1] * (
                qy - py
            ):
                distance = abs(cx - (px + qx) / 2) / (qx - px)
                candidates.append((distance, i))
        candidates.sort()
        if len(candidates) > 1 and candidates[1][0] - candidates[0][0] < 0.15:
            ambiguous.update(i for _, i in candidates)
            continue
        if candidates:
            idx = candidates[0][1]
            assignments[idx][item.label] = max(
                item.score, assignments[idx].get(item.label, 0)
            )
    rows = []
    for i, person in enumerate(people):
        seen = sorted(assignments[i])
        unknown = sorted(set(required) - set(seen))
        rows.append(
            {
                "person_index": i,
                "box": person.xyxy,
                "observed": seen,
                "possibly_missing": unknown,
                "status": "inconclusive"
                if unknown or i in ambiguous
                else "observed_compliant",
                "association_ambiguous": i in ambiguous,
                "scores": assignments[i],
            }
        )
    return rows


class PpeTemporalMonitor:
    def __init__(self, *, hold_seconds=2.0, max_gap_seconds=0.75):
        self.hold, self.max_gap = hold_seconds, max_gap_seconds
        self._previous = {}
        self._last_timestamp = None

    def process(self, timestamp, people):
        if (
            not math.isfinite(timestamp)
            or timestamp < 0
            or (self._last_timestamp is not None and timestamp <= self._last_timestamp)
        ):
            raise ValueError("PPE timestamps must strictly increase")
        self._last_timestamp = timestamp
        # Conservative IoU association. Ambiguous matches reset persistence.
        updated = {}
        result = []
        used = set()
        for person in people:
            candidates = sorted(
                (
                    (iou(person["box"], old["box"]), key)
                    for key, old in self._previous.items()
                    if timestamp - old["time"] <= self.max_gap and key not in used
                ),
                reverse=True,
            )
            matched = bool(
                candidates
                and candidates[0][0] > 0.5
                and (len(candidates) < 2 or candidates[0][0] - candidates[1][0] > 0.15)
            )
            if matched:
                key = candidates[0][1]
                old = self._previous[key]
                used.add(key)
                since = (
                    old["since"]
                    if old["missing"] == person["possibly_missing"]
                    else timestamp
                )
            else:
                from uuid import uuid4

                key = str(uuid4())
                since = timestamp
            suspect = (
                bool(person["possibly_missing"]) and not person["association_ambiguous"]
            )
            stable = suspect and timestamp - since >= self.hold
            result.append(
                {
                    **person,
                    "track_id": key,
                    "review_required": stable,
                    "status": "possible_noncompliance" if stable else person["status"],
                }
            )
            updated[key] = {
                "box": person["box"],
                "time": timestamp,
                "since": since,
                "missing": person["possibly_missing"],
            }
        self._previous = updated
        return result


class OnnxPpeDetector:
    def __init__(self, manifest_path: str | Path, *, threshold=0.5, nms_iou=0.45):
        import onnxruntime as ort

        if not (0 <= threshold <= 1 and 0 < nms_iou <= 1):
            raise ValueError("PPE thresholds must be finite probability/IoU values")
        self.manifest = json.loads(Path(manifest_path).read_text())
        for key in ["weights", "sha256", "source", "license", "classes", "input_size"]:
            if not self.manifest.get(key):
                raise ValueError(f"Model manifest missing {key}")
        weights = (Path(manifest_path).parent / self.manifest["weights"]).resolve()
        if hashlib.sha256(weights.read_bytes()).hexdigest() != self.manifest["sha256"]:
            raise ValueError("PPE model checksum mismatch")
        self.classes = self.manifest["classes"]
        self.size = int(self.manifest["input_size"])
        if not {"person", "hard_hat", "high_visibility_vest"} <= set(
            self.classes.values()
        ):
            raise ValueError(
                "Manifest must include person, hard_hat and high_visibility_vest"
            )
        self.threshold, self.nms = threshold, nms_iou
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(weights), sess_options=options, providers=["CPUExecutionProvider"]
        )
        inputs = self.session.get_inputs()
        if len(inputs) != 1 or inputs[0].type != "tensor(float)" or inputs[0].shape != [1, 3, self.size, self.size]:
            raise ValueError("Unsupported ONNX input; expected float32 fixed [1,3,size,size]")
        self.input = inputs[0].name

    def detect(self, frame):
        import cv2
        import numpy as np

        height, width = frame.shape[:2]
        scale = min(self.size / width, self.size / height)
        nw, nh = round(width * scale), round(height * scale)
        left, top = (self.size - nw) // 2, (self.size - nh) // 2
        image = np.full((self.size, self.size, 3), 114, dtype=np.uint8)
        image[top : top + nh, left : left + nw] = cv2.resize(frame, (nw, nh))
        tensor = (
            np.ascontiguousarray(
                image[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32
            )
            / 255
        )
        raw = np.asarray(self.session.run(None, {self.input: tensor})[0])
        if raw.ndim != 3 or raw.shape[0] != 1:
            raise ValueError(
                "Unsupported ONNX output; expected YOLOv8 raw detection head"
            )
        # Support [1,4+C,N] and [1,N,4+C], not end-to-end or objectness heads.
        rows = raw[0].T if raw.shape[1] < raw.shape[2] else raw[0]
        expected = int(
            self.manifest.get(
                "number_of_classes", max(int(k) for k in self.classes) + 1
            )
        )
        if rows.shape[1] != 4 + expected:
            raise ValueError("ONNX class count does not match manifest")
        boxes = []
        for row in rows:
            idx = int(np.argmax(row[4:]))
            score = float(row[4 + idx])
            label = self.classes.get(str(idx))
            if (
                label not in {"person", "hard_hat", "high_visibility_vest"}
                or score < self.threshold
            ):
                continue
            cx, cy, w, h = map(float, row[:4])
            xyxy = (
                max(0, (cx - w / 2 - left) / scale),
                max(0, (cy - h / 2 - top) / scale),
                min(width, (cx + w / 2 - left) / scale),
                min(height, (cy + h / 2 - top) / scale),
            )
            if xyxy[2] > xyxy[0] and xyxy[3] > xyxy[1]:
                boxes.append(Box(label, score, xyxy))
        kept = []
        for box in sorted(boxes, key=lambda b: b.score, reverse=True):
            if not any(
                x.label == box.label and iou(x.xyxy, box.xyxy) > self.nms for x in kept
            ):
                kept.append(box)
        return kept


def draw_ppe_overlay(frame, boxes, people):
    """Render actual detections; candidate absence stays explicitly unconfirmed."""
    import cv2
    output = frame.copy()
    for box in boxes:
        x1, y1, x2, y2 = map(round, box.xyxy)
        cv2.rectangle(output, (x1, y1), (x2, y2), (255, 180, 0), 2)
        cv2.putText(output, f"{box.label} {box.score:.2f}", (x1, max(15, y1-5)),
                    cv2.FONT_HERSHEY_SIMPLEX, .4, (255, 180, 0), 1)
    for person in people:
        x1, y1, _, _ = map(round, person['box'])
        label = 'REVIEW: possible missing PPE' if person.get('review_required') else person['status']
        cv2.putText(output, label, (x1, y1+18), cv2.FONT_HERSHEY_SIMPLEX, .4, (0, 200, 255), 1)
    return output

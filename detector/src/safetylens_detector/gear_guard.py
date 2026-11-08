"""Offline-only Qualcomm GearGuardNet ONNX adapter (helmet/vest, no person).

Protocol checked against official ai-hub-models v0.65.0. This does not make a
person-specific compliance system. The camera worker remains deployment-disabled.
"""

from pathlib import Path
import hashlib
import json
from .ppe import Box, iou


class GearGuardDetector:
    classes = {"0": "hard_hat", "1": "high_visibility_vest"}

    def __init__(self, manifest_path, *, threshold=0.05, nms_iou=0.7):
        import onnxruntime as ort

        if not 0 <= threshold <= 1 or not 0 < nms_iou <= 1:
            raise ValueError("Invalid inference thresholds")
        self.manifest = json.loads(Path(manifest_path).read_text())
        root = Path(manifest_path).parent
        for name, digest in self.manifest["files_sha256"].items():
            path = (root / name).resolve()
            if (
                not path.is_relative_to(root.resolve())
                or hashlib.sha256(path.read_bytes()).hexdigest() != digest
            ):
                raise ValueError("GearGuard model asset checksum mismatch")
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(root / self.manifest["weights"]),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        inputs = self.session.get_inputs()
        if (
            len(inputs) != 1
            or inputs[0].shape != [1, 3, 320, 192]
            or inputs[0].type != "tensor(float)"
        ):
            raise ValueError("Unexpected GearGuard input contract")
        self.input = inputs[0].name
        if [x.name for x in self.session.get_outputs()] != [
            "boxes",
            "scores",
            "class_idx",
        ]:
            raise ValueError("Unexpected GearGuard output contract")
        self.threshold, self.nms = threshold, nms_iou

    def detect(self, frame):
        import numpy as np
        import cv2

        h, w = frame.shape[:2]
        scale = min(192 / w, 320 / h)
        nw, nh = round(w * scale), round(h * scale)
        left, top = (192 - nw) // 2, (320 - nh) // 2
        padded = np.zeros((320, 192, 3), dtype=np.uint8)
        padded[top : top + nh, left : left + nw] = cv2.resize(
            frame, (nw, nh), interpolation=cv2.INTER_LINEAR
        )
        tensor = (
            np.ascontiguousarray(
                padded[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32
            )
            / 255
        )
        coordinates, scores, classes = self.session.run(None, {self.input: tensor})
        boxes = []
        for xyxy, score, index in zip(coordinates[0], scores[0], classes[0]):
            if score < self.threshold:
                continue
            label = self.classes.get(str(int(index)))
            if not label:
                continue
            x1, y1, x2, y2 = map(float, xyxy)
            box = (
                max(0, (x1 - left) / scale),
                max(0, (y1 - top) / scale),
                min(w, (x2 - left) / scale),
                min(h, (y2 - top) / scale),
            )
            if box[2] > box[0] and box[3] > box[1]:
                boxes.append(Box(label, float(score), box))
        kept = []
        for box in sorted(boxes, key=lambda x: x.score, reverse=True):
            if not any(
                old.label == box.label and iou(old.xyxy, box.xyxy) > self.nms
                for old in kept
            ):
                kept.append(box)
        return kept

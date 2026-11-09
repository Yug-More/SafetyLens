"""Export the official research checkpoint outside Git and verify numeric parity.

Run in an isolated environment with pinned PyTorch/Ultralytics/ONNX; downloading
or loading arbitrary pickle checkpoints is not supported. Use official source,
explicit caller-supplied checksum and research licensing review.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/safetylens-ultralytics")
p = argparse.ArgumentParser()
p.add_argument("--checkpoint", required=True, type=Path)
p.add_argument("--sha256", required=True)
p.add_argument("--image", required=True, type=Path)
p.add_argument("--report", required=True, type=Path)
a = p.parse_args()
if hashlib.sha256(a.checkpoint.read_bytes()).hexdigest() != a.sha256:
    raise ValueError("Checkpoint hash mismatch")
from ultralytics import YOLO
import torch
import onnxruntime as ort
import onnx
import cv2
import numpy as np

model = YOLO(str(a.checkpoint))
onnx_path = Path(
    model.export(
        format="onnx", imgsz=640, opset=12, simplify=False, dynamic=False, device="cpu"
    )
)
frame = cv2.imread(str(a.image))
h, w = frame.shape[:2]
scale = min(640 / w, 640 / h)
nw, nh = round(w * scale), round(h * scale)
left, top = (640 - nw) // 2, (640 - nh) // 2
image = np.full((640, 640, 3), 114, dtype=np.uint8)
image[top : top + nh, left : left + nw] = cv2.resize(frame, (nw, nh))
tensor = (
    np.ascontiguousarray(image[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32)
    / 255
)
with torch.no_grad():
    expected = model.model(torch.from_numpy(tensor))[0].numpy()
opts = ort.SessionOptions()
opts.intra_op_num_threads = 1
session = ort.InferenceSession(
    str(onnx_path), sess_options=opts, providers=["CPUExecutionProvider"]
)
actual = session.run(None, {session.get_inputs()[0].name: tensor})[0]
geometry = float(np.max(np.abs(expected[:, :4] - actual[:, :4])))
score = float(np.max(np.abs(expected[:, 4:] - actual[:, 4:])))
# Predeclared parity gate: score error <=.001, coordinate error <=.1 input pixel.
passed = score <= 0.001 and geometry <= 0.1
result = {
    "checkpoint_sha256": a.sha256,
    "onnx_sha256": hashlib.sha256(onnx_path.read_bytes()).hexdigest(),
    "graph_sha256": hashlib.sha256(
        onnx.load(onnx_path).graph.SerializeToString()
    ).hexdigest(),
    "shape": list(actual.shape),
    "class_names": model.names,
    "max_score_absolute_error": score,
    "max_coordinate_absolute_error_pixels": geometry,
    "parity_passed": passed,
    "protocol": "Same fixed RGB/255/114-centered-letterbox tensor; CPU float export; one diagnostic image only",
    "torch_version": torch.__version__,
}
a.report.write_text(json.dumps(result, indent=2) + "\n")
if not passed:
    raise ValueError("Export parity gate failed")

# The export's embedded class map, not README list position, defines decoding.
expected = {
    0: "person",
    2: "ear-mufs",
    4: "face-guard",
    5: "face-mask",
    8: "glasses",
    9: "gloves",
    10: "helmet",
    14: "shoes",
    16: "safety-vest",
}
if any(model.names.get(k) != v for k, v in expected.items()):
    raise ValueError("Unexpected publisher checkpoint classes; inspect mapping")
labels = {
    0: "person",
    2: "earmuffs",
    4: "face_shield",
    5: "medical_mask",
    8: "ordinary_eyewear",
    9: "gloves",
    10: "hard_hat",
    14: "ordinary_footwear",
    16: "high_visibility_vest",
}
manifest = {
    "weights": os.path.relpath(onnx_path, a.report.parent),
    "sha256": result["onnx_sha256"],
    "source": "https://github.com/ahmadmughees/SH17dataset/releases/download/v1/yolo8n.pt",
    "license": "AGPL-3.0 model/export; SH17 CC-BY-NC-SA-4.0 research data; no deployment clearance",
    "classes": {str(k): v for k, v in labels.items()},
    "input_size": 640,
    "number_of_classes": 17,
    "checkpoint_sha256": a.sha256,
}
(a.report.parent / "sh17-model-manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n"
)

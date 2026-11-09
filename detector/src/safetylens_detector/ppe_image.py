"""Actual offline multi-class ONNX inference with per-person unknown-safe review."""

import argparse
import json
from pathlib import Path
from time import perf_counter
from .ppe import OnnxPpeDetector, draw_ppe_overlay
from .compliance import assess_people, CATEGORIES


def main():
    import cv2

    p = argparse.ArgumentParser()
    p.add_argument("image", type=Path)
    p.add_argument("--model-manifest", required=True, type=Path)
    p.add_argument("--required", nargs="*", choices=sorted(CATEGORIES), default=[])
    p.add_argument("--threshold", type=float, default=0.5)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--overlay", type=Path)
    a = p.parse_args()
    frame = cv2.imread(str(a.image))
    if frame is None:
        p.error("Unreadable image")
    detector = OnnxPpeDetector(a.model_manifest, threshold=a.threshold)
    start = perf_counter()
    boxes = detector.detect(frame)
    people = assess_people(boxes, a.required, threshold=a.threshold)
    elapsed = perf_counter() - start
    output = {
        "mode": "actual_offline_onnx",
        "model_sha256": detector.manifest["sha256"],
        "deployment_enabled": False,
        "required_ppe": a.required,
        "inference_association_seconds": elapsed,
        "objects": [b.__dict__ for b in boxes],
        "people": people,
        "association_accuracy": None,
        "compliance_accuracy": None,
    }
    a.output.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    if a.overlay:
        overlay = draw_ppe_overlay(
            frame,
            boxes,
            [
                {"box": x["person_box"], "status": "UNKNOWN - visual rating unverified"}
                for x in people
            ],
        )
        cv2.imwrite(str(a.overlay), overlay)
    print(
        "Actual appearance objects:",
        len(boxes),
        "people:",
        len(people),
        "deployment disabled",
    )


if __name__ == "__main__":
    main()

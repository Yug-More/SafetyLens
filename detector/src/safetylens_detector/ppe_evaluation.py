"""Labeled image benchmark for a supplied licensed, disjoint PPE test manifest.

Reports interpolated AP at 0.50 and 0.50:0.95. No dataset or labels are generated.
Unannotated classes remain null and are excluded from the macro-average explicitly.
"""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
from .ppe import OnnxPpeDetector, iou, associate_ppe

CLASSES = ("person", "hard_hat", "high_visibility_vest")


def average_precision(records, ground_truth_count):
    if not ground_truth_count:
        return None
    hits = 0
    precisions = []
    recalls = []
    for index, (_, correct) in enumerate(
        sorted(records, key=lambda x: x[0], reverse=True), start=1
    ):
        hits += bool(correct)
        precisions.append(hits / index)
        recalls.append(hits / ground_truth_count)
    return (
        sum(
            max((p for p, r in zip(precisions, recalls) if r >= level / 100), default=0)
            for level in range(101)
        )
        / 101
    )


def score_class(samples, label, threshold):
    records = []
    total = 0
    for sample in samples:
        truths = [x["xyxy"] for x in sample["ground_truth"] if x["label"] == label]
        total += len(truths)
        used = set()
        for prediction in sorted(
            [x for x in sample["predictions"] if x["label"] == label],
            key=lambda x: x["score"],
            reverse=True,
        ):
            candidates = sorted(
                (
                    (iou(prediction["xyxy"], box), index)
                    for index, box in enumerate(truths)
                    if index not in used
                ),
                reverse=True,
            )
            match = bool(candidates and candidates[0][0] >= threshold)
            if match:
                used.add(candidates[0][1])
            records.append((prediction["score"], match))
    true = sum(bool(x[1]) for x in records)
    return {
        "true_positive_boxes": true,
        "f1": 2 * true / (len(records) + total) if len(records) + total else None,
        "ground_truth_boxes": total,
        "predicted_boxes": len(records),
        "precision": true / len(records) if records else None,
        "recall": true / total if total else None,
        "ap": average_precision(records, total),
    }


def evaluate(manifest_path, model_manifest, output):
    import cv2

    root = Path(manifest_path).parent
    manifest = json.loads(Path(manifest_path).read_text())
    splits = {}
    seen = set()
    rows = []
    for image in manifest["images"]:
        for key in (
            "id",
            "path",
            "sha256",
            "source",
            "license",
            "split",
            "group",
            "boxes",
        ):
            if key not in image:
                raise ValueError(f"Missing {key}")
        if image["sha256"] in seen:
            raise ValueError("Duplicate image content")
        seen.add(image["sha256"])
        if image["group"] in splits and splits[image["group"]] != image["split"]:
            raise ValueError("Subject/source group crosses splits")
        splits[image["group"]] = image["split"]
        if image["split"] == "test":
            rows.append(image)
    if not rows:
        raise ValueError("No held-out images supplied")
    model_spec = json.loads(Path(model_manifest).read_text())
    detector_class = OnnxPpeDetector
    if model_spec.get("architecture") == "gear_guard_net":
        from .gear_guard import GearGuardDetector

        detector_class = GearGuardDetector
    detector = detector_class(
        model_manifest, threshold=manifest.get("prediction_threshold", 0.05)
    )
    samples = []
    started = perf_counter()
    for row in rows:
        path = root / row["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Image checksum mismatch")
        frame = cv2.imread(str(path))
        if frame is None:
            raise ValueError("Unreadable test image")
        inference_started = perf_counter()
        predictions = [x.__dict__ for x in detector.detect(frame)]
        inference_seconds = perf_counter() - inference_started
        samples.append(
            {
                "id": row["id"],
                "ground_truth": row["boxes"],
                "predictions": predictions,
                "inference_decode_seconds": inference_seconds,
            }
        )
    metrics = {}
    classes = manifest.get("evaluation_classes", CLASSES)
    supported = set(detector.classes.values())
    for label in classes:
        if label not in supported:
            metrics[label] = {"status": "unsupported", "iou_50": None, "ap_50_95": None}
            continue
        thresholds = [0.5 + index * 0.05 for index in range(10)]
        values = [score_class(samples, label, x) for x in thresholds]
        metrics[label] = {
            "status": "evaluated",
            "iou_50": values[0],
            "ap_50_95": sum(x["ap"] for x in values) / 10
            if values[0]["ap"] is not None
            else None,
        }
    available = [x["ap_50_95"] for x in metrics.values() if x["ap_50_95"] is not None]
    result = {
        "status": "evaluated_on_supplied_manifest",
        "model": detector.manifest,
        "manifest_sha256": hashlib.sha256(Path(manifest_path).read_bytes()).hexdigest(),
        "images": len(rows),
        "supported_classes": sorted(set(detector.classes.values())),
        "prediction_threshold": detector.threshold,
        "metrics": metrics,
        "map_50_95": sum(available) / len(available) if available else None,
        "processing_seconds": perf_counter() - started,
        "samples": samples,
        "association_accuracy": None,
        "compliance_accuracy": None,
        "limitations": [
            "AP uses 101-point interpolation and greedy per-image class matching; no COCO crowd/ignore annotations",
            "mAP excludes classes without ground-truth boxes; inspect support counts",
            "Appearance labels (ordinary eyewear/footwear, medical mask) do not establish protective rating",
            "Association/compliance accuracy require additional per-person relation and assessability labels; not inferred from object AP",
        ],
    }
    Path(output).write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True)
    p.add_argument("--model-manifest", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    result = evaluate(a.manifest, a.model_manifest, a.output)
    print(json.dumps(result["metrics"], indent=2))


if __name__ == "__main__":
    main()

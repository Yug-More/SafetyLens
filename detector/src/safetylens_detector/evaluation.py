"""Reproducible video-level held-out evaluation; no synthetic sample generation.

Manifest rows require explicit provenance/license/split/group labels and hashes.
Video-level presence metrics are separate from onset-matched event metrics.
"""

from __future__ import annotations
import argparse
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter
from .video import analyze_video
from .models import DetectorConfig


def ratio(a, b):
    return a / b if b else None


def wilson(success, total):
    if not total:
        return None
    z = 1.959963984540054
    p = success / total
    den = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / den
    half = z * ((p * (1 - p) / total + z * z / (4 * total * total)) ** 0.5) / den
    return [max(0, centre - half), min(1, centre + half)]


def evaluate_manifest(
    manifest_path, model_path, output_path, *, sample_fps=12, profile="legacy"
):
    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text())
    samples = manifest["samples"]
    seen = set()
    groups = {}
    hashes = set()
    for row in samples:
        for field in [
            "id",
            "path",
            "sha256",
            "label",
            "split",
            "group",
            "source",
            "license",
        ]:
            if field not in row or row[field] is None:
                raise ValueError(f"Missing sample {field}")
        if row["id"] in seen or row["sha256"] in hashes:
            raise ValueError("Duplicate sample or content leakage")
        seen.add(row["id"])
        hashes.add(row["sha256"])
        if row["label"] not in {"fall", "normal"}:
            raise ValueError("Unsupported label")
        group = groups.setdefault(row["group"], row["split"])
        if group != row["split"]:
            raise ValueError("Subject/session group crosses splits")
        path = (manifest_path.parent / row["path"]).resolve()
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError("Sample hash mismatch")
    results = []
    tp = fp = tn = fn = 0
    negative_hours = 0
    false_events = 0
    started = perf_counter()
    for row in samples:
        if row["split"] != "test":
            continue
        cfg = DetectorConfig(enable_overhead_displacement=profile == "legacy")
        result = analyze_video(
            manifest_path.parent / row["path"],
            model_path,
            sample_fps=sample_fps,
            config=cfg,
            pose_region=row.get("pose_region"),
            maximum_pose_people=4 if profile == "tracked" else 1,
        )
        events = list(result.events)
        if profile in {"conservative", "tracked"}:
            events = [e for e in events if "rapid_drop" in e.trigger_signals]
        positive = row["label"] == "fall"
        predicted = bool(events)
        tp += positive and predicted
        fn += positive and not predicted
        fp += not positive and predicted
        tn += not positive and not predicted
        if not positive:
            negative_hours += result.duration_seconds / 3600
            false_events += len(events)
        onset = row.get("onset_seconds")
        latency = None
        if onset is not None:
            after = [
                e.occurred_at_seconds - onset
                for e in events
                if e.occurred_at_seconds >= onset
            ]
            latency = min(after) if after else None
        results.append(
            {
                "sample": row,
                "result": result.to_dict(),
                "fall_events_counted": len(events),
                "onset_latency_seconds": latency,
            }
        )
    if not results:
        raise ValueError("No held-out test samples")
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    output = {
        "schema_version": "1.0",
        "evaluation_level": "video-level event presence; not per-frame accuracy",
        "profile": profile,
        "model_sha256": hashlib.sha256(Path(model_path).read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "sample_fps": sample_fps,
        "parameters": DetectorConfig(
            enable_overhead_displacement=profile == "legacy"
        ).__dict__,
        "metrics": {
            "samples": len(results),
            "true_positive": tp,
            "false_positive": fp,
            "true_negative": tn,
            "false_negative": fn,
            "precision": precision,
            "recall": recall,
            "f1": ratio(2 * tp, 2 * tp + fp + fn),
            "false_positive_rate": ratio(fp, fp + tn),
            "false_negative_rate": ratio(fn, fn + tp),
            "recall_95pct_wilson": wilson(tp, tp + fn),
            "precision_95pct_wilson": wilson(tp, tp + fp),
            "false_alarms_per_negative_camera_hour": ratio(
                false_events, negative_hours
            ),
            "negative_camera_hours": negative_hours,
            "processing_seconds": perf_counter() - started,
            "processing_fps": ratio(
                sum(x["result"]["analyzed_frames"] for x in results),
                sum(x["result"]["processing_seconds"] for x in results),
            ),
            "event_detection_latency": "Only available for samples with independently annotated onset; pre-onset alerts not matched.",
            "cpu_utilization": None,
            "gpu_utilization": None,
            "peak_memory_bytes": None,
        },
        "samples": results,
        "limitations": [
            "No threshold tuning on this test set",
            "No industrial safety certification",
            "Video-level metrics can credit an unrelated alert in a positive video; inspect events and supply onset annotations for event-level evaluation",
            "Subject metadata must be verified by dataset owner; unknown subjects cannot establish subject-disjoint generalization",
        ],
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    return output


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--model", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--sample-fps", default=12, type=float)
    p.add_argument("--profile", choices=["legacy", "conservative", "tracked"], default="legacy")
    a = p.parse_args()
    out = evaluate_manifest(
        a.manifest, a.model, a.output, sample_fps=a.sample_fps, profile=a.profile
    )
    print(json.dumps(out["metrics"], indent=2))


if __name__ == "__main__":
    main()

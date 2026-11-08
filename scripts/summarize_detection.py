"""Reproducible per-camera video-presence summaries; never pool paired views."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "detector/src"))
from safetylens_detector.evaluation import wilson

p = argparse.ArgumentParser()
p.add_argument("--results", required=True, type=Path)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
data = json.loads(a.results.read_text())
groups = {}
for row in data["samples"]:
    groups.setdefault(row["sample"].get("camera", "unspecified"), []).append(row)
summary = {}
for camera, rows in groups.items():
    tp = fn = fp = tn = 0
    negative_seconds = 0
    all_alarms = 0
    for row in rows:
        actual = row["sample"]["label"] == "fall"
        predicted = bool(row["fall_events_counted"])
        tp += actual and predicted
        fn += actual and not predicted
        fp += not actual and predicted
        tn += not actual and not predicted
        if not actual:
            negative_seconds += row["result"]["duration_seconds"]
            all_alarms += len(row["result"]["events"])
    precision = tp / (tp + fp) if negative_seconds and tp + fp else None
    summary[camera] = {
        "clips": len(rows),
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "precision": precision,
        "recall": tp / (tp + fn) if tp + fn else None,
        "f1": 2 * tp / (2 * tp + fp + fn)
        if negative_seconds and 2 * tp + fp + fn
        else None,
        "recall_95pct_wilson": wilson(tp, tp + fn),
        "precision_95pct_wilson": wilson(tp, tp + fp) if negative_seconds else None,
        "negative_seconds": negative_seconds,
        "fall_alarms_per_negative_camera_hour": fp * 3600 / negative_seconds
        if negative_seconds
        else None,
        "all_candidate_alarms_on_negative_clips": all_alarms,
    }
a.output.write_text(
    json.dumps(
        {
            "source_sha256": hashlib.sha256(a.results.read_bytes()).hexdigest(),
            "cameras": summary,
            "limitations": [
                "Video-presence, not frame accuracy",
                "Nominal binomial intervals ignore unknown subject/session clustering",
                "No precision or F1 estimated for positive-only camera subsets",
            ],
        },
        indent=2,
    )
)

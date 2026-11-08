"""Post-hoc event matching using independent publisher frame labels, not training.

Only camera0 labels apply. Count misses and unmatched alerts alongside detected-
only video-time delays. This does not measure live end-to-end latency.
"""

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean, median

parser = argparse.ArgumentParser()
parser.add_argument("--results", required=True, type=Path)
parser.add_argument("--labels", required=True, type=Path)
parser.add_argument("--output", required=True, type=Path)
args = parser.parse_args()
labels = {}
for row in csv.reader(args.labels.open()):
    labels.setdefault(row[0], []).append((int(row[1]), int(row[2])))
results = json.loads(args.results.read_text())
rows = []
tp = fn = fp = tn = 0
delays = []
for row in results["samples"]:
    sample = row["sample"]
    if sample.get("camera") != "camera0":
        continue
    events = [
        e for e in row["result"]["events"] if "rapid_drop" in e["trigger_signals"]
    ]
    if sample["label"] == "normal":
        fp += len(events)
        tn += not events
        rows.append(
            {
                "sample": sample["id"],
                "negative_category": True,
                "unmatched_alerts": len(events),
            }
        )
        continue
    sequence = sample["id"].rsplit("-cam", 1)[0]
    annotation = labels[sequence]
    if (
        min(x[0] for x in annotation) != 1
        or max(x[0] for x in annotation) != row["result"]["decoded_frames"]
    ):
        raise ValueError("Unverified label/video frame-count alignment")
    falling = [index for index, label in annotation if label == 0]
    if not falling:
        raise ValueError("No independent transition annotation; do not invent onset")
    onset = (min(falling) - 1) / row["result"]["source_fps"]
    end = min(onset + 5, row["result"]["duration_seconds"])
    matched = [e for e in events if onset <= e["occurred_at_seconds"] <= end]
    detected = bool(matched)
    tp += detected
    fn += not detected
    fp += len(events) - int(detected)
    delay = min(e["occurred_at_seconds"] - onset for e in matched) if detected else None
    if delay is not None:
        delays.append(delay)
    rows.append(
        {
            "sample": sample["id"],
            "publisher_first_transition_frame": min(falling),
            "onset_video_seconds": onset,
            "matching_window_end_seconds": end,
            "matched": detected,
            "delay_video_seconds": delay,
            "unmatched_alerts": len(events) - int(detected),
        }
    )
output = {
    "publisher_label_url": "https://fenix.ur.edu.pl/~mkepski/ds/data/urfall-cam0-falls.csv",
    "publisher_labels_sha256": hashlib.sha256(args.labels.read_bytes()).hexdigest(),
    "prediction_file_sha256": hashlib.sha256(args.results.read_bytes()).hexdigest(),
    "protocol": "Frozen post-hoc matching: one first-transition label0 per fall-category camera0 video; first alert within5s or clip end. Unmatched alerts retained. No classifier retuning.",
    "matched_true_events": tp,
    "missed_true_events": fn,
    "unmatched_false_alerts": fp,
    "negative_videos_without_alert": tn,
    "detected_only_delay_seconds": {
        "count": len(delays),
        "mean": mean(delays) if delays else None,
        "median": median(delays) if delays else None,
        "maximum": max(delays) if delays else None,
        "values": delays,
    },
    "samples": rows,
    "limitations": [
        "Publisher posture labels, not independent workplace accident verification",
        "One-based frame alignment checked by counts for all clips, raw RGB pixel correspondence separately checked for fall17",
        "Video-relative delay, not live capture-to-operator or medical response time",
        "Camera1 excluded because independent sampling and no applicable frame labels",
        "True negative counts use negative videos; this is not a per-frame confusion matrix",
    ],
}
args.output.write_text(json.dumps(output, indent=2))
print(
    json.dumps(
        {
            k: v
            for k, v in output.items()
            if k
            in [
                "matched_true_events",
                "missed_true_events",
                "unmatched_false_alerts",
                "detected_only_delay_seconds",
            ]
        },
        indent=2,
    )
)

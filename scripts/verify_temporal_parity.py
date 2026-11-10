"""Replay published test media to check runtime/evaluator parity, not new accuracy.

No training/selection or threshold changes. Reuses the frozen checkpoint and
source/cache hashes; verifies sampled pose features and event times end-to-end.
"""

import argparse
import hashlib
import json
from pathlib import Path
from time import perf_counter
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "detector/src"))
from safetylens_detector.temporal import TemporalModel, DECISION_VERSION
from safetylens_detector.video import analyze_video
from temporal_experiment import events, summarize

p = argparse.ArgumentParser()
p.add_argument("--cache", required=True, type=Path)
p.add_argument("--manifest", required=True, type=Path)
p.add_argument("--checkpoint", required=True, type=Path)
p.add_argument("--checkpoint-sha256", required=True)
p.add_argument("--pose-model", required=True, type=Path)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
cache = json.loads(a.cache.read_text())
manifest = json.loads(a.manifest.read_text())
lookup = {r["id"]: r for r in manifest["samples"]}
model = TemporalModel.load(a.checkpoint, expected_sha256=a.checkpoint_sha256)
if hashlib.sha256(a.pose_model.read_bytes()).hexdigest() != cache["model_sha256"]:
    raise ValueError("Pose model mismatch")
rows = []
start = perf_counter()
for clip in cache["clips"]:
    row = lookup[clip["sample"]["id"]]
    path = a.manifest.parent / row["path"]
    if hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError("Media changed")
    actual = analyze_video(
        path, a.pose_model, temporal_model=model, pose_region=row.get("pose_region")
    )
    expected, _ = events(clip, model)
    runtime = [e.occurred_at_seconds for e in actual.events]
    if len(expected) != len(runtime) or any(
        abs(x - y) > 1e-6 for x, y in zip(expected, runtime)
    ):
        raise AssertionError(
            f"Runtime/evaluation divergence for {row['id']}: {runtime} != {expected}"
        )
    rows.append(
        {
            "id": row["id"],
            "runtime_event_times": runtime,
            "cached_event_times": expected,
            "sampled_frames": actual.analyzed_frames,
            "analysis_seconds": actual.processing_seconds,
        }
    )
    print("parity", row["id"], runtime, flush=True)
result = {
    "decision_version": DECISION_VERSION,
    "scope": "Published test replay and runtime/evaluator consistency, NOT a new held-out experiment",
    "checkpoint_sha256": a.checkpoint_sha256,
    "unchanged_model_and_operating_point": True,
    "samples_verified": len(rows),
    "wall_seconds": perf_counter() - start,
    "metrics": summarize(cache["clips"], model),
    "runtime_samples": rows,
}
a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")

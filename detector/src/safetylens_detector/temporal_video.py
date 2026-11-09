"""Explicit opt-in real-video inference with a hash-pinned research checkpoint."""

import argparse
import hashlib
import json
from pathlib import Path
from .temporal import TemporalModel
from .video import analyze_video


def main():
    p = argparse.ArgumentParser()
    p.add_argument("video", type=Path)
    p.add_argument("--pose-model", required=True, type=Path)
    p.add_argument("--checkpoint", required=True, type=Path)
    p.add_argument("--checkpoint-sha256", required=True)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--maximum-people", type=int, choices=range(1, 5), default=1)
    p.add_argument(
        "--rgb-right-half",
        action="store_true",
        help="Explicit URFall composite calibration only",
    )
    a = p.parse_args()
    model = TemporalModel.load(a.checkpoint, expected_sha256=a.checkpoint_sha256)
    if hashlib.sha256(a.pose_model.read_bytes()).hexdigest() != model.checkpoint.get(
        "pose_model_sha256"
    ):
        p.error("Pose model hash differs from training")
    result = analyze_video(
        a.video,
        a.pose_model,
        temporal_model=model,
        maximum_pose_people=a.maximum_people,
        pose_region=(0.5, 0, 1, 1) if a.rgb_right_half else None,
    ).to_dict()
    result.update(checkpoint_sha256=a.checkpoint_sha256, research_only=True)
    a.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("Actual events:", len(result["events"]))


if __name__ == "__main__":
    main()

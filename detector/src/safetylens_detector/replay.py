from __future__ import annotations

import argparse
import json
from pathlib import Path

from .engine import DetectorEngine
from .models import Landmark, PoseObservation


def _observation(payload: dict[str, object]) -> PoseObservation:
    raw_landmarks = payload.get("landmarks")
    if not isinstance(raw_landmarks, dict):
        raise ValueError("landmarks must be an object")
    landmarks: dict[str, Landmark] = {}
    for name, raw in raw_landmarks.items():
        if not isinstance(name, str) or not isinstance(raw, list) or len(raw) not in {2, 3}:
            raise ValueError("each landmark must be [x, y] or [x, y, visibility]")
        landmarks[name] = Landmark(float(raw[0]), float(raw[1]), float(raw[2]) if len(raw) == 3 else 1.0)
    return PoseObservation(
        timestamp_seconds=float(payload["timestamp_seconds"]),
        track_id=str(payload["track_id"]),
        source_id=str(payload.get("source_id", "replay")),
        source_timestamp_seconds=(
            float(payload["source_timestamp_seconds"])
            if payload.get("source_timestamp_seconds") is not None
            else None
        ),
        landmarks=landmarks,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay pose JSONL through the SafetyLens detector")
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    engine = DetectorEngine()

    with args.path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                result = engine.process(_observation(json.loads(line)))
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                raise SystemExit(f"line {line_number}: {error}") from error
            print(
                json.dumps(
                    {
                        "track_id": result.track_id,
                        "previous_state": result.previous_state.value,
                        "state": result.state.value,
                        "reasons": list(result.reasons),
                        "event": result.event.to_dict() if result.event else None,
                    },
                    sort_keys=True,
                )
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


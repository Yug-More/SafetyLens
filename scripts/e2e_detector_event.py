"""Integration fixture: synthetic media/event, never detection-evaluation data."""

import json
import os
from pathlib import Path
import sys
import tempfile
from uuid import uuid4

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "detector/src"))
import cv2
import numpy as np
from safetylens_detector.delivery import EventOutbox

folder = Path(tempfile.mkdtemp(prefix="safetylens-event-fixture-"))
clip = folder / "integration-fixture.mp4"
writer = cv2.VideoWriter(str(clip), cv2.VideoWriter_fourcc(*"mp4v"), 8, (320, 240))
if not writer.isOpened():
    raise RuntimeError("Fixture encoder unavailable")
for i in range(40):
    frame = np.zeros((240, 320, 3), np.uint8)
    cv2.putText(
        frame,
        "INTEGRATION TEST ONLY",
        (10, 120),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
    )
    writer.write(frame)
writer.release()
event = {
    "schema_version": "1.0",
    "event_id": str(uuid4()),
    "event_type": "possible_person_down",
    "source_id": "integration-test-fixture",
    "trigger_signals": ["integration_fixture"],
    "limitations": ["Synthetic integration fixture, not measured CV output"],
}
outbox = EventOutbox(folder / "outbox")
outbox.enqueue(
    event,
    clip,
    camera_id="cam-03",
    location="Browser integration test",
    clip_event_offset_seconds=2,
)
if not outbox.flush_once("http://127.0.0.1:8107", os.environ["DETECTOR_API_TOKEN"]):
    raise RuntimeError("Event was not acknowledged")
print(json.dumps({"event_id": event["event_id"]}))

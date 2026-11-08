"""Actual-model same-UUID concurrent large upload regression, isolated stack only.

Padding is an MP4 free box to exercise spooled-file I/O, never a CV test sample.
"""

import argparse, asyncio, hashlib, json, struct, time
from pathlib import Path
import httpx

p = argparse.ArgumentParser()
p.add_argument("--env-file", required=True, type=Path)
p.add_argument("--clip", required=True, type=Path)
p.add_argument("--model", required=True, type=Path)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
a.output.mkdir(parents=True, exist_ok=True)
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "detector/src"))
from safetylens_detector.video import analyze_video
from safetylens_detector.models import DetectorConfig

analysis = analyze_video(
    a.clip,
    a.model,
    pose_region=(0.5, 0, 1, 1),
    config=DetectorConfig(enable_overhead_displacement=False),
    source_id="concurrent-real-model",
)
event = next(e.to_dict() for e in analysis.events if "rapid_drop" in e.trigger_signals)
clip = a.clip.read_bytes() + struct.pack(">I4s", 3_000_008, b"free") + bytes(3_000_000)
event.update(
    camera_id="cam-03",
    clip_event_offset_seconds=event["occurred_at_seconds"],
    evidence={"clip_sha256": hashlib.sha256(clip).hexdigest()},
)
values = dict(
    x.split("=", 1)
    for x in a.env_file.read_text().splitlines()
    if "=" in x and not x.startswith("#")
)


async def run():
    async with httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=30,
        headers={"Authorization": "Bearer " + values["DETECTOR_API_TOKEN"]},
    ) as client:

        async def submit():
            return await client.post(
                "/api/detector/events",
                data={"event_json": json.dumps(event), "auto_analyze": "false"},
                files={"clip": ("real-large-fixture.mp4", clip, "video/mp4")},
            )

        start = time.perf_counter()
        responses = await asyncio.gather(submit(), submit())
        elapsed = time.perf_counter() - start
        assert [r.status_code for r in responses] == [202, 202], [
            r.status_code for r in responses
        ]
        codes = [r.json()["data"]["asset_code"] for r in responses]
        assert codes[0] == codes[1]
        result = {
            "real_model_event_id": event["event_id"],
            "source_model_time_seconds": event["occurred_at_seconds"],
            "fixture_bytes": len(clip),
            "sha256": event["evidence"]["clip_sha256"],
            "concurrent_http_statuses": [r.status_code for r in responses],
            "single_asset_mapping": codes[0],
            "pair_wall_seconds": elapsed,
            "scope": "Actual recorded footage/model event with free-box padding for transport only; not an evaluation video or production latency claim",
        }
        (a.output / "verification.json").write_text(json.dumps(result, indent=2))
        print(json.dumps(result, indent=2))


asyncio.run(run())

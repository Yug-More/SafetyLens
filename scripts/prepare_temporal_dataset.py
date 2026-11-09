"""Acquire fixed URFall recording splits outside Git; never redistribute raw media.

Upstream CC BY-NC-SA 4.0, academic research only. Subject/session IDs unknown.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--directory", required=True, type=Path)
a = p.parse_args()
a.directory.mkdir(parents=True, exist_ok=True)
reference = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "docs/evaluation/research/urfall-manifest.json"
    ).read_text()
)
expected = {r["id"]: r["sha256"] for r in reference["samples"]}
rows = []
for kind, count in [("fall", 30), ("adl", 40)]:
    for i in range(1, count + 1):
        split = "train" if i <= 16 else "validation" if i <= 26 else "test"
        name = f"{kind}-{i:02d}-cam0"
        destination = a.directory / (name + ".mp4")
        url = f"https://fenix.ur.edu.pl/~mkepski/ds/data/{name}.mp4"
        if not destination.exists():
            # Reuse hash-checked public recordings from prior local experiments.
            choices = [
                Path("/tmp/safetylens-hardening/holdout") / destination.name,
                Path("/tmp/safetylens-hardening/development") / f"{kind}-{i:02d}.mp4",
            ]
            existing = next((x for x in choices if x.exists()), None)
            if existing:
                destination.write_bytes(existing.read_bytes())
            else:
                subprocess.run(
                    [
                        "curl",
                        "--fail",
                        "--location",
                        "--retry",
                        "2",
                        url,
                        "-o",
                        str(destination),
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        if hashlib.sha256(destination.read_bytes()).hexdigest() != expected[name]:
            raise ValueError(f"Frozen recording content changed: {name}")
        rows.append(
            dict(
                id=name,
                path=destination.name,
                sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                label="fall" if kind == "fall" else "normal",
                split=split,
                group=f"urfall-{kind}-{i:02d}",
                source=url,
                license="CC-BY-NC-SA-4.0",
                pose_region=[0.5, 0, 1, 1],
                subject="unknown",
                session="unknown",
            )
        )
labels = a.directory / "urfall-cam0-falls.csv"
if not labels.exists():
    subprocess.run(
        [
            "curl",
            "--fail",
            "--location",
            "https://fenix.ur.edu.pl/~mkepski/ds/data/urfall-cam0-falls.csv",
            "-o",
            str(labels),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
if hashlib.sha256(labels.read_bytes()).hexdigest() != reference["label_sha256"]:
    raise ValueError("Publisher label content changed")
manifest = {
    "dataset": "URFall camera0; fixed recording split; NOT subject-disjoint",
    "label_file": labels.name,
    "label_sha256": hashlib.sha256(labels.read_bytes()).hexdigest(),
    "samples": rows,
}
(a.directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("Prepared", len(rows), "clips; models/data remain outside Git")

"""Reacquire frozen validation media by exact source URL and SHA-256.

Research-only dataset use: UR Fall and upstream SH17 are CC-BY-NC-SA-4.0.
The SH17 mirror declares CC-BY-4.0; that does not override upstream obligations.
No weights, images or video are redistributed in the repository.
"""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--kind", choices=["urfall", "ppe", "hardening"], required=True)
p.add_argument("--directory", type=Path, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
source = (
    root / "docs/evaluation/hardening/holdout-manifest.json"
    if a.kind == "hardening"
    else root
    / "docs/evaluation/final"
    / ("urfall20-manifest.json" if a.kind == "urfall" else "ppe24-manifest.json")
)
manifest = json.loads(source.read_text())
a.directory.mkdir(parents=True, exist_ok=True)
rows = manifest["images" if a.kind == "ppe" else "samples"]
for row in rows:
    relative = Path(row["path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Manifest paths must remain inside the acquisition directory")
    destination = a.directory / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        subprocess.run(
            [
                "curl",
                "--fail",
                "--location",
                "--retry",
                "2",
                row["source"],
                "--output",
                str(destination),
            ],
            check=True,
        )
    if hashlib.sha256(destination.read_bytes()).hexdigest() != row["sha256"]:
        raise ValueError(f"Content differs from frozen validation sample: {row['id']}")
shutil.copyfile(source, a.directory / "manifest.json")
print(
    f"Verified {len(rows)} source hashes. Research use only; no subject-disjoint or model-training-overlap guarantee."
)

"""Download a prespecified noncommercial academic subset, with hashes/provenance.

No redistribution in Git. Read the upstream license before use. This command never
creates labels or onsets beyond the publisher's video-category labels.
"""

import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("--directory", required=True, type=Path)
a = p.parse_args()
a.directory.mkdir(parents=True, exist_ok=True)
samples = []
for kind in ("fall", "adl"):
    for index in range(1, 7):
        name = f"{kind}-{index:02d}"
        url = f"https://fenix.ur.edu.pl/~mkepski/ds/data/{name}-cam0.mp4"
        destination = a.directory / f"{name}.mp4"
        if not destination.exists():
            urllib.request.urlretrieve(url, destination)
        samples.append(
            {
                "id": name,
                "path": destination.name,
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "label": "fall" if kind == "fall" else "normal",
                "split": "test",
                "group": "urfall-subject-unknown",
                "source": url,
                "license": "CC-BY-NC-SA-4.0",
                "onset_seconds": None,
            }
        )
(a.directory / "manifest.json").write_text(
    json.dumps(
        {
            "dataset": "UR Fall camera0; first six falls and first six ADLs; no threshold tuning",
            "samples": samples,
        },
        indent=2,
    )
    + "\n"
)
print(
    "Saved 12 public academic video samples and manifest; subject identity unknown, onset unannotated."
)

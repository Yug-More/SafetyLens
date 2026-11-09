"""Match source annotations to mirror geometry before assigning semantic names.

Download research annotations only; never use model predictions to choose mapping.
"""

import json, subprocess, urllib.parse, hashlib, collections
from pathlib import Path
import argparse

p = argparse.ArgumentParser(
    description="Verify numeric mirror semantics against independent original labels, without predictions"
)
p.add_argument("--annotations", required=True, type=Path)
p.add_argument("--manifest", type=Path)
p.add_argument("--count", type=int, default=100)
p.add_argument("--label-directory", required=True, type=Path)
p.add_argument("--output", required=True, type=Path)
a = p.parse_args()
d = json.loads(a.annotations.read_text())
chosen = (
    json.loads(a.manifest.read_text())
    if a.manifest
    else {"images": sorted(d["images"], key=lambda x: x["file_name"])[: a.count]}
)
ids = {int(x["id"]) for x in chosen["images"]}
folder = a.label_directory
folder.mkdir(parents=True, exist_ok=True)
anns = collections.defaultdict(list)
for x in d["annotations"]:
    anns[x["image_id"]].append(x)
counts = collections.Counter()
unmatched = 0
provenance = []
for image in d["images"]:
    if image["id"] not in ids:
        continue
    name = Path(image["extra"]["name"]).stem + ".txt"
    p = folder / name
    url = (
        "https://www.kaggle.com/api/v1/datasets/download/mugheesahmad/sh17-dataset-for-ppe-detection/"
        + urllib.parse.quote("labels/" + name, safe="")
    )
    if not p.exists():
        subprocess.run(
            [
                "curl",
                "--fail",
                "--silent",
                "--show-error",
                "--location",
                "--max-filesize",
                "1000000",
                url,
                "-o",
                str(p),
            ],
            check=True,
        )
    original = []
    for line in p.read_text().splitlines():
        label, x, y, w, h = map(float, line.split())
        original.append(
            (
                int(label),
                (x - w / 2) * image["width"],
                (y - h / 2) * image["height"],
                w * image["width"],
                h * image["height"],
            )
        )
    used = set()
    linked = 0
    for annotation in anns[image["id"]]:
        distances = sorted(
            (max(abs(x - y) for x, y in zip(annotation["bbox"], o[1:])), j, o[0])
            for j, o in enumerate(original)
            if j not in used
        )
        if distances and distances[0][0] <= 2:
            delta, j, label = distances[0]
            used.add(j)
            counts[(annotation["category_id"], label)] += 1
            linked += 1
        else:
            unmatched += 1
    provenance.append(
        {
            "image_id": image["id"],
            "original_label_source": url,
            "original_label_sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            "mirror_boxes": len(anns[image["id"]]),
            "matched_geometry": linked,
        }
    )
    print(image["id"], linked, "/", len(anns[image["id"]]), flush=True)
mapping = {}
for (mirror, original), n in counts.items():
    if mirror in mapping and mapping[mirror] != original:
        raise ValueError("Inconsistent semantic mapping")
    mapping[mirror] = original
if unmatched:
    raise ValueError("Unmatched source/mirror boxes; semantic verification incomplete")
out = {
    "method": "Independent original publisher YOLO annotations matched to mirror COCO boxes, maximum per-coordinate error <=2 pixels; predictions not consulted",
    "mirror_annotations_sha256": hashlib.sha256(a.annotations.read_bytes()).hexdigest(),
    "mirror_category_to_publisher_class": mapping,
    "pair_counts": [
        {"mirror_category": m, "publisher_class": o, "boxes": n}
        for (m, o), n in sorted(counts.items())
    ],
    "unmatched_boxes": unmatched,
    "files": provenance,
}
a.output.write_text(json.dumps(out, indent=2) + "\n")
print(mapping)

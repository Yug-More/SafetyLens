"""Pinned, labeled multi-class SH17 diagnostic; overlap with pretraining UNKNOWN.

Source CC BY-NC-SA overrides mirror CC BY declaration. Never deploy or commit
images/weights. Numeric mirror IDs map via the official sh17.yaml class order.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument("--annotations", required=True, type=Path)
p.add_argument("--directory", required=True, type=Path)
p.add_argument("--count", type=int, default=100)
p.add_argument("--verified-mapping", required=True, type=Path)
a = p.parse_args()
a.directory.mkdir(parents=True, exist_ok=True)
data = json.loads(a.annotations.read_text())
by_id = {x["id"]: x for x in data["categories"]}
names = {
    0: "person",
    2: "earmuffs",
    4: "face_shield",
    5: "medical_mask",
    8: "ordinary_eyewear",
    9: "gloves",
    10: "hard_hat",
    14: "ordinary_footwear",
    16: "high_visibility_vest",
}
verification = json.loads(a.verified_mapping.read_text())
if (
    verification["mirror_annotations_sha256"]
    != hashlib.sha256(a.annotations.read_bytes()).hexdigest()
):
    raise ValueError("Mapping provenance mismatch")
category_map = {
    int(k): v for k, v in verification["mirror_category_to_publisher_class"].items()
}
annotations = {}
for obj in data["annotations"]:
    annotations.setdefault(obj["image_id"], []).append(obj)
reference = json.loads(
    (
        Path(__file__).resolve().parents[1]
        / "docs/evaluation/research/ppe100-manifest.json"
    ).read_text()
)
expected = {r["id"]: r["sha256"] for r in reference["images"]}
rows = []
for image in sorted(data["images"], key=lambda x: x["file_name"])[: a.count]:
    name = image["file_name"]
    target = a.directory / name
    if Path(name).name != name:
        raise ValueError("Unsafe filename")
    source = (
        "https://huggingface.co/datasets/fathansanum/SH-17-Dataset/resolve/c979be777eaa1c6b5338410788b65926a033e3a0/SH17-dataset-1/test/"
        + name
    )
    if not target.exists():
        old = Path("/tmp/safetylens-hardening/ppe24") / name
        if old.exists():
            target.write_bytes(old.read_bytes())
        else:
            subprocess.run(
                [
                    "curl",
                    "--fail",
                    "--location",
                    "--retry",
                    "2",
                    source,
                    "-o",
                    str(target),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    if (
        str(image["id"]) not in expected
        or hashlib.sha256(target.read_bytes()).hexdigest() != expected[str(image["id"])]
    ):
        raise ValueError("Image outside frozen diagnostic or content changed")
    boxes = []
    for obj in annotations.get(image["id"], []):
        category = by_id[obj["category_id"]]["name"]
        if not category.isdigit():
            continue
        if obj["category_id"] not in category_map:
            raise ValueError("Unverified numeric semantic category")
        label = names.get(category_map[obj["category_id"]])
        if label is None:
            continue
        if obj.get("iscrowd", 0):
            raise ValueError("Crowd annotations require a different evaluator")
        x, y, w, h = obj["bbox"]
        boxes.append({"label": label, "xyxy": [x, y, x + w, y + h]})
    rows.append(
        {
            "id": str(image["id"]),
            "path": name,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "source": source,
            "license": "CC-BY-NC-SA-4.0 upstream; mirror CC-BY declaration does not override",
            "split": "test",
            "group": name.split("_jpeg.rf.")[0],
            "boxes": boxes,
        }
    )
manifest = {
    "dataset": "SH17 pinned first100 mirror filenames; diagnostic only, pretrained overlap unknown",
    "prediction_threshold": 0.05,
    "evaluation_classes": list(names.values()),
    "annotations_sha256": hashlib.sha256(a.annotations.read_bytes()).hexdigest(),
    "label_mapping_source": "Independent original publisher annotations matched to mirror geometry; see verified-label-mapping.json",
    "mapping_sha256": hashlib.sha256(a.verified_mapping.read_bytes()).hexdigest(),
    "images": rows,
}
(a.directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(
    "Prepared",
    len(rows),
    "labeled images; no wearer or visibility relationships available",
)

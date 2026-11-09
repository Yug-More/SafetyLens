"""Reproducible causal pose learning without pickle, PyTorch or test-set tuning.

extract --splits train validation; train; freeze checkpoint; only then extract
--splits test and evaluate. All model/data/cache artifacts stay outside Git.
"""

import argparse
from dataclasses import asdict
import hashlib
import json
import platform
from pathlib import Path
from time import perf_counter
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "detector/src"))
import numpy as np
from safetylens_detector.temporal import (
    CausalFeatures,
    TemporalModel,
    FEATURE_NAMES,
    FEATURE_VERSION,
)
from safetylens_detector.mediapipe_provider import MediaPipePoseProvider
from safetylens_detector.evaluation import wilson


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_manifest(path):
    data = json.loads(Path(path).read_text())
    seen, hashes, groups = set(), set(), {}
    for r in data["samples"]:
        if (
            r["id"] in seen
            or r["sha256"] in hashes
            or groups.get(r["group"], r["split"]) != r["split"]
        ):
            raise ValueError("Duplicate content or recording split leakage")
        seen.add(r["id"])
        hashes.add(r["sha256"])
        groups[r["group"]] = r["split"]
        if r["split"] not in {"train", "validation", "test"}:
            raise ValueError("Unsupported split")
    return data


def extract(args):
    import cv2

    source = load_manifest(args.manifest)
    root = args.manifest.parent
    if digest(root / source["label_file"]) != source["label_sha256"]:
        raise ValueError("Publisher label hash mismatch")
    labels = {}
    for line in (root / source["label_file"]).read_text().splitlines():
        f = line.split(",")
        labels.setdefault(f[0], {})[int(f[1])] = int(f[2])
    started = perf_counter()
    clips = []
    for r in source["samples"]:
        if r["split"] not in args.splits:
            continue
        path = root / r["path"]
        if digest(path) != r["sha256"]:
            raise ValueError("Video hash mismatch")
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if fps <= 0:
            raise ValueError("Missing FPS")
        annotation = labels.get(r["id"].replace("-cam0", ""), {})
        if r["label"] == "fall" and (
            len(annotation) != total or max(annotation) != total
        ):
            raise ValueError("Publisher annotation/video frame alignment mismatch")
        onset = next(
            ((i - 1) / fps for i, v in sorted(annotation.items()) if v == 0), None
        )
        history = CausalFeatures()
        rows = []
        decoded = 0
        next_sample = 0
        pose_seconds = 0
        try:
            with MediaPipePoseProvider(
                args.pose_model, region=r.get("pose_region")
            ) as pose:
                while True:
                    ok, frame = cap.read()
                    if not ok:
                        break
                    t = decoded / fps
                    decoded += 1
                    if t + 1e-9 < next_sample:
                        continue
                    next_sample += 1 / 12
                    tick = perf_counter()
                    obs = pose.detect(frame, timestamp_seconds=t, source_id=r["id"])
                    pose_seconds += perf_counter() - tick
                    if obs is None:
                        rows.append(
                            {
                                "t": t,
                                "features": None,
                                "metrics": None,
                                "label": int(r["label"] == "fall" and t >= onset),
                            }
                        )
                        continue
                    features, metrics = history.process(obs)
                    rows.append(
                        {
                            "t": t,
                            "features": features.tolist()
                            if features is not None
                            else None,
                            "metrics": asdict(metrics),
                            "label": int(r["label"] == "fall" and t >= onset),
                        }
                    )
        finally:
            cap.release()
        clips.append(
            {
                "sample": r,
                "source_fps": fps,
                "decoded_frames": decoded,
                "duration": total / fps,
                "onset": onset,
                "rows": rows,
                "pose_seconds": pose_seconds,
            }
        )
        print("extracted", r["id"], len(rows), flush=True)
    result = {
        "feature_version": FEATURE_VERSION,
        "manifest_sha256": digest(args.manifest),
        "model_sha256": digest(args.pose_model),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "splits": args.splits,
        "processing_seconds": perf_counter() - started,
        "clips": clips,
    }
    args.output.write_text(json.dumps(result, allow_nan=False) + "\n")


def events(clip, model):
    # Same debounce, coverage and sustained-upright rearm as runtime engine.
    valid = [r for r in clip["rows"] if r["features"] is not None]
    scores = (
        iter(model.score(np.array([r["features"] for r in valid])).tolist())
        if valid
        else iter([])
    )
    since = None
    latched = False
    recovery = None
    last = None
    times = []
    scored = []
    for row in clip["rows"]:
        t = row["t"]
        f = row["features"]
        if f is None:
            since = None
            scored.append([t, None])
            continue
        score = next(scores)
        scored.append([t, score])
        if last is not None and t - last > 0.75:
            since = None
        last = t
        if latched:
            m = row["metrics"]
            upright = (
                m["torso_angle_degrees_from_vertical"] < 35
                and (m["bbox_width_height_ratio"] or 10) < 1.2
            )
            recovery = (t if recovery is None else recovery) if upright else None
            if recovery is not None and t - recovery >= 1:
                latched = False
                since = None
        elif score >= model.threshold:
            since = t if since is None else since
            if t - since >= 0.083 and f[-2] >= 0.25:
                times.append(t)
                latched = True
        else:
            since = None
    return times, scored


def summarize(clips, model, *, include_scores=False):
    tp = fp = tn = fn = 0
    false_events = 0
    negative_seconds = 0
    matched = missed = unmatched = 0
    delays = []
    samples = []
    for c in clips:
        times, scores = events(c, model)
        positive = c["sample"]["label"] == "fall"
        pred = bool(times)
        tp += positive and pred
        fn += positive and not pred
        fp += not positive and pred
        tn += not positive and not pred
        onset = c["onset"]
        delay = None
        if positive:
            after = [t for t in times if onset <= t <= min(onset + 5, c["duration"])]
            matched += bool(after)
            missed += not bool(after)
            unmatched += len(times) - int(bool(after))
            if after:
                delay = after[0] - onset
                delays.append(delay)
        else:
            negative_seconds += c["duration"]
            false_events += len(times)
            unmatched += len(times)
        sample = {
            "id": c["sample"]["id"],
            "label": c["sample"]["label"],
            "event_times": times,
            "onset": onset,
            "matched_delay": delay,
            "frames": len(c["rows"]),
            "missing_or_low_quality": sum(r["features"] is None for r in c["rows"]),
        }
        if include_scores:
            sample["scores"] = scores
        samples.append(sample)
    ratio = lambda a, b: a / b if b else None
    return {
        "video_presence": {
            "tp": int(tp),
            "fn": int(fn),
            "fp": int(fp),
            "tn": int(tn),
            "precision": ratio(tp, tp + fp),
            "recall": ratio(tp, tp + fn),
            "f1": ratio(2 * tp, 2 * tp + fp + fn),
            "specificity": ratio(tn, tn + fp),
            "false_positive_rate": ratio(fp, fp + tn),
            "false_negative_rate": ratio(fn, fn + tp),
            "recall_nominal_wilson95": wilson(tp, tp + fn),
            "precision_nominal_wilson95": wilson(tp, tp + fp),
        },
        "onset_matched": {
            "matched": matched,
            "missed": missed,
            "unmatched_alerts": unmatched,
            "mean_detected_delay_seconds": float(np.mean(delays)) if delays else None,
            "delays_seconds": delays,
        },
        "negative_seconds": negative_seconds,
        "false_events": false_events,
        "false_alarms_per_negative_hour": ratio(false_events * 3600, negative_seconds),
        "samples": samples,
    }


def train(args):
    data = json.loads(args.cache.read_text())
    if set(data["splits"]) != {"train", "validation"}:
        raise ValueError("Training input must contain only train/validation")
    train_clips = [c for c in data["clips"] if c["sample"]["split"] == "train"]
    validation = [c for c in data["clips"] if c["sample"]["split"] == "validation"]
    if not train_clips or not validation:
        raise ValueError("Both recording splits required")
    X = []
    y = []
    weights = []
    for c in train_clips:
        rows = [r for r in c["rows"] if r["features"] is not None]
        for r in rows:
            X.append(r["features"])
            y.append(r["label"])
            weights.append(1 / len(rows))
    X = np.array(X)
    y = np.array(y)
    weights = np.array(weights)
    if set(y) != {0, 1}:
        raise ValueError("Two training classes required")
    for label in (0, 1):
        weights[y == label] /= weights[y == label].sum() * 2
    mean = X.mean(axis=0)
    scale = np.maximum(X.std(axis=0), 0.05)
    z = np.clip((X - mean) / scale, -8, 8)
    selection = []
    checkpoints = []
    curves = {}
    for linear in (True, False):
        rng = np.random.default_rng(42)
        h = len(FEATURE_NAMES) if linear else 32
        w1 = (
            np.eye(h)
            if linear
            else rng.normal(0, 1 / np.sqrt(z.shape[1]), (z.shape[1], h))
        )
        b1 = np.zeros(h)
        w2 = np.zeros(h)
        b2 = np.array(0.0)
        params = [w2, b2] if linear else [w1, b1, w2, b2]
        mom = [np.zeros_like(p) for p in params]
        vel = [np.zeros_like(p) for p in params]
        curve = []
        for epoch in range(1, 301):
            hidden = z @ w1 + b1
            if not linear:
                hidden = np.tanh(hidden)
            logits = hidden @ w2 + b2
            pred = 1 / (1 + np.exp(-np.clip(logits, -30, 30)))
            d = (pred - y) * weights
            g2 = hidden.T @ d + 0.001 * w2
            gb2 = np.asarray(d.sum())
            if linear:
                grads = [g2, gb2]
            else:
                dh = (d[:, None] * w2) * (1 - hidden**2)
                grads = [z.T @ dh + 0.001 * w1, dh.sum(axis=0), g2, gb2]
            for i, (param, grad) in enumerate(zip(params, grads)):
                mom[i] = 0.9 * mom[i] + 0.1 * grad
                vel[i] = 0.999 * vel[i] + 0.001 * grad**2
                param -= (
                    0.01
                    * (mom[i] / (1 - 0.9**epoch))
                    / (np.sqrt(vel[i] / (1 - 0.999**epoch)) + 1e-8)
                )
            if epoch % 10 == 0:
                curve.append(
                    {
                        "epoch": epoch,
                        "weighted_train_bce": float(
                            -np.sum(
                                weights
                                * (
                                    y * np.log(pred + 1e-9)
                                    + (1 - y) * np.log(1 - pred + 1e-9)
                                )
                            )
                        ),
                    }
                )
        name = "linear" if linear else "mlp32"
        curves[name] = curve
        checkpoint = {
            "feature_version": FEATURE_VERSION,
            "feature_names": list(FEATURE_NAMES),
            "mean": mean.tolist(),
            "scale": scale.tolist(),
            "w1": w1.tolist(),
            "b1": b1.tolist(),
            "w2": w2.tolist(),
            "b2": float(b2),
            "linear": linear,
            "seed": 42,
            "epochs": 300,
            "learning_rate": 0.01,
            "l2": 0.001,
            "cache_sha256": digest(args.cache),
            "pose_model_sha256": data["model_sha256"],
            "research_only": True,
            "license": "Derived from URFall CC-BY-NC-SA-4.0; noncommercial research only",
            "training_recordings": [c["sample"]["id"] for c in train_clips],
        }
        for threshold in (0.3, 0.5, 0.7, 0.9):
            candidate = {**checkpoint, "threshold": threshold}
            metrics = summarize(validation, TemporalModel(candidate))
            v = metrics["video_presence"]
            selection.append(
                {"architecture": name, "threshold": threshold, "metrics": metrics}
            )
            checkpoints.append(candidate)

    def rank(i):
        v = selection[i]["metrics"]["video_presence"]
        return (v["f1"] or 0, v["precision"] or 0, int(checkpoints[i]["linear"]))

    index = max(range(len(selection)), key=rank)
    chosen = checkpoints[index]
    args.output.write_text(json.dumps(chosen, indent=2, allow_nan=False) + "\n")
    args.report.write_text(
        json.dumps(
            {
                "protocol": "Frozen causal-pose experiment, validation-only model and threshold selection",
                "checkpoint_sha256": digest(args.output),
                "selected": selection[index],
                "candidates": selection,
                "curves": curves,
                "training_rows": len(y),
                "training_recordings": len(train_clips),
                "validation_recordings": len(validation),
                "parameters": len(chosen["w2"])
                + (
                    0
                    if chosen["linear"]
                    else len(chosen["w1"]) * len(chosen["w2"]) + len(chosen["b1"])
                )
                + 1,
                "test_accessed": False,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "Selected",
        selection[index]["architecture"],
        chosen["threshold"],
        selection[index]["metrics"]["video_presence"],
    )


def evaluate(args):
    data = json.loads(args.cache.read_text())
    model = TemporalModel.load(args.checkpoint, expected_sha256=args.checkpoint_sha256)
    if set(data["splits"]) != {"test"}:
        raise ValueError("Final evaluation requires test-only cache")
    train = set(model.checkpoint["training_recordings"])
    if train & {c["sample"]["id"] for c in data["clips"]}:
        raise ValueError("Training/test recording overlap")
    if data["model_sha256"] != model.checkpoint["pose_model_sha256"]:
        raise ValueError("Pose provider mismatch")
    start = perf_counter()
    result = summarize(data["clips"], model, include_scores=True)
    result.update(
        checkpoint_sha256=args.checkpoint_sha256,
        cache_sha256=digest(args.cache),
        feature_version=FEATURE_VERSION,
        decision_seconds=perf_counter() - start,
        pose_seconds=sum(c["pose_seconds"] for c in data["clips"]),
        sampled_frames=sum(len(c["rows"]) for c in data["clips"]),
        limitations=[
            "Four positive held-out recordings only",
            "Subject/session/pretraining overlap unknown",
            "Scores are not calibrated probabilities",
            "No industrial validation",
            "Onset delays are offline, detected-only; misses retained",
        ],
    )
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(result["video_presence"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    q = sub.add_parser("extract")
    q.add_argument("--manifest", required=True, type=Path)
    q.add_argument("--pose-model", required=True, type=Path)
    q.add_argument(
        "--splits", required=True, nargs="+", choices=["train", "validation", "test"]
    )
    q.add_argument("--output", required=True, type=Path)
    q = sub.add_parser("train")
    q.add_argument("--cache", required=True, type=Path)
    q.add_argument("--output", required=True, type=Path)
    q.add_argument("--report", required=True, type=Path)
    q = sub.add_parser("evaluate")
    q.add_argument("--cache", required=True, type=Path)
    q.add_argument("--checkpoint", required=True, type=Path)
    q.add_argument("--checkpoint-sha256", required=True)
    q.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    {"extract": extract, "train": train, "evaluate": evaluate}[a.command](a)

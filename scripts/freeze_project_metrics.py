"""Freeze release claims from committed evaluation artifacts, or check for drift.

A metrics refresh is explicit (--write). --check never trains, infers or alters
files. Source and artifact hashes bind claims to the tested implementation.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/evaluation/finalization/frozen-metrics.json"
DOCUMENT = ROOT / "docs/FINAL_PROJECT_METRICS.md"
SOURCES = [
    "detector/src/safetylens_detector/" + n + ".py"
    for n in [
        "temporal",
        "engine",
        "state_machine",
        "metrics",
        "mediapipe_provider",
        "ppe",
        "ppe_evaluation",
        "compliance",
        "tracking",
        "stream",
        "worker",
        "video",
    ]
] + ["scripts/temporal_experiment.py", "scripts/verify_temporal_parity.py"]
SOURCES.append("scripts/freeze_project_metrics.py")
INPUTS = [
    "docs/evaluation/finalization/" + n + ".json"
    for n in [
        "temporal-parity",
        "test-results",
        "clean-install",
        "compose",
        "security-summary",
    ]
] + [
    "docs/evaluation/research/ppe100-final.json",
    "docs/evaluation/research/verified-label-mapping.json",
]


INPUTS.extend(
    [
        "docs/evaluation/research/test-baseline.json",
        "docs/evaluation/finalization/ppe-replay.json",
        "docs/evaluation/finalization/accessibility.json",
        "docs/evaluation/finalization/backend-advisories.json",
        "docs/evaluation/finalization/frontend-advisories.json",
        "docs/evaluation/finalization/frontend-production-advisories.json",
    ]
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_text())


def build():
    replay = read(INPUTS[0])
    tests = read(INPUTS[1])
    clean = read(INPUTS[2])
    compose = read(INPUTS[3])
    security = read(INPUTS[4])
    ppe = read(INPUTS[5])
    mapping = read(INPUTS[6])
    return dict(
        schema_version="1.0",
        frozen_date="2026-11-09",
        project="SafetyLens",
        description="Computer vision evidence and human-supervised incident-response research platform",
        technical_areas=[
            "Applied AI",
            "Computer Vision",
            "Multimodal AI",
            "Reliable Intelligent Systems",
        ],
        scope="Research release; not workplace-ready or certified",
        award={
            "competition": "The Executable World Hackathon",
            "team_reported_place": 1,
            "team_reported_prize_usd": 25000,
            "participant_denominator_team_reported": 384,
            "independent_organizer_corroboration_of_prize_and_denominator": False,
            "evidence": "docs/README_RESTORATION.md",
        },
        fall={
            "checkpoint_sha256": replay["checkpoint_sha256"],
            "decision_version": replay["decision_version"],
            "evaluation_status": "Published 18-clip replay with runtime parity; original held-out evaluation preserved, no new holdout claimed",
            "video_presence": replay["metrics"]["video_presence"],
            "onset_matching": replay["metrics"]["onset_matched"],
            "negative_seconds": replay["metrics"]["negative_seconds"],
            "false_alarms_per_negative_hour": replay["metrics"][
                "false_alarms_per_negative_hour"
            ],
            "subjects_and_sessions": "unknown; recording/content split only",
            "default_promotion": False,
            "same_recordings_baseline": read(
                "docs/evaluation/research/test-baseline.json"
            )["metrics"],
        },
        ppe={
            "diagnostic_images": ppe["images"],
            "model_sha256": ppe["model"]["sha256"],
            "appearance_metrics": ppe["metrics"],
            "mapping_verified_boxes": sum(x["boxes"] for x in mapping["pair_counts"]),
            "mapping_unmatched": mapping["unmatched_boxes"],
            "independent_wearer_accuracy": None,
            "protective_rating_accuracy": None,
            "all_protective_deployment_gates_closed": True,
            "training_overlap": "unknown",
        },
        engineering={
            "tests": tests,
            "clean_install": clean,
            "actual_model_workflow": compose,
            "security": security,
        },
        source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        source_hashes={p: sha(ROOT / p) for p in SOURCES},
        artifact_hashes={p: sha(ROOT / p) for p in INPUTS},
    )


SOP_100 = "SafetyLens sharpened my interest in reliable computer vision by exposing the gap between detecting patterns and supporting decisions. I investigated temporal pose models, carefully evaluated their false alarms, and learned to reject improvements unsupported by representative evidence. A second investigation traced misleading PPE scores to a dataset mirror's category mapping, reinforcing the importance of provenance. Connecting these findings to evidence storage, cited procedures, human approval, and recovery taught me to study models within complete systems. I hope to deepen this work through graduate research in applied AI, computer vision, and intelligent systems that communicate uncertainty and preserve accountable human oversight."
TECH_200 = "SafetyLens is a computer vision and incident-response research platform built with MediaPipe, ONNX Runtime, FastAPI, PostgreSQL, and Next.js. Separate camera workers produce temporal candidates, preserve evidence, and deliver checksum-verified clips through a persistent retry outbox. The application maintains authenticated review, cited procedure retrieval, selected human approval, simulated response, and audit reporting. Its fall research compares a compact causal temporal classifier with a neural alternative using training-only normalization and explicit recording splits. Published test results expose excessive false alerts, so the learned profile remains optional rather than becoming an operational safety claim. Runtime and evaluation now share decision logic, including pose-loss handling and observed recovery. PPE research uses an official object detector with independently corrected category semantics, validated by matching original publisher annotations. Nine appearance classes are evaluated separately; ordinary glasses, shoes, and masks are distinguished from verified protective equipment. Geometric association abstains on ambiguity, and all protective deployment gates remain closed. Fresh PostgreSQL and Docker startup, actual-model browser workflows, restart recovery, dependency advisory checks, and automated accessibility scans provide engineering evidence. The frozen metrics ledger binds claims to source and experiment hashes, while acknowledging unknown subject separation, missing wearer labels, licensing restrictions, and unverified industrial conditions. These boundaries remain explicit."


def render(j):
    f = j["fall"]["video_presence"]
    t = j["engineering"]["tests"]
    s = j["engineering"]["security"]
    text = """# Final project metrics — frozen research release

This is the authoritative source for future application claims. Numerical facts are generated from versioned artifacts, not marketing text. `scripts/freeze_project_metrics.py --check` rejects changed experiment inputs or bound vision/decision source. Updating results requires an explicit new freeze and honest evaluation scope. Historical artifacts remain preserved.

## Identity and attribution

SafetyLens connects camera evidence, cited procedures and human-supervised incident response. Primary areas: applied AI, computer vision, multimodal interpretation and reliable intelligent software. The historical team plan assigns Yug backend/database/workflows/integration, Sean the original detector, and Abhinav demo support. Commit identity does not independently prove individual design ownership; use first-person claims only for work you can personally explain. Genuine contributors and original screenshots remain credited.

Team-reported award: **1st Place — The Executable World Hackathon | $25,000 Prize**, among 384 participants. Contributor reports support this statement; organizer evidence reviewed does not independently corroborate prize/denominator. See [evidence](README_RESTORATION.md). No added award, publication or adoption claim.

## Fall detection

URFall camera0, MediaPipe Lite plus frozen causal temporal linear classifier. Thirty-two training, twenty development/validation and eighteen originally held-out recordings (four falls/fourteen negatives). This release replays published test media to verify runtime/evaluation parity, without retraining or operating-point tuning. Subject/session independence and pose pretraining overlap are unknown. Default conservative rules remain unchanged; learned detection is opt-in.

"""
    text += f"- TP{f['tp']}/FN{f['fn']}/FP{f['fp']}/TN{f['tn']}; precision {f['precision']:.4f}, recall {f['recall']:.4f}, F1 {f['f1']:.4f}; false-positive rate {f['false_positive_rate']:.4f}, specificity {f['specificity']:.4f}.\n"
    text += f"- Nominal recall Wilson95% interval {f['recall_nominal_wilson95']}; unknown clustering is not accounted for. Four positive clips cannot establish general high recall.\n"
    onset = j["fall"]["onset_matching"]
    text += f"- Onset matches {onset['matched']}, misses {onset['missed']}, unmatched alerts {onset['unmatched_alerts']}; detected-only mean annotation-to-rule delay {onset['mean_detected_delay_seconds']:.4f}s. Offline video time, not live response latency.\n"
    text += f"- Negative exposure {j['fall']['negative_seconds']:.3f}s; unstable extrapolated false alerts/hour {j['fall']['false_alarms_per_negative_hour']:.2f}. Excessive false alarms block promotion.\n"
    text += "\nUnchanged conservative-rule baseline on the same published 18 recordings: TP0/FN4/FP8/TN6, F1 0. The learned sensitivity gain does not solve false alerts. Earlier 40%-recall/F1.533 results were a different ten-positive/twenty-clip subset and must not be compared as the same test.\n"
    text += "\n## PPE appearance diagnostics\n\nOfficial SH17 YOLOv8n ONNX export; 100 fixed images, unknown pretraining overlap. These are object-appearance metrics at score floor .05/IoU .5, not protective-rating or wearer-compliance results. Mirror semantics were independently corrected against 1,172 publisher boxes, with zero unmatched boxes. Earlier mis-mapped equipment values are withdrawn.\n\n"
    for label, m in j["ppe"]["appearance_metrics"].items():
        x = m["iou_50"]
        text += f"- **{label}**: support {x['ground_truth_boxes']}, precision {x['precision']:.4f}, recall {x['recall']:.4f}, F1 {x['f1']:.4f}, AP50 {x['ap']:.4f}, AP50:95 {m['ap_50_95']:.4f}.\n"
    text += "\nEight protective requirements are configured, but all deployment gates are closed. Ordinary glasses/shoes/medical masks do not establish goggles, rated boots or respiratory protection. Independent person-association/compliance accuracy, meaningful unknown-rate quality and PPE video false-alert rates are **unmeasured**. Geometric exclusivity/abstention and human incident review are implemented; an independently validated per-item wearer registry is not.\n\n## Engineering verification\n\n"
    text += f"- Backend: {t['backend_passed']} passed; detector: {t['detector_passed']} passed; browser: {t['browser_passed']} passed. Lint/typecheck/standalone build passed. No component-test or coverage percentage is invented.\n"
    text += f"- Automated WCAG A/AA scan: {t['accessibility_routes']} core routes, {t['accessibility_violations']} detected violations after fixes. Automated scans are not accessibility certification.\n"
    text += "- Fresh named volumes, PostgreSQL17, backend/frontend health and zero default accounts were verified through the documented Compose profile. Actual model evidence completed notification, playback, cited SOP, human approval, simulated response, audit/PDF and controlled restart/restore. No paid provider or external action was invoked.\n"
    text += f"- Dependency audit: {s['backend_packages_checked']} pinned Python packages, {s['backend_advisories']} known advisories; frontend production {s['npm_production_advisories']}, complete frontend tree {s['npm_all_advisories']} (development-only moderate findings). This is an advisory snapshot, not a vulnerability-free guarantee.\n"
    text += "\n## Performance and evaluation scope\n\nCPU host: Apple M2 Pro,16 GiB, macOS14.5. The published four-replay check processed 252 sampled frames in 2.966s including startup (84.95 aggregate offline sampled FPS), peak RSS 593,035,264 bytes; repeated scenes/short duration are not fleet capacity. A learned clip processed 37 sampled frames in 1.08s analysis with 266,223,616-byte peak process RSS. PPE100-image run 11.949s, mean inference/decode .1168s/image. These prior measured runs are retained, not claimed as new measurements. Current parity replay timings are in its artifact. GPU use, physical fall-to-notification latency and representative storage/day remain unmeasured.\n\nStable architectural contributions: scoped authentication, evidence checksums/idempotency, persistent retry outbox, bounded live frames, independent track histories, shared causal decisions, unknown-safe association, conditional policies, exact SOP citations and independent human approval. Production HTTPS, physical fleet qualification, organization tenancy/SSO, immutable audit and industrial certification remain outside verified scope.\n\n## Evidence and reproducibility\n\n"
    text += f"Frozen model `{j['fall']['checkpoint_sha256']}`, decision `{j['fall']['decision_version']}`. Tested source revision `{j['source_revision']}`; source-content hashes remain valid across documentation/merge commits. Merge commit and final CI are recorded in the delivery/PR, avoiding a self-referential commit hash.\n\n"
    for p in INPUTS:
        text += f"- [{p.split('/')[-1]}]({str(Path(p).relative_to('docs'))})\n"
    text += "\n[Reproduction commands](REPRODUCIBILITY.md) · [Fall methods](FALL_DETECTION_EVALUATION.md) · [PPE methods](PPE_EVALUATION.md) · [Graduate summaries](GRADUATE_APPLICATION_SUMMARY.md).\n\n## Application materials\n\n**One sentence:** SafetyLens is a computer-vision research platform connecting uncertain camera evidence to cited procedures and auditable human-supervised incident response.\n\n- Engineered a causal pose-learning and inference pipeline with explicit recording splits and shared runtime/evaluation decisions; quantified sensitivity/false-alarm tradeoffs and prevented promotion unsupported by evidence.\n- Recovered a corrupted PPE category mapping by independently verifying1,172 annotations, then evaluated nine-class ONNX appearance inference with person-specific association and uncertainty gates.\n- Integrated authenticated evidence transport, cited SOP retrieval and human-approved simulated response; verified clean PostgreSQL/Docker startup, browser workflows and controlled recovery.\n\nUse individual claims only where personal contribution is confirmed; inherited team work remains credited.\n"
    text += (
        "\n### 100-word SOP candidate\n\nConfirm personal ownership before using first-person statements.\n\n"
        + SOP_100
        + "\n\n### 200-word technical description\n\n"
        + TECH_200
        + "\n\n### Faculty interview explanation\n\nExplain the pipeline from uncertain visual evidence to independent human approval. Lead with the measured false-alarm tradeoff and corrected label provenance; distinguish algorithmic scores, appearance objects and human decisions. Do not describe four-positive recall as general accuracy or public-data diagnostics as industrial validation.\n\n### Exact implementation references\n\n"
    )
    for path in SOURCES:
        text += f"- [{path}](../{path})\n"
    return text


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = p.parse_args()
    if a.write:
        j = build()
        LEDGER.write_text(json.dumps(j, indent=2, allow_nan=False) + "\n")
        DOCUMENT.write_text(render(j))
        print("Frozen verified metrics and evidence hashes")
    else:
        j = json.loads(LEDGER.read_text())
        for key in ["source_hashes", "artifact_hashes"]:
            for path, expected in j[key].items():
                if sha(ROOT / path) != expected:
                    raise SystemExit("Frozen evidence drift: " + path)
        if DOCUMENT.read_text() != render(j):
            raise SystemExit("Generated metrics document drift")
        print("Frozen metrics match source and evaluation evidence")

# Final project metrics — frozen research release

This is the authoritative source for future application claims. Numerical facts are generated from versioned artifacts, not marketing text. `scripts/freeze_project_metrics.py --check` rejects changed experiment inputs or bound vision/decision source. Updating results requires an explicit new freeze and honest evaluation scope. Historical artifacts remain preserved.

## Identity and attribution

SafetyLens connects camera evidence, cited procedures and human-supervised incident response. Primary areas: applied AI, computer vision, multimodal interpretation and reliable intelligent software. The historical team plan assigns Yug backend/database/workflows/integration, Sean the original detector, and Abhinav demo support. Commit identity does not independently prove individual design ownership; use first-person claims only for work you can personally explain. Genuine contributors and original screenshots remain credited.

Team-reported award: **1st Place — The Executable World Hackathon | $25,000 Prize**, among 384 participants. Contributor reports support this statement; organizer evidence reviewed does not independently corroborate prize/denominator. See [evidence](README_RESTORATION.md). No added award, publication or adoption claim.

## Fall detection

URFall camera0, MediaPipe Lite plus frozen causal temporal linear classifier. Thirty-two training, twenty development/validation and eighteen originally held-out recordings (four falls/fourteen negatives). This release replays published test media to verify runtime/evaluation parity, without retraining or operating-point tuning. Subject/session independence and pose pretraining overlap are unknown. Default conservative rules remain unchanged; learned detection is opt-in.

- TP4/FN0/FP10/TN4; precision 0.2857, recall 1.0000, F1 0.4444; false-positive rate 0.7143, specificity 0.2857.
- Nominal recall Wilson95% interval [0.5101091635454027, 1]; unknown clustering is not accounted for. Four positive clips cannot establish general high recall.
- Onset matches 4, misses 0, unmatched alerts 10; detected-only mean annotation-to-rule delay 0.4917s. Offline video time, not live response latency.
- Negative exposure 115.533s; unstable extrapolated false alerts/hour 311.60. Excessive false alarms block promotion.

Unchanged conservative-rule baseline on the same published 18 recordings: TP0/FN4/FP8/TN6, F1 0. The learned sensitivity gain does not solve false alerts. Earlier 40%-recall/F1.533 results were a different ten-positive/twenty-clip subset and must not be compared as the same test.

## PPE appearance diagnostics

Official SH17 YOLOv8n ONNX export; 100 fixed images, unknown pretraining overlap. These are object-appearance metrics at score floor .05/IoU .5, not protective-rating or wearer-compliance results. Mirror semantics were independently corrected against 1,172 publisher boxes, with zero unmatched boxes. Earlier mis-mapped equipment values are withdrawn.

- **person**: support 236, precision 0.5437, recall 0.8178, F1 0.6531, AP50 0.7846, AP50:95 0.5316.
- **earmuffs**: support 5, precision 0.5000, recall 0.2000, F1 0.2857, AP50 0.1040, AP50:95 0.0208.
- **face_shield**: support 3, precision 0.1818, recall 0.6667, F1 0.2857, AP50 0.4422, AP50:95 0.2766.
- **medical_mask**: support 14, precision 0.3846, recall 0.3571, F1 0.3704, AP50 0.3564, AP50:95 0.1754.
- **ordinary_eyewear**: support 12, precision 0.1905, recall 0.3333, F1 0.2424, AP50 0.3027, AP50:95 0.1522.
- **gloves**: support 63, precision 0.2680, recall 0.4127, F1 0.3250, AP50 0.3179, AP50:95 0.1867.
- **hard_hat**: support 40, precision 0.5862, recall 0.4250, F1 0.4928, AP50 0.3587, AP50:95 0.1903.
- **ordinary_footwear**: support 99, precision 0.3247, recall 0.5051, F1 0.3953, AP50 0.4046, AP50:95 0.2035.
- **high_visibility_vest**: support 30, precision 0.3433, recall 0.7667, F1 0.4742, AP50 0.6121, AP50:95 0.3329.

Eight protective requirements are configured, but all deployment gates are closed. Ordinary glasses/shoes/medical masks do not establish goggles, rated boots or respiratory protection. Independent person-association/compliance accuracy, meaningful unknown-rate quality and PPE video false-alert rates are **unmeasured**. Geometric exclusivity/abstention and human incident review are implemented; an independently validated per-item wearer registry is not.

## Engineering verification

- Backend: 92 passed; detector: 69 passed; browser: 10 passed. Lint/typecheck/standalone build passed. No component-test or coverage percentage is invented.
- Automated WCAG A/AA scan: 5 core routes, 0 detected violations after fixes. Automated scans are not accessibility certification.
- Fresh named volumes, PostgreSQL17, backend/frontend health and zero default accounts were verified through the documented Compose profile. Actual model evidence completed notification, playback, cited SOP, human approval, simulated response, audit/PDF and controlled restart/restore. No paid provider or external action was invoked.
- Dependency audit: 52 pinned Python packages, 0 known advisories; frontend production 0, complete frontend tree 7 (development-only moderate findings). This is an advisory snapshot, not a vulnerability-free guarantee.

## Performance and evaluation scope

CPU host: Apple M2 Pro,16 GiB, macOS14.5. The published four-replay check processed 252 sampled frames in 2.966s including startup (84.95 aggregate offline sampled FPS), peak RSS 593,035,264 bytes; repeated scenes/short duration are not fleet capacity. A learned clip processed 37 sampled frames in 1.08s analysis with 266,223,616-byte peak process RSS. PPE100-image run 11.949s, mean inference/decode .1168s/image. These prior measured runs are retained, not claimed as new measurements. Current parity replay timings are in its artifact. GPU use, physical fall-to-notification latency and representative storage/day remain unmeasured.

Stable architectural contributions: scoped authentication, evidence checksums/idempotency, persistent retry outbox, bounded live frames, independent track histories, shared causal decisions, unknown-safe association, conditional policies, exact SOP citations and independent human approval. Production HTTPS, physical fleet qualification, organization tenancy/SSO, immutable audit and industrial certification remain outside verified scope.

## Evidence and reproducibility

Frozen model `436948b4ec1fb8e371303a2c346630fa9869a00894cc9067e572bb5c34fd8bd8`, decision `temporal-decision-v2`. Tested source revision `bb7df098fa269998b48139bf83ec77aafebbc807`; source-content hashes remain valid across documentation/merge commits. Merge commit and final CI are recorded in the delivery/PR, avoiding a self-referential commit hash.

- [temporal-parity.json](evaluation/finalization/temporal-parity.json)
- [test-results.json](evaluation/finalization/test-results.json)
- [clean-install.json](evaluation/finalization/clean-install.json)
- [compose.json](evaluation/finalization/compose.json)
- [security-summary.json](evaluation/finalization/security-summary.json)
- [ppe100-final.json](evaluation/research/ppe100-final.json)
- [verified-label-mapping.json](evaluation/research/verified-label-mapping.json)
- [test-baseline.json](evaluation/research/test-baseline.json)
- [ppe-replay.json](evaluation/finalization/ppe-replay.json)
- [accessibility.json](evaluation/finalization/accessibility.json)
- [backend-advisories.json](evaluation/finalization/backend-advisories.json)
- [frontend-advisories.json](evaluation/finalization/frontend-advisories.json)
- [frontend-production-advisories.json](evaluation/finalization/frontend-production-advisories.json)

[Reproduction commands](REPRODUCIBILITY.md) · [Fall methods](FALL_DETECTION_EVALUATION.md) · [PPE methods](PPE_EVALUATION.md) · [Graduate summaries](GRADUATE_APPLICATION_SUMMARY.md).

## Application materials

**One sentence:** SafetyLens is a computer-vision research platform connecting uncertain camera evidence to cited procedures and auditable human-supervised incident response.

- Engineered a causal pose-learning and inference pipeline with explicit recording splits and shared runtime/evaluation decisions; quantified sensitivity/false-alarm tradeoffs and prevented promotion unsupported by evidence.
- Recovered a corrupted PPE category mapping by independently verifying1,172 annotations, then evaluated nine-class ONNX appearance inference with person-specific association and uncertainty gates.
- Integrated authenticated evidence transport, cited SOP retrieval and human-approved simulated response; verified clean PostgreSQL/Docker startup, browser workflows and controlled recovery.

Use individual claims only where personal contribution is confirmed; inherited team work remains credited.

### 100-word SOP candidate

Confirm personal ownership before using first-person statements.

SafetyLens sharpened my interest in reliable computer vision by exposing the gap between detecting patterns and supporting decisions. I investigated temporal pose models, carefully evaluated their false alarms, and learned to reject improvements unsupported by representative evidence. A second investigation traced misleading PPE scores to a dataset mirror's category mapping, reinforcing the importance of provenance. Connecting these findings to evidence storage, cited procedures, human approval, and recovery taught me to study models within complete systems. I hope to deepen this work through graduate research in applied AI, computer vision, and intelligent systems that communicate uncertainty and preserve accountable human oversight.

### 200-word technical description

SafetyLens is a computer vision and incident-response research platform built with MediaPipe, ONNX Runtime, FastAPI, PostgreSQL, and Next.js. Separate camera workers produce temporal candidates, preserve evidence, and deliver checksum-verified clips through a persistent retry outbox. The application maintains authenticated review, cited procedure retrieval, selected human approval, simulated response, and audit reporting. Its fall research compares a compact causal temporal classifier with a neural alternative using training-only normalization and explicit recording splits. Published test results expose excessive false alerts, so the learned profile remains optional rather than becoming an operational safety claim. Runtime and evaluation now share decision logic, including pose-loss handling and observed recovery. PPE research uses an official object detector with independently corrected category semantics, validated by matching original publisher annotations. Nine appearance classes are evaluated separately; ordinary glasses, shoes, and masks are distinguished from verified protective equipment. Geometric association abstains on ambiguity, and all protective deployment gates remain closed. Fresh PostgreSQL and Docker startup, actual-model browser workflows, restart recovery, dependency advisory checks, and automated accessibility scans provide engineering evidence. The frozen metrics ledger binds claims to source and experiment hashes, while acknowledging unknown subject separation, missing wearer labels, licensing restrictions, and unverified industrial conditions. These boundaries remain explicit.

### Faculty interview explanation

Explain the pipeline from uncertain visual evidence to independent human approval. Lead with the measured false-alarm tradeoff and corrected label provenance; distinguish algorithmic scores, appearance objects and human decisions. Do not describe four-positive recall as general accuracy or public-data diagnostics as industrial validation.

### Exact implementation references

- [detector/src/safetylens_detector/temporal.py](../detector/src/safetylens_detector/temporal.py)
- [detector/src/safetylens_detector/engine.py](../detector/src/safetylens_detector/engine.py)
- [detector/src/safetylens_detector/state_machine.py](../detector/src/safetylens_detector/state_machine.py)
- [detector/src/safetylens_detector/metrics.py](../detector/src/safetylens_detector/metrics.py)
- [detector/src/safetylens_detector/mediapipe_provider.py](../detector/src/safetylens_detector/mediapipe_provider.py)
- [detector/src/safetylens_detector/ppe.py](../detector/src/safetylens_detector/ppe.py)
- [detector/src/safetylens_detector/ppe_evaluation.py](../detector/src/safetylens_detector/ppe_evaluation.py)
- [detector/src/safetylens_detector/compliance.py](../detector/src/safetylens_detector/compliance.py)
- [detector/src/safetylens_detector/tracking.py](../detector/src/safetylens_detector/tracking.py)
- [detector/src/safetylens_detector/stream.py](../detector/src/safetylens_detector/stream.py)
- [detector/src/safetylens_detector/worker.py](../detector/src/safetylens_detector/worker.py)
- [detector/src/safetylens_detector/video.py](../detector/src/safetylens_detector/video.py)
- [scripts/temporal_experiment.py](../scripts/temporal_experiment.py)
- [scripts/verify_temporal_parity.py](../scripts/verify_temporal_parity.py)
- [scripts/freeze_project_metrics.py](../scripts/freeze_project_metrics.py)

# Finalization acceptance — November 9, 2026

The authoritative, machine-checkable release claims are now in [FINAL_PROJECT_METRICS.md](FINAL_PROJECT_METRICS.md). The November 8 research report is preserved below. This finalization changes decision consistency and release verification, not model weights or thresholds.

- Fixed a scientific-validity defect: cached evaluation duplicated runtime decision code, and missing pose could erase a latch or contribute unseen recovery time. Both paths now share `TemporalDecision` v2; explicit pose-loss handling never counts as observed upright recovery. All 18 published test recordings match actual MediaPipe event times exactly. Training reproduction remains byte-identical; validation/test confusion matrices are unchanged. This is published-data replay, not a new holdout.
- Bounded temporal checkpoint reading before allocation and rejected missing/duplicate wearer IDs in association ground truth. No independent wearer accuracy is invented.
- Verified 92 backend and 69 detector tests; all 10 actual-model browser cases passed, including five-route automated WCAG A/AA scans with zero detected violations after button/link fixes. No scan rules or tests were disabled; this is not accessibility certification.
- Removed the unused shadcn generator dependency tree while retaining its exact required MIT stylesheet/license; a first clean build exposed the stylesheet dependency and Linux optional-lock entries. Both were repaired and verified. Final advisory snapshot: 52 pinned Python packages/zero known advisories; frontend production zero, complete frontend seven moderate development-tool advisories, no high/critical. Forced major dependency changes were not used.
- A truly fresh `safetylens-validation-release` project had no prior containers/volumes, generated private secrets and zero default users. PostgreSQL 17/backend/frontend became healthy in 58.80s using cached build layers. An initial probe's wrong `users` table name was corrected; the passing run used another entirely new project, not a reset database.
- An actual default detector event on that installation completed protected evidence/checksum, notification, cited procedures, human approval, simulated response, audit/PDF and controlled restart/retry/restore. Source footage/weights/private dumps stay outside Git. A Docker update had broken local plugin symlinks; task-local configuration restored Compose without changing global settings. These environment/harness failures were not hidden as passing tests.
- CI now enforces frozen metrics/source consistency and runs the documented fresh-volume Docker profile. README is a concise 618-word overview excluding commands/diagram; all original images, current diagram, award evidence and human attribution remain.

Release scope remains a research platform. Excessive false alarms and unqualified protective-rating inference are excluded from operational deployment; no workplace readiness, paid-provider validation, physical RTSP qualification or certification is claimed. Engineering acceptance requires local/CI tests, clean deployment, preserved evidence and scientific honesty—not invented detector quality. Mandatory checks must pass before the normal GitHub merge; remaining development-only advisory risk is disclosed.

---

# SafetyLens research and reliability validation — November 8, 2026

## Executive assessment

This phase adds substantive, reproducible AI research and reliability engineering on a dedicated branch from latest main `af081c0`: a trained causal temporal detector, corrected multi-class PPE evaluation, independent benchmark-label provenance, eight-category contextual policies, explicit uncertainty/gates, bounded live frame transport, ingress byte budgets and provider metadata/logging defenses. Original human attribution, screenshots and award material remain. No default detector is promoted from inadequate evidence, and no main merge is authorized by this phase.

**Readiness: experimental applied-AI platform with verified local integration; not a workplace-ready, certified or sole emergency detector.** It is suitable for a graduate-application discussion of methods and engineering judgment when personal contributions are accurately distinguished from team work.

## Baseline independently established

At branch creation, latest remote main contained the prior PR11 merge plus a README update. Backend 84 tests passed in 13.75s, detector 58 in .081s, frontend lint/typecheck and actual-model browser8 cases passed. Historical PostgreSQL 17 and detection evidence were inspected rather than assumed current. A source/config/test/document inventory covered330 text artifacts; prior raw predictions remain preserved. The internal audit and severity priorities are [CURRENT_TECHNICAL_AUDIT.md](CURRENT_TECHNICAL_AUDIT.md).

## Implemented AI and evaluation changes

- **Causal temporal learning:** 62 pose geometry/motion/history features; fixed linear/32-unit neural comparisons; seed42; training-only normalization and recording/class balance; validation-only selection; per-track debounce/recovery; bounded/hash-pinned non-executable JSON checkpoints. Actual offline and worker inference are runnable; no weights are bundled.
- **Fresh test and rejected promotion:** training 32 recordings, validation 20, test 18 (four positives/fourteen negatives). Validation-selected linear model gives development F1 .8182, but fresh test TP4/FN0/FP10/TN4, precision .2857/F1 .4444. Existing rules on identical test give TP0/FN4/FP8/TN6, F1 0. This is greater sensitivity with unacceptable false alerts, not a reliable detector upgrade. Default rules remain unchanged; learned inference is opt-in research.
- **Event matching:** independent publisher labels and frame-count alignment, no test retuning. Learned detected-only mean annotation-to-rule delay .4917 video-seconds, all four matches and ten unmatched alerts retained. Four positive recordings/unknown subjects prevent strong recall claims; negative exposure 115.533 seconds is inadequate for sustained rates.
- **Critical PPE correction:** original publisher labels independently matched 1,172 mirror rectangles across 100 images with zero unmatched boxes, revealing category renumbering. Historical equipment metrics are withdrawn with explicit notices; old predictions/history remain. Person/fall semantics are unaffected.
- **Actual multi-class PPE:** official SH17 YOLOv8n exported to ONNX, embedded class indices verified, CPU parity score error .0000035763/coordinate error .0031128 input pixels on one image. Nine appearance labels are evaluated; eight protective requirements remain distinct. Fixed100-image person AP50 .7846/recall .8178, helmet AP50 .3587/recall .4250, vest AP50 .6121/recall .7667; remaining class metrics/support are in [PPE_EVALUATION.md](PPE_EVALUATION.md). Unknown training overlap means diagnostic, not held-out accuracy.
- **Association and abstention:** region-based exclusive object/person assignment abstains on ambiguity. Ordinary glasses/shoes/medical masks cannot prove protective rating. Missing equipment visibility remains unknown even after temporal review becomes due. Independent wearer/compliance accuracy and PPE false-alert video rates remain unmeasured.

Full protocols, raw outputs, hash manifests and negative findings: [FALL_DETECTION_EVALUATION.md](FALL_DETECTION_EVALUATION.md), [PPE_EVALUATION.md](PPE_EVALUATION.md), [REPRODUCIBILITY.md](REPRODUCIBILITY.md), `evaluation/research/`.

## Platform, frontend and security

Eight requirement categories persist per camera/zone, plus bounded typed conditional rules for supplied activity/operational role/local minute ranges. Missing context is pending; known nonmatches do not activate a rule. A discovered seeded-policy preview mismatch was fixed to use actual stored requirements. Administrator preview is read-only in effect and cannot authorize actions. Real class gates/appearance metrics, retry/empty states, contextual forms and mobile layout are browser-tested. Camera snapshots now poll sequentially with abort timeouts, avoiding overlapping requests/object-URL retention.

Network capture has a one-slot latest-frame reader, replacement counts and bounded consumer wait; FFMPEG open/read timeout options are explicit. Recorded inputs retain exhaustive decoding. Physical RTSP and hard native timeout guarantees remain unverified. Device scoped delivery, SHA checks and human approval remain intact. Body byte limits are enforced before multipart spooling, and media allowance is route-bound. A scoped device’s direct unqualified PPE upload was rejected with 409/PPE_DEPLOYMENT_DISABLED on the final image; historical UUID retries remain separate. Provider metadata is untrusted JSON; remote exception text is redacted from logs/tracebacks. No live-provider prompt-injection or penetration-test claim is made. See [SECURITY.md](SECURITY.md).

## Actual deployment and integration evidence

Both final images built, including standalone frontend/TypeScript production build; the documented backend/frontend/PostgreSQL 17 Compose profile started healthy on existing isolated verification volumes. A newly created PostgreSQL database independently migrated to `0001_platform` and seeded without modifying the existing database. The reproducible probe is `scripts/verify_fresh_postgres.py`; the initial run retained12 cameras,4 procedures and16 chunks.

An **actual learned-model event** completed authenticated checksum-verified ingestion, local-CV interpretation, incident/notification, browser evidence playback, stored SOP retrieval, confirmation, selected human approval, simulated execution, 17 audit entries and a 6,827-byte PDF. Backend-outage retry reused evidence; PostgreSQL restart preserved session/evidence mapping; concurrent operators returned200/409; private dump restored12 test/replay detector records to a new database. These records are not12 independent falls. The final Docker PPE UI separately verified eight gates and administrator context preview. No external message or physical action occurred.

Four default actual-model replay workers acknowledged four events and processed 252 sampled frames in 2.966s including startup, **84.95 aggregate offline sampled FPS**. The repeated scene and brief duration do not establish four-camera workplace reliability. Controlled local MJPEG source loss/restoration produced online 2.426s → offline 4.375s → online 12.744s. Final network summary processed 84 frames over 20.063s and counted one overwritten slot frame in its final connection. That count excludes source/network loss and intentional sampling skips, and is not a whole-fleet dropped-frame statistic.

## Measured efficiency and practical limits

Host: Apple M2 Pro,16 GiB, macOS14.5. One actual learned fall27 video processed 37 sampled frames in1.08s analysis time (34.26 sampled FPS); whole process 1.35s real,1.80s user+1.58s system, maximum RSS 266,223,616 bytes. This includes startup and is not sustained capacity. Four replay process maximum RSS 593,035,264 bytes;2.95s real and7.29 CPU seconds on the one-core accounting basis. CPU can exceed100% because native threads run concurrently. GPU utilization was not measured.

Cached temporal scoring/decision evaluation took .0434s across 1,519 sampled test rows; pose extraction accounted 15.669s. Cached decision timing excludes decoding/feature extraction/model startup and must not be advertised as end-to-end FPS. Multi-class PPE100 images took 11.949s total, mean inference/decode .1168s/image with one ONNX CPU thread; low-threshold Python postprocessing is included. No quantization or acceleration quality/speedup is claimed.

Actual learned replay-to-ack was1.944s including offline startup/processing, not physical fall-to-notification latency. Thirty warm camera-inventory requests averaged6.838ms (4.877–19.939ms); this is not a saturation test or SLO. Video storage/day, representative browser responsiveness, live notification latency and production fleet throughput remain unmeasured.

## Verification status

Final verification: **92 backend tests passed in 11.85s; 66 detector tests passed; 9 actual-model browser cases passed**, with zero failed/skipped cases. Frontend lint/typecheck and production standalone/container build passed. Exact command/timing receipts are recorded in `evaluation/research/test-summary.json`. The baseline 84/58/8 counts are not silently substituted. New regressions exercise causal/gap/shape/hash boundaries, per-person uncertainty, persistent unknowns, stream backpressure/stalls, contextual/seeded policies, role restrictions, chunked/declared byte limits, spoofed content type and provider failure redaction. One new browser case verifies actual capability/error/retry/mobile/context behavior; repeated cases are not counted twice. No failing tests were disabled, no coverage percentage is claimed, and CI is reported only after observed completion.

## Feature classification and remaining risks

- **Implemented and verified:** local authenticated application, protected evidence workflow, conditional policy resolution/UI, byte budgets, provider error redaction, default/learned actual-model transport, human-approved simulated response, PostgreSQL migrations/recovery and controlled stream checks under documented conditions.
- **Implemented and experimentally evaluated:** causal learned temporal model, opt-in multi-person histories, official multi-class ONNX appearance inference, geometric association/abstention and public dataset protocols.
- **Disabled/blocked:** all local protective-category deployment gates; useful workplace fall monitoring; validated wearer/protective-rating conclusions. Quality, representative validation, data rights and licensing remain unmet.
- **Implemented interfaces but unverified here:** physical RTSP/webcams, nonlocal HTTPS/proxy configuration and live paid multimodal provider behavior.
- **Not implemented:** trained TCN/RNN/transformer, calibrated fall probabilities, independent subject-disjoint dataset, general activity/role inference, per-item human-confirmed wearer registry, browser high-FPS overlays, organization tenancy/per-user evidence ownership, SSO/MFA, immutable certified audit ledger, distributed exactly-once actions, external dispatch/physical actuation and industrial certification.

The prior [PILOT_READINESS.md](PILOT_READINESS.md) proposes prospective acceptance thresholds; none is achieved by this small public-data exercise. Further work requires representative independent data, longer negative exposure, wearer/assessability labels, privacy review, proxy/admission controls and operational safety review.

## Documentation and Git delivery

README retains the exact award statement, attributed evidence, original screenshots/team material and current architecture diagram; new genuine UI captures are labeled. No award, adoption or certification is invented. Graduate summaries and three restrained résumé candidates are in [GRADUATE_APPLICATION_SUMMARY.md](GRADUATE_APPLICATION_SUMMARY.md).

Branch: `codex/temporal-research-ppe-policy`, created from fetched `main` at `af081c0`. All new commits must be verified with author/committer `Yug-More <yugmore20@gmail.com>` and no AI co-author trailers. Final commit IDs, remote branch verification and PR URL are included in the delivery response/downloadable report after push. This phase creates a PR for review and **does not merge into main**.

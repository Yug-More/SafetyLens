# Causal temporal fall research — November 8, 2026

## Architecture and comparison

The deployed default remains MediaPipe Lite plus the existing calibrated temporal rules. New `detector/src/safetylens_detector/temporal.py` adds a separate opt-in causal learned classifier. `CausalFeatures.process` derives six normalized pose quality/geometry/motion values and trailing 0.5/1/2-second mean/range/change summaries, coverage and density: 62 features. No future frames are consulted. Low torso visibility and long observation gaps reset feature history. Independent per-track state is bounded; ambiguous geometric IDs and expiry do not establish real identity.

`scripts/temporal_experiment.py` trains two fixed alternatives: class/recording-balanced regularized logistic classification and a 32-unit tanh temporal MLP. Training-only normalization, seed 42, 300 Adam epochs, learning rate .01 and L2 .001 are fixed. Validation-only thresholds .3/.5/.7/.9 and F1/precision/compactness selection choose the linear model at .9. Its 63 learned coefficients are not calibrated fall probabilities. Normalization and fixed identity projection are additional checkpoint data. No pretrained temporal network, TCN or transformer is claimed. Given limited subject metadata, a larger network was not justified by validation.

`TemporalDetectorEngine.process` requires sustained score, at least half a second of history, per-track latching and sustained upright recovery. `mark_missing` abstains; lost/recreated tracks cannot establish physical event identity across long outages. Hash-pinned JSON loading validates shape, numeric finiteness, size and feature version; no pickle checkpoint is loaded for temporal inference. Worker use requires explicit checkpoint and SHA plus the matching pose-model hash. Default rules remain unchanged.

## Data and scientific boundaries

UR Fall Detection Dataset, Kwolek and Kepski, University of Rzeszow: [publisher](https://fenix.ur.edu.pl/~mkepski/ds/uf.html). CC BY-NC-SA 4.0; noncommercial academic research, not commercial clearance. Camera-0 composite videos use explicit right-half RGB calibration. All 70 file hashes and exact split/group IDs are in [urfall-manifest.json](evaluation/research/urfall-manifest.json). Raw media and learned weights stay outside Git.

- Training: falls 01–16 and ADLs 01–16, 32 recordings.
- Validation: falls 17–26 and ADLs 17–26, 20 recordings. These previously examined recordings are explicitly development data now.
- Fresh test: falls 27–30 and ADLs 27–40, 18 recordings, four positives and fourteen negatives.

This is recording/content separation. Publisher subject/session identities and pose pretraining overlap are unknown, so subject-disjoint generalization is not established. No paired camera view crosses training/test; this experiment measures camera 0 only. Camera-1 evaluation from the previous phase is historical; the proposed new angle-transfer extension was not performed. Four fresh positive recordings are too few to support high-recall claims. Previous historical twelve/twenty/thirty-clip results are preserved and must not be pooled as independent tests.

The [protocol](evaluation/research/protocol.txt), [checkpoint/source freeze](evaluation/research/model-freeze.json), [candidate selection/curves](evaluation/research/selection.json) and identical same-host retraining receipt establish the procedure. The test split was extracted only after selection. Formatting subsequently preserved Python ASTs. No test-driven threshold retuning followed the negative result.

## Results, including the unfavorable tradeoff

Validation-selected model: TP9/FN1/FP3/TN7, precision .75, recall .90, F1 .8182. This is a selected development result, not held-out accuracy.

On the identical fresh 18-clip test:

- Existing conservative rules: **TP0/FN4/FP8/TN6**, precision 0, recall 0, F1 0, specificity .4286, false-positive rate .5714 and false-negative rate 1.
- Frozen learned temporal model: **TP4/FN0/FP10/TN4**, precision .2857, recall 1, F1 .4444, specificity .2857, false-positive rate .7143 and false-negative rate 0.

Raw baseline predictions: [test-baseline.json](evaluation/research/test-baseline.json). Learned per-sample scores/alerts: [test-results.json](evaluation/research/test-results.json). A 100% point recall over four staged recordings is **not reliable high recall**: nominal Wilson 95% interval [.5101,1], ignoring unknown subject clustering. Precision interval [.1172,.5465]. The larger MLP did not win validation and was not post-hoc selected against test results.

Publisher camera-0 frame labels independently define first transition label 0, indexed one-based; frame-count alignment is checked for every positive. First event within five seconds or clip end is matched; unmatched events and misses are retained. Learned matching found four matches, zero misses and ten unmatched negative alerts. Detected-only annotation-to-rule delays: .600/.400/.333/.633 seconds, mean .4917. This is offline video time, not notification/medical response latency.

Negative exposure is only 115.533 seconds: baseline 8 alerts gives approximately 249.28/hour, learned 10 gives 311.60/hour. These unstable extrapolations demonstrate excessive false-alert burden, not a sustained camera-hour test. Public clips lack independent scenario tags sufficient for a comprehensive sitting/kneeling/slip/exercise/occlusion breakdown. Per-file scores, missing observations and raw events support inspection; no invented per-scenario accuracy is supplied.

## Failure analysis and deployment decision

Earlier rules missed short post-fall tails, lost poses and insufficient down-posture confirmation; intentional reclining/bending also triggered alerts. Learned training improves sensitivity to fall-like posture trajectories but transfers poorly to the later ADLs: the resulting alert burden is unacceptable. Neither tuning to these test clips nor advertising only recall would solve this reliability problem. The learned engine remains explicitly experimental and opt-in, without promotion to default or a workplace-readiness claim.

Needed next: independent subject/session metadata and consented target-camera footage; independently labeled intent, onset, recovery and wearer visibility; longer realistic negative exposure; calibration/abstention and prospective false-alert acceptance gates fixed before evaluation. This phase establishes a runnable learning/evaluation path and a defensible rejection of promotion, not a solved safety classifier.

Actual runtime, CPU/memory and multi-camera results are in [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md). Training/inference commands: [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

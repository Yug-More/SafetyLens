> **November 8 correction:** historical PPE equipment metrics in this document used a mis-mapped mirror category order and are withdrawn. Person and fall metrics are unaffected. See [PPE_EVALUATION.md](PPE_EVALUATION.md) for independently verified semantics and corrected results; [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md) is the current status. Historical findings remain below for traceability.

# Final detection validation

## Protocol and frozen change

Base code `9c9315c` and all prior 12-clip outputs remain preserved. The original twelve clips are now development diagnostics, not an untouched final test. The candidate changes were fixed before predictions on UR Fall camera-0 fall-07..16 and adl-07..16: explicitly crop the RGB half of each composite depth/RGB input, preserve descent observed in CONFIRMING, retain the conservative thresholds unchanged. `evaluation/final/candidate-freeze.txt` and source hashes record this decision. No threshold sweep, training or selection against these twenty results occurred. The baseline uses archived pre-change source and the original full composite input. Thus the comparison measures a combined input-calibration and state-machine correction, not a learned classifier improvement or an ablation proving which change contributed how much.

Twenty new clips are content-disjoint from the diagnostic twelve. They are not independently certified subject-disjoint; identities and pretrained-model overlap are unknown. Camera settings share dataset environments. Video-category labels are supplied by UR Fall, not invented by this project. No independent onset annotations were available; all confusion matrices below are video-presence results, not temporally matched event-level results.

## Original four false negatives

Actual frames/contact sheets and per-sample traces were inspected. The composite input includes a rendered depth silhouette that can attract the single-person pose tracker. In the original full-frame trace:

- fall-01: 27 detected poses / 64 analyzed samples, 37 missing. Down-posture confirmation is interrupted by track loss; late reacquisition cannot complete the window before EOF. RGB calibration gives 55 poses/64 and a counted fall event on the diagnostic rerun.
- fall-03: 86/86 poses but no confirmed horizontal hold. The person approaches the camera and falls near the image boundary; the full-body geometric condition is not sustained. RGB calibration still misses this clip. This is an unresolved limitation, not fixed by claiming that a visible pose implies reliable posture.
- fall-04: 39/39 poses; enters confirmation without rapid descent, but later descent was not retained by the CONFIRMING branch. The corrected candidate emits a fall event. The short tail and continued movement made the alternative low-motion path insufficient.
- fall-05: 31 detected / 61 analyzed, 30 missing. Confirmation resets to monitoring and then track-missing; RGB calibration yields 52/61 poses and a counted event.

`evaluation/final/miss-diagnostics.json` preserves compact frame-state evidence. New diagnostic results are TP5/FN1/FP0/TN6 (F1 .9091). These are post-diagnosis development results and must not be presented as fresh generalization evidence.

## Untouched twenty-clip comparison

Preserved pre-change conservative baseline: **TP5, FN5, FP2, TN8**, precision .7143, recall .5, F1 .5882. Calibrated candidate: **TP8, FN2, FP2, TN8**, precision .8, recall .8, F1 .8. Candidate precision and recall Wilson 95% intervals are both approximately [.4902,.9433]. The two confidence intervals are not evidence of a statistically established population improvement.

Negative duration is .0219906 camera-hours (79.166 seconds). Two alerts correspond to approximately 90.95 alarms/hour; this highly unstable number cannot be extrapolated to a deployment. Actual negative clips adl-10 and adl-11 show the person sitting and deliberately reclining on a couch. The rule set does **not reliably distinguish intentional reclining from falling**. No bed/furniture model or intent inference is implemented. Candidate misses fall-13 and fall-15: inspected frames contain an additional seated person, a rapid forward fall, partial lower-frame truncation and little post-fall footage. Stable multi-person target selection and truncated observations remain unresolved. No post-test retuning was performed.

Walking, sitting, bending and intentional reclining are represented in inspected footage. Kneeling, running, camera movement, systematic occlusion and longer crowd activity were not independently labeled and exhaustively evaluated. Constructed temporal unit tests do not substitute for those scenarios.

Raw per-video predictions/transitions, parameters, model SHA and timings: `evaluation/final/baseline-results.json` and `candidate-results.json`. Observed analyzed throughput approximately 80.58 and 81.03 FPS respectively on Apple M2 Pro; these runs overlapped other local work and are not isolated capacity benchmarks. Target sampling is 12 input samples/s. Worker sampling drift was subsequently fixed to use the same fixed replay clock. No measured onset latency, GPU utilization or long-duration fleet capacity is claimed.

## Real labeled PPE evaluation

Prespecified first 24 lexicographic filenames from the SH17 COCO mirror test partition, 92 supported annotations: 57 person, 28 helmet, 7 vest. The mirror exports 640×640 stretched images and numeric category names; IDs are mapped using the [authoritative SH17 YAML](https://github.com/ahmadmughees/SH17dataset/blob/master/sh17.yaml): 0 person, 10 helmet, 16 safety-vest. No images were chosen based on successful predictions. No weights were trained or tuned here; overlap with the reference model's undisclosed training data is unknown. Therefore this is a labeled external diagnostic, not proven training-disjoint validation.

Reference ONNX model hash remains `b99fed37bae1d111ddb622a0ef9077d42918a4daebd4a0bffbd8faaba273f246`. CPU Runtime accepts float32 [1,3,640,640], emits [1,18,8400]; actual letterboxing/RGB normalization, class decoding and per-class NMS execute. Model threshold for AP collection .05, NMS .45; these truncated-score AP values are not COCO leaderboard-equivalent. At IoU .5:

- Person: 2 predictions, precision 1.0, recall .03509, AP50 .03960; AP50:95 .007921.
- Hard hat: 18 predictions, precision .05556, recall .03571, AP50 .005658; AP50:95 .001132.
- Vest: 13 predictions, precision 0, recall 0, AP50 0; AP50:95 0.

Macro AP50:95 **.003017**. This is poor performance and excludes this reference model from deployment. Its two correct person predictions do not establish useful person recall. Total recorded inference/decode/read time for 24 images: 21.717 seconds (approximately .905 seconds/image average, not a latency percentile). Raw boxes and per-class calculations are in `ppe-results.json`. Runtime metadata and one additional actual-inference smoke are in `ppe-runtime.json`. Preview overlays draw actual boxes and explicitly label possible missing PPE; raw incident evidence remains unchanged. Overlay generation is exercised separately, not a validated PPE-incident benchmark.

Association/compliance accuracy and false-compliance/violation rates remain **unmeasured**: object boxes do not label wearer relationships or assessability. No relations were fabricated. The adapter and temporal association are functional software, but the currently evaluated model is not a trustworthy PPE monitor.

## Licenses and reproduction

[UR Fall](https://fenix.ur.edu.pl/~mkepski/ds/uf.html) and [upstream SH17](https://github.com/ahmadmughees/SH17dataset#license) restrict dataset use under CC-BY-NC-SA-4.0. The SH17 mirror labels itself CC-BY-4.0; the archived acquisition manifest retains that mirror declaration for hash reproducibility, **not permission to override the upstream noncommercial restrictions**. No image/video is redistributed here. The reference model's card/ONNX license conflict remains unresolved; commercial deployment is excluded. See MODEL_REGISTRY.md.

```sh
python scripts/acquire_final_validation.py --kind urfall --directory /tmp/safetylens-urfall20
python scripts/acquire_final_validation.py --kind ppe --directory /tmp/safetylens-ppe24
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.evaluation --manifest /tmp/safetylens-urfall20/manifest.json --model /path/pose_landmarker_lite.task --profile conservative --output /tmp/candidate.json
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.ppe_evaluation --manifest /tmp/safetylens-ppe24/manifest.json --model-manifest /path/ppe.json --output /tmp/ppe-results.json
```

The final manifests retain exact URLs/hashes; if upstream content changes acquisition refuses it. Original code can be checked out separately at `9c9315c` for the preserved baseline. Running that evaluator ignores the candidate pose-region field, reproducing the full-frame baseline. No model downloads occur implicitly in application startup.

## Final hardening research — broader recording/camera check

The earlier twelve and twenty-clip runs remain above and in their original JSON. They are development evidence for this phase. Before new predictions, `evaluation/hardening/freeze.json` fixed a comparison of the existing calibrated Lite single-pose profile, official Full model under the same rules, and an opt-in four-pose geometric tracker. No temporal thresholds were lowered. The tracker uses mutual unambiguous geometry, new IDs on ambiguous crossings, expiry and a 64-track memory cap. It cannot establish biometric identity or reliable occluded tracking. `test_tracking.py` checks order swaps, ambiguity, expiry and bounded memory. Full and tracked alternatives are not silently made defaults.

New recording IDs17–26 supply twenty camera0 clips (ten fall/ten ADL) plus ten paired camera1 fall views. Camera1 negatives are unavailable. Both views of a recording share a group and remain in the test partition. They are **not thirty independent physical events**. Subject/session separation and pretrained overlap cannot be established. The [publisher](https://fenix.ur.edu.pl/~mkepski/ds/uf.html) identifies the two viewpoints and provides the labels/data; no industrial scenario or extra camera1 negatives are invented. Source hashes and all transitions are retained in `evaluation/hardening/`.

Camera0 video-presence results on the same new clips:

- Preserved `9c9315c` comparison code, full composite input: TP2/FN8/FP1/TN9; precision .6667, recall .2, F1 .3077.
- Current calibrated Lite/default: **TP4/FN6/FP1/TN9**; precision .8, recall .4, F1 .5333.
- Full model/same temporal rules: TP4/FN6/FP0/TN10; precision1 on four predictions, recall .4, F1 .5714.
- Lite/four-pose tracking: TP5/FN5/FP2/TN8; precision .7143, recall .5, F1 .5882.

All configurations found four of ten camera1 positives. Its false-positive rate is unmeasured. Do not pool the two camera views as independent trials. The default camera0 recall's nominal Wilson interval is [.1682,.6873]; precision [.3755,.9638]. These binomial intervals ignore unknown subject/session clustering and are not population guarantees. Negative exposure is only **67.666 seconds**: one default alert corresponds to an unstable53.20/hour. Full's zero observed alerts does not establish a zero operational rate. Raw all-candidate alerts on negatives equal1/0/2 for Lite/Full/tracked respectively, so slow person-down candidates are not hidden from the workload accounting on this set.

The earlier F1 .8 does **not generalize** to this check. Development Full F1 .8 merely tied Lite while running more slowly; four-pose development F1 .7619 was worse than Lite. No new-set result was used to retune or silently select a default.

### Inspected remaining failures

Actual contact sheets and state histories were reviewed. Default camera0 misses: fall17 (33 poses/5 missing),18 (21/5),19 (29/11),21 (17/5),23 (26/4),25 (28/6). fall17/21/25 enter confirmation late and never complete it; fall18 returns from confirming to monitoring; fall19 loses the track; fall23 remains suspected without a confirmed down sequence. These are observed algorithmic failure paths, not proof of a single universal cause. Reviewed footage includes forward movement, lower-frame truncation, a seated additional person and short post-fall tails. The default false alert in adl17 occurs while bending/handling an object in low light; partial geometry can resemble sustained down posture. Intentional couch reclining false alerts from the prior development set remain unresolved. The alternative tracker has its own two new negative alerts. Exhaustive kneeling/running/camera-motion and occlusion validation is still absent.

### Publisher-onset matching and latency

Frame labels were subsequently acquired **without changing predictions or thresholds**. `scripts/match_publisher_onsets.py` implements the protocol recorded before label/prediction comparison in `onset-protocol.txt`: camera0 fall-category onset is the first publisher transition label0; match the first alert within five seconds or clip end; retain unmatched alerts and all misses. Labels span one-based indices matching decoded frame counts for all ten clips. For fall17, the raw95-frame RGB archive was checked at frames1/59/71 against the composite MP4's RGB half; mean absolute RGB pixel differences were approximately2.43/2.56/2.58 after resizing/compression. This is direct alignment evidence for that archive, not a guarantee of absolute depth/RGB sensor synchronization across the dataset.

Matched event counts agree with the video-presence counts here: original2 detected/8 missed/1 unmatched alert; Lite4/6/1; Full4/6/0; tracked5/5/2. Default **detected-only** video-time delays: [1.700,1.067,1.067,1.200] seconds; mean1.258, median1.133. Six misses have no finite delay and must stay visible. Full mean1.300s on four matches; tracked mean1.240s on five. These are annotation-to-rule-event delays in fixed-rate video, **not live capture-to-notification latency**, medical response time or a percentile guarantee. Camera1 is excluded from onset matching. `onsets-*.json` retains every match/miss and source-label hash. True-negative counts denote negative videos, not a per-frame event confusion matrix.

### Reproduction

```sh
python3 scripts/acquire_final_validation.py --kind hardening --directory /tmp/safetylens-hardening-holdout
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.evaluation --manifest /tmp/safetylens-hardening-holdout/manifest.json --model /path/pose_landmarker_lite.task --profile conservative --output /tmp/lite.json
# Use the same command with the official Full task, or --profile tracked with Lite.
curl -fL https://fenix.ur.edu.pl/~mkepski/ds/data/urfall-cam0-falls.csv -o /tmp/publisher-labels.csv
python3 scripts/match_publisher_onsets.py --results /tmp/lite.json --labels /tmp/publisher-labels.csv --output /tmp/onsets.json
```

Source model paths, file hashes, preprocessing and resource measurements are in the raw results, frozen manifest and PERFORMANCE_REPORT.md. No training of a TCN/RNN/transformer is claimed: trustworthy subject/session-separated training labels were not established, and fitting these small test sets would not justify a reliable classifier.

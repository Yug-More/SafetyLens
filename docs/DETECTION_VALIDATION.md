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

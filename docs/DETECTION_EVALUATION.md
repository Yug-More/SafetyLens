# Detection evaluation — November 7, 2026

## Actual external experiment

Source: [UR Fall Detection Dataset](https://fenix.ur.edu.pl/~mkepski/ds/uf.html), Kwolek and Kepski, 2014. Publisher license: CC BY-NC-SA 4.0, noncommercial academic use. Video is not redistributed. Prespecified subset: camera 0 fall-01 through fall-06 and adl-01 through adl-06, 12 clips, 15,289,036 downloaded bytes. Labels are publisher video-category labels. No SafetyLens model was trained and no thresholds were tuned on these clips. Subject identifiers are unknown; this is NOT demonstrated subject-disjoint evaluation. Pretrained pose model pretraining overlap is unknown.

`evaluation/urfall-12-manifest.json` preserves sources, labels, splits and SHA-256 hashes. The same unknown-subject group is entirely in the test split. `evaluation/urfall-12-legacy.json` and `evaluation/urfall-12-conservative.json` preserve every event, transition, timing and failure case. Their video-presence metrics do not require an alert to overlap an annotated falling interval; that is a limitation, not an event-level accuracy result.

### Results

- Legacy configuration: TP=2, FN=4, FP=1, TN=5; precision 2/3; recall 2/6; F1 0.4444. One negative-video alert in 0.0099075 negative camera-hours (approximately 35.7 seconds). The derived 100.93 false alarms/hour is unstable and must not be extrapolated to real installations.
- Conservative fall classification: TP=2, FN=4, FP=0, TN=6; precision 2/2; recall 2/6; F1 0.5. Zero observed false alarms in this tiny negative duration does NOT establish a zero false-alarm rate. Precision Wilson 95% interval approximately [0.3424, 1.0]; recall interval [0.0968, 0.7000].
- Legacy processing throughput: approximately 76.79 analyzed frames per processing second; conservative approximately 77.64. Both target 12 input samples/second. These are offline single-process throughput measurements on Apple M2 Pro, not multi-camera throughput or end-to-end alert latency. Per-video provider initialization is included in the recorded processing time; decoding overhead is included by the runner.
- No onset labels were supplied. Event detection latency and onset-matched event confusion are **not measured**. CPU utilization, GPU utilization, peak memory, queue latency and production alert latency are **not measured**.

These results show poor recall on this external subset. The enhanced worker is experimental and is not suitable for unattended life-safety decisions. The conservative profile was implemented before evaluation: overhead displacement disabled; only rapid-drop events count as fall evidence. Sustained down posture without observed descent is reported separately as person-down. The legacy configuration is retained for reproducibility. Neither profile has been tuned against the test set after seeing these results.

## Runtime failure and recovery

The original declared MediaPipe 1.0.1 package aborted natively during initialization, including outside the sandbox. The isolated MediaPipe 0.10.21 runtime succeeded outside the sandbox with the CPU delegate. It still needed an OS graphics context on this Mac; inside the sandbox it failed to create NSOpenGLPixelFormat. The verified video extra now pins MediaPipe 0.10.21, OpenCV contrib 4.11.0.86 and NumPy 1.26.4. Backend and detector environments are separate to avoid conflicting OpenCV distributions. Headless Linux/container pose execution remains unverified here.

## Reproduction

From the repository root:

```sh
python3.12 -m venv detector/.venv
uv pip sync --python detector/.venv/bin/python detector/requirements-video.lock.txt
python scripts/acquire_urfall.py --directory /tmp/urfall-check
# Acquire the pretrained pose_landmarker_lite.task through detector/README.md.
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.evaluation \
  --manifest /tmp/urfall-check/manifest.json --model /path/pose_landmarker_lite.task \
  --output /tmp/legacy-evaluation.json --profile legacy
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.evaluation \
  --manifest /tmp/urfall-check/manifest.json --model /path/pose_landmarker_lite.task \
  --output /tmp/conservative-evaluation.json --profile conservative
```

The acquisition script uses direct clip paths; the archived run manifest used a `urfall/` subdirectory. Both preserve identical video hashes. Match directory layouts when replaying the archived manifest. No dataset download is implicit at application startup.

## PPE inference

`evaluation/ppe-smoke.json` records actual ONNX CPU inference on the existing normal-standing screenshot. The reference model loaded and ran; zero supported boxes exceeded the configured 0.5 threshold. This does not establish detection quality, person detection recall, PPE precision/recall, association accuracy, compliance accuracy or mAP. No labeled disjoint PPE evaluation was available. Do not advertise these as measured capabilities.

Model: [Hexmon/vyra-yolo-ppe-detection](https://huggingface.co/Hexmon/vyra-yolo-ppe-detection), publisher-described YOLOv8m. ONNX metadata confirmed 14 classes and [1,18,8400] output. Only Person, Hardhat and Safety Vest are used; image-level Fall-Detected is ignored. **License conflict:** model card declares CC BY 4.0 while ONNX embeds AGPL-3.0. Weights remain outside Git and must not be redistributed/deployed without resolving relevant obligations. See MODEL_REGISTRY.md.

PPE association/ambiguity, temporal smoothing and transport are unit/integration tested. Those tests use constructed boxes or test events and are NOT empirical model evaluation.

## Next evaluation requirements

A larger, separately acquired subject/camera-disjoint set; independently annotated onsets; explicit normal-resting/crouching/kneeling/occlusion cases; longer negative camera-hours; per-class PPE boxes and per-person relations; AP at declared IoUs; bootstrap confidence intervals grouped by video/subject; full end-to-end camera load testing. Keep raw predictions and model hashes. Never optimize thresholds on the final test set.

## Supplied PPE image benchmark interface

`python -m safetylens_detector.ppe_evaluation --manifest /path/labeled-images.json --model-manifest /path/ppe.json --output /tmp/ppe-results.json` consumes user-supplied images only. Each `images` row requires id, path, SHA-256, source, license, split, group, and a `boxes` list of canonical `label`/pixel `xyxy` objects. It checks duplicate content and group split leakage, then reports per-class precision/recall, 101-point AP50, AP50:95 and class support. Classes with no annotations produce null AP. No PPE images/labels are fabricated or bundled. Association/compliance accuracy remain null until independently annotated per-person relations/assessability are supplied; object AP cannot establish them. Mathematical AP unit tests are not empirical model evaluation.

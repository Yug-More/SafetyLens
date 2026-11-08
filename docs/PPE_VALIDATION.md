# PPE validation and deployment exclusion

## Current state

**Local PPE deployment is disabled in both camera configuration and the worker.** The camera form exposes a disabled control with the reason; the API rejects policies enabling the local detector with `PPE_DEPLOYMENT_DISABLED`. Historical configured/multimodal PPE reviews and camera requirements remain available. Offline evaluation stays available. This is enforced behavior, not just a model-card warning.

Sources: `save_camera` in [platform.py](../backend/app/api/routes/platform.py), [worker.py](../detector/src/safetylens_detector/worker.py), `test_local_ppe_deployment_is_explicitly_disabled` in [test_platform.py](../backend/tests/test_platform.py). No candidate below establishes a complete deployment-ready person/PPE system.

## Original reference and diagnosis

The prior Hexmon reference model ran through float32[1,3,640,640], RGB/255 letterbox, [1,18,8400] raw-head decode and per-class NMS. Actual metadata provides Person11/Hardhat3/Vest13. The previous24-image labeled diagnostic produced macro AP50:95 .003017 with person recall .0351, helmet recall .0357 and zero vest recall. This evidence remains in `evaluation/final/ppe-results.json`; the adapter's successful loading is not useful accuracy.

Its model card/embedded AGPL conflict remains unresolved. There is no demonstrated calibration, wearer relationship ground truth, or evidence that the model's training distribution matches target cameras. It is not re-enabled by this phase. No specific training-data defect is asserted without its training records.

## Publisher-declared Apache alternative inspected

[HammadNaseer/PPE](https://huggingface.co/HammadNaseer/PPE), pinned revision `0d20493e32a17fe9fbf9ee5a0772df25b7456256`, was downloaded and inspected outside Git. Although the card declares Apache2.0, ONNX metadata embeds AGPL and lists glove/helmet/pants/vest, with no person class; the card's described classes do not match that export. No related face-recognition components were downloaded or used. This is not a cleared full-system replacement. No accuracy number is invented for it.

## Official alternative actually evaluated

[Qualcomm PPE-Detection/GearGuardNet](https://huggingface.co/qualcomm/PPE-Detection) publishes BSD3-Clause licensing and a two-class export. The tagged [official implementation](https://github.com/qualcomm/ai-hub-models/tree/v0.65.0/src/qai_hub_models/models/gear_guard_net) and associated preprocessing were inspected. An offline-only adapter, [gear_guard.py](../detector/src/safetylens_detector/gear_guard.py), validates graph/external-data hashes and fixed float32[1,3,320,192] input. It uses centered black letterboxing, RGB/255 and the exported xyxy/scores/class-index heads, then per-class NMS. Both file hashes are recorded in `gear-guard-manifest.json`. Weights are not bundled.

Actual CPU evaluation reused the24 fixed labeled SH17 mirror images, not a successful-image selection. At score floor .05 and IoU .5: helmet5 predictions/28 annotations, zero matches; vest14 predictions/7 annotations, zero matches. Both precision/recall/AP50/AP50:95 are zero. Person is **unsupported**, not a functioning class with zero precision. The macro metric in generic output includes a zero-person slot; it must not be used to imply person capability. Raw predictions and per-image inference timings: `evaluation/hardening/ppe-qualcomm.json`.

The official protocol was inspected; a PyTorch numerical-parity run was not performed. These are results for this adapter/export/subset, not a universal claim about the architecture. The official publisher's license declaration is more useful provenance than the conflicting third-party cards, but it does not establish complete commercial clearance for training data, target use or this platform. The alternative lacks person inference and useful measured transfer here, so deployment remains excluded.

## What remains necessary

A license-reviewed model with useful person/helmet/vest performance on representative independent data; preprocessing/export parity checks; sufficiently small equipment boxes at actual camera distances; independently annotated wearer links and visible/occluded regions; temporal video evaluation; false-compliance/violation measurements and uncertainty. Existing geometric association abstains on ambiguous overlaps and treats missing equipment as unconfirmed. Constructed box tests do not measure wearer accuracy.

The external dataset's mirror declaration does not override upstream restrictions; see DETECTION_VALIDATION.md/MODEL_REGISTRY.md. New weights, image data, private credentials and model binaries remain outside Git. No PPE accuracy, certification or production deployment is claimed.

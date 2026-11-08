# External model manifests

Keep weights outside Git. `OnnxPpeDetector` requires a JSON manifest containing `weights` (relative path), `sha256`, `source`, `license`, `classes` (integer-string → canonical label), `number_of_classes`, and `input_size`.

The optional reference model investigated is [Hexmon/vyra-yolo-ppe-detection](https://huggingface.co/Hexmon/vyra-yolo-ppe-detection), whose publisher declares CC BY 4.0 and a YOLOv8m model. Supported mappings only: 3 → hard_hat, 11 → person, 13 → high_visibility_vest; 14 total classes, 640 input. Other output classes are deliberately ignored, including its image-level fall label. Review upstream model/data/base-model obligations before redistribution or deployment. Publisher claims are not SafetyLens evaluation results.

A model must load and pass inference smoke tests before it is labeled implemented; it remains experimental until a disjoint labeled evaluation is supplied. No model downloads happen implicitly at application startup.

## Observed license conflict

The downloaded ONNX metadata embeds AGPL-3.0, whereas the publisher model card declares CC BY 4.0. Neither declaration is silently treated as a resolved redistribution license. The file remains external and the integration experimental; see evaluation/ppe-smoke.json for the model hash and actual smoke result (zero boxes above threshold, no accuracy inference).

## Final validation decision

The reference model was subsequently evaluated on 24 real labeled SH17 mirror images. Macro AP50:95 .003017 with very low person/helmet recall and zero vest recall. It is **excluded from deployment**, not promoted on the basis of successful runtime loading. Upstream SH17 is CC-BY-NC-SA-4.0 despite the mirror's CC-BY declaration. Model-card versus embedded ONNX licensing remains unresolved. See DETECTION_VALIDATION.md and evaluation/final/ppe-results.json for the full negative findings; no independent wearer/compliance labels were available.

## Final hardening candidates

MediaPipe Pose Landmarker Lite remains the default; Full and opt-in four-pose Lite were compared with unchanged temporal thresholds. Full/tracked are experimental alternatives, not validated upgrades. Source/model hashes and per-camera outcomes are in `evaluation/hardening/` and DETECTION_VALIDATION.md. Track IDs are geometric and ephemeral.

Qualcomm GearGuardNet v0.65.0 was evaluated offline using its graph plus external data, fixed RGB input and publisher preprocessing/output contract. It supplies helmet/vest boxes, not person boxes. Publisher BSD-3 metadata does not constitute full commercial clearance. HammadNaseer/PPE had conflicting card versus embedded license metadata and no person class. Neither replaces the deployed detector; local PPE is disabled. See PPE_VALIDATION.md for exact provenance, performance and remaining qualification requirements.

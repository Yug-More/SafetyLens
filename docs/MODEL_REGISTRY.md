# External model manifests

Keep weights outside Git. `OnnxPpeDetector` requires a JSON manifest containing `weights` (relative path), `sha256`, `source`, `license`, `classes` (integer-string → canonical label), `number_of_classes`, and `input_size`.

The optional reference model investigated is [Hexmon/vyra-yolo-ppe-detection](https://huggingface.co/Hexmon/vyra-yolo-ppe-detection), whose publisher declares CC BY 4.0 and a YOLOv8m model. Supported mappings only: 3 → hard_hat, 11 → person, 13 → high_visibility_vest; 14 total classes, 640 input. Other output classes are deliberately ignored, including its image-level fall label. Review upstream model/data/base-model obligations before redistribution or deployment. Publisher claims are not SafetyLens evaluation results.

A model must load and pass inference smoke tests before it is labeled implemented; it remains experimental until a disjoint labeled evaluation is supplied. No model downloads happen implicitly at application startup.

## Observed license conflict

The downloaded ONNX metadata embeds AGPL-3.0, whereas the publisher model card declares CC BY 4.0. Neither declaration is silently treated as a resolved redistribution license. The file remains external and the integration experimental; see evaluation/ppe-smoke.json for the model hash and actual smoke result (zero boxes above threshold, no accuracy inference).

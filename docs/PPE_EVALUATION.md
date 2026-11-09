# PPE evaluation and corrected semantic provenance

## What was actually implemented

The official SH17 YOLOv8n checkpoint is exported to fixed float32 ONNX [1,3,640,640], raw [1,21,8400] output. `OnnxPpeDetector.detect` applies RGB/255, centered 114 letterboxing, embedded class indices, xywh decode, original-image coordinate restoration and class NMS. It now supports nine explicit appearance labels. `ppe_image.py` runs actual offline inference and produces per-person unknown-safe assessments/optional overlays. Weights are not shipped or downloaded at startup.

The official checkpoint/export are from [SH17 authors](https://github.com/ahmadmughees/SH17dataset), not a general commercially cleared model. Framework/export metadata is AGPL-3.0; source data is CC BY-NC-SA 4.0. Commercial redistribution/deployment is not cleared. Original publisher class YAML and checkpoint metadata agree; README list positions are not used as output indices. Exact hashes/versions/parity are retained in [export-parity.json](evaluation/research/export-parity.json) and [model manifest](evaluation/research/sh17-model-manifest.json).

One-image PyTorch/ONNX numeric parity passed the predeclared score-error ≤.001 and coordinate-error ≤.1 input-pixel gate: max score error .0000035763, coordinate error .0031128 pixels. This supports export equivalence for that tensor, not complete backend/quantization parity. Repeat exports include changing metadata and can change full-file hashes; final pinned export predictions were rerun and matched the earlier corrected run exactly.

## Critical correction to historical PPE results

The third-party SH17 mirror uses numeric category names after renumbering classes. Assuming name 10 still meant original class 10 was wrong. The recovered mapping corresponds to lexical ordering of original numeric labels, not their numeric order. For example mirror category3 is original helmet10; category9 is original vest16; category11 is original face3; category17 is original gloves9.

`scripts/verify_sh17_mapping.py` downloaded independent original publisher YOLO annotations through the publisher-linked Kaggle dataset, then matched them to mirror COCO rectangles by maximum per-coordinate error ≤2 pixels. **All 1,172 boxes across all 100 fixed images matched; zero unmatched boxes; every recovered category mapping was consistent.** Predictions were not consulted. [verified-label-mapping.json](evaluation/research/verified-label-mapping.json) preserves per-file source URLs/hashes, category pairs and support. No guessed semantic mapping is accepted by dataset preparation.

**Historical equipment metrics are withdrawn.** The old .003017 macro result and Qualcomm zero-vest-match claim were based on incorrect equipment semantics; historical predictions/files remain unchanged with correction notices. Person labels and fall metrics are unaffected. Corrected replay uses the same original 24 images and predictions with independently verified ground-truth names:

- Reference: person precision1/recall .0351, helmet precision .3889/recall .3684, vest precision .5385/recall .5833; AP50:95 .00792/.08678/.31944 respectively. Tiny person support remains inadequate despite corrected equipment results.
- Qualcomm: person unsupported, helmet zero matches, vest precision .1429/recall .1667/AP50 .1419. It is not a full person/PPE replacement.
- Official SH17 export on identical24: person precision .5904/recall .8596, helmet precision .8182/recall .4737, vest precision .5714/recall .6667. AP50:95 .57004/.21743/.36390. This is an in-domain diagnostic with unknown training overlap, not independent transfer accuracy.

See `evaluation/research/ppe24-corrected-*.json`. These corrections are not threshold tuning or a claim that numerical label names convey semantics.

## Fixed 100-image diagnostic

Pinned mirror revision `c979be777eaa1c6b5338410788b65926a033e3a0`, first100 filenames sorted before evaluation; all image and annotation hashes retained in [ppe100-manifest.json](evaluation/research/ppe100-manifest.json). Upstream noncommercial restrictions override the mirror's conflicting CC BY declaration. Images remain outside Git. Existing source/mirror images may overlap model training and contain correlated stock scenes; no held-out or independent generalization claim is made.

Score floor .05 and class NMS .45 were fixed. Precision/recall/F1 below are object detections at IoU .5; AP uses 101-point interpolation and greedy class matching over the retained score range. It is not COCO crowd/ignore evaluation, and AP below the score floor is unobserved. Small supports require caution.

- **person**: 236 ground-truth objects, 355 predictions, 193 matches; precision 0.5437, recall 0.8178, F1 0.6531, AP50 0.7846, AP50:95 0.5316.
- **earmuffs**: 5 ground-truth objects, 2 predictions, 1 matches; precision 0.5000, recall 0.2000, F1 0.2857, AP50 0.1040, AP50:95 0.0208.
- **face_shield**: 3 ground-truth objects, 11 predictions, 2 matches; precision 0.1818, recall 0.6667, F1 0.2857, AP50 0.4422, AP50:95 0.2766.
- **medical_mask**: 14 ground-truth objects, 13 predictions, 5 matches; precision 0.3846, recall 0.3571, F1 0.3704, AP50 0.3564, AP50:95 0.1754.
- **ordinary_eyewear**: 12 ground-truth objects, 21 predictions, 4 matches; precision 0.1905, recall 0.3333, F1 0.2424, AP50 0.3027, AP50:95 0.1522.
- **gloves**: 63 ground-truth objects, 97 predictions, 26 matches; precision 0.2680, recall 0.4127, F1 0.3250, AP50 0.3179, AP50:95 0.1867.
- **hard_hat**: 40 ground-truth objects, 29 predictions, 17 matches; precision 0.5862, recall 0.4250, F1 0.4928, AP50 0.3587, AP50:95 0.1903.
- **ordinary_footwear**: 99 ground-truth objects, 154 predictions, 50 matches; precision 0.3247, recall 0.5051, F1 0.3953, AP50 0.4046, AP50:95 0.2035.
- **high_visibility_vest**: 30 ground-truth objects, 67 predictions, 23 matches; precision 0.3433, recall 0.7667, F1 0.4742, AP50 0.6121, AP50:95 0.3329.

These appearance classes cover the eight target policy categories only through explicitly labeled evidence types. `ordinary_eyewear` is not verified safety goggles; `ordinary_footwear` does not establish safety-rated footwear; `medical_mask` is not validated respiratory protection. Gloves, earmuffs, face shields, hats and vests also lack equipment-rating and representative wearer validation. No protective-category accuracy is substituted for appearance AP.

## Person association, uncertainty and temporal controls

`compliance.assess_people` associates each appearance object with at most one person using head/torso/hand/foot regions. Ambiguous overlaps abstain; equipment seen on one worker is not shared across workers. These are geometric heuristics, not learned wearer identification. All required categories remain `unknown` under closed validation gates, with explicit appearance observations/reasons; absent policy categories are `not_required`. Human-confirmed incident review remains a separate authenticated workflow. No automatic function labels a person compliant from ordinary glasses or invisible boots.

Existing `PpeTemporalMonitor` can request evidence review after repeated missing visibility, but now retains `inconclusive` instead of converting repeated invisibility into noncompliance. Tests cover separate persons, ambiguity, missing footwear, appearance/rating distinction and persistent unknowns. Independent wearer/assessability/occlusion labels are absent: **association accuracy, compliance accuracy, unknown-rate quality, angle-specific compliance and false alerts per camera-hour are unmeasured**, not zero or inferred from object AP. No PPE video benchmark was conducted.

## Policy/API/UI and deployment gates

Eight categories are configurable per camera/zone. Conditional requirements use explicit activity, operational role and local minute ranges, including overnight ranges. Missing context remains pending/unknown; a known nonmatch does not accidentally activate a rule. This is operator-supplied operational context, not identity or activity inference.

`GET /api/ppe-capabilities` returns per-class status and labeled appearance metrics. Administrator `POST /api/cameras/{id}/ppe-context-preview` resolves stored rules without inference or authorization effects. Camera forms persist eight requirements and optional typed JSON context rules. The PPE page displays real server gates, errors/retry and a functional context preview. Historical seeded policy requirements are preserved and resolved correctly. API role/CSRF checks apply; viewer access does not grant configuration rights.

**All eight categories remain disabled for local deployment.** Offline model inference is available, but useful person-specific representative validation, protective-rating labels and licensing review remain unmet. Existing configured/demo and optional provider reviews remain labeled and independent. Model availability alone does not open a deployment gate.

New automated `ppe_noncompliance` detector ingestion is rejected while all visual gates are closed, even if a device bypasses the normal worker/configuration controls. Existing UUID acknowledgements remain retryable. Configured demos, human review and offline diagnostics are separate paths, not qualified live PPE deployment.

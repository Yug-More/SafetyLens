# Reproducibility — current research phase

Run from the repository root. Use Python 3.12 and Node 22+. Keep credentials, raw media, weights and caches outside Git. Read upstream noncommercial/AGPL obligations before acquiring research artifacts. This is not deployment clearance. No packages were added to repository dependency files in this phase; export tools were installed in a separate `/tmp` target.

## Application and test environments

```sh
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.lock.txt
python3.12 -m venv detector/.venv
detector/.venv/bin/python -m pip install -r detector/requirements-video.lock.txt
detector/.venv/bin/python -m pip install onnxruntime==1.31.1
npm --prefix frontend ci
backend/.venv/bin/python -m pytest -c backend/pytest.ini backend/tests -q
PYTHONPATH=detector/src backend/.venv/bin/python -m unittest discover -s detector/tests -q
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

Observed detector runtime: Python 3.12.12, NumPy1.26.4, OpenCV4.11.0, MediaPipe0.10.21, ONNX Runtime1.31.1. CPU host Apple M2 Pro,16 GiB, macOS14.5 arm64. Native MediaPipe required host graphics-context access even with CPU delegation. No GPU utilization was measured. Time/RSS results are single-host observations.

## Temporal learning: explicit split before inference

Use a new research directory. Acquisition retrieves camera0 files from the publisher and records hashes; frozen reference hashes/splits are under `docs/evaluation/research/urfall-manifest.json`. The 01–16/17–26/27+ recording split does not establish subject/session independence. This test set is now published and should not be reused as a future holdout.

```sh
mkdir -p /tmp/safetylens-reproduce/models
curl --fail --location https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task -o /tmp/safetylens-reproduce/models/pose.task
# Verify pose SHA256: 59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a
PYTHONPATH=detector/src detector/.venv/bin/python scripts/prepare_temporal_dataset.py --directory /tmp/safetylens-reproduce/urfall
PYTHONPATH=detector/src detector/.venv/bin/python scripts/temporal_experiment.py extract --manifest /tmp/safetylens-reproduce/urfall/manifest.json --pose-model /tmp/safetylens-reproduce/models/pose.task --splits train validation --output /tmp/safetylens-reproduce/train-validation.json
OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=detector/src detector/.venv/bin/python scripts/temporal_experiment.py train --cache /tmp/safetylens-reproduce/train-validation.json --output /tmp/safetylens-reproduce/temporal.json --report /tmp/safetylens-reproduce/selection.json
```

Freeze the resulting model hash/configuration before extracting test features. Seed42, 300 epochs, train-only normalization, balancing, candidate/threshold selection and loss curves are in code and the selection artifact. Same-host repeat training produced byte-identical weights. Different BLAS/platform behavior can change floating-point/file bytes; compare procedures and predictions, not a promised universal checkpoint hash.

```sh
PYTHONPATH=detector/src detector/.venv/bin/python scripts/temporal_experiment.py extract --manifest /tmp/safetylens-reproduce/urfall/manifest.json --pose-model /tmp/safetylens-reproduce/models/pose.task --splits test --output /tmp/safetylens-reproduce/test.json
MODEL_SHA256=$(python3 -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("/tmp/safetylens-reproduce/temporal.json").read_bytes()).hexdigest())')
PYTHONPATH=detector/src detector/.venv/bin/python scripts/temporal_experiment.py evaluate --cache /tmp/safetylens-reproduce/test.json --checkpoint /tmp/safetylens-reproduce/temporal.json --checkpoint-sha256 "$MODEL_SHA256" --output /tmp/safetylens-reproduce/results.json
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.temporal_video /tmp/safetylens-reproduce/urfall/fall-27-cam0.mp4 --pose-model /tmp/safetylens-reproduce/models/pose.task --checkpoint /tmp/safetylens-reproduce/temporal.json --checkpoint-sha256 "$MODEL_SHA256" --rgb-right-half --output /tmp/safetylens-reproduce/video-result.json
```

For live-worker experimentation, add `--temporal-checkpoint /path/temporal.json --temporal-sha256 "$MODEL_SHA256"` to the existing worker command. This is explicitly opt-in; poor fresh-test specificity prevents default promotion. Source loss/reidentification remains a limitation. Neither score nor pose quality is a calibrated fall probability.

## PPE: resolve semantics before evaluating

The pinned mirror's numeric names are not original class numbers. Original annotations are retrieved from the publisher-linked Kaggle dataset using URL-encoded file paths, bounded to1MB/file. Class semantics must be established before image acquisition/evaluation; predictions do not enter the mapping procedure.

```sh
mkdir -p /tmp/safetylens-reproduce/ppe
curl --fail --location https://huggingface.co/datasets/fathansanum/SH-17-Dataset/resolve/c979be777eaa1c6b5338410788b65926a033e3a0/SH17-dataset-1/test/_annotations.coco.json -o /tmp/safetylens-reproduce/ppe/annotations.json
detector/.venv/bin/python scripts/verify_sh17_mapping.py --annotations /tmp/safetylens-reproduce/ppe/annotations.json --count 100 --label-directory /tmp/safetylens-reproduce/ppe/original-labels --output /tmp/safetylens-reproduce/ppe/verified-mapping.json
detector/.venv/bin/python scripts/prepare_sh17_diagnostic.py --annotations /tmp/safetylens-reproduce/ppe/annotations.json --verified-mapping /tmp/safetylens-reproduce/ppe/verified-mapping.json --directory /tmp/safetylens-reproduce/ppe/images --count 100
```

Use a separate Python 3.12 export environment with `torch==2.6.0`, `torchvision==0.21.0`, `ultralytics==8.3.235`, `onnx==1.17.0`, `onnxruntime==1.31.1`, `numpy==1.26.4`, OpenCV4.11 and the package dependencies. `export_sh17.py` hash-checks the official checkpoint before loading it; do not load arbitrary PyTorch pickle files. Export tools are not needed for normal ONNX inference. The official checkpoint SHA256 is `5449f62bd7cf30c01c7fd138db2729a38abcb4d5120449773fba475d54f30b62`.

```sh
curl --fail --location https://github.com/ahmadmughees/SH17dataset/releases/download/v1/yolo8n.pt -o /tmp/safetylens-reproduce/ppe/yolo8n.pt
# Run with your isolated export Python, not the API environment:
python scripts/export_sh17.py --checkpoint /tmp/safetylens-reproduce/ppe/yolo8n.pt --sha256 5449f62bd7cf30c01c7fd138db2729a38abcb4d5120449773fba475d54f30b62 --image /tmp/safetylens-reproduce/ppe/images/construction-site-build-construction-work-159358_jpeg.rf.894f1abe324abfb7565fe8322034b549.jpg --report /tmp/safetylens-reproduce/ppe/export-parity.json
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.ppe_evaluation --manifest /tmp/safetylens-reproduce/ppe/images/manifest.json --model-manifest /tmp/safetylens-reproduce/ppe/sh17-model-manifest.json --output /tmp/safetylens-reproduce/ppe/results.json
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.ppe_image /tmp/safetylens-reproduce/ppe/images/construction-site-build-construction-work-159358_jpeg.rf.894f1abe324abfb7565fe8322034b549.jpg --model-manifest /tmp/safetylens-reproduce/ppe/sh17-model-manifest.json --required hard_hat high_visibility_vest protective_footwear --output /tmp/safetylens-reproduce/ppe/review.json
```

Full ONNX hashes can change with export metadata; the export receipt records actual bytes and metadata-independent graph hash. No quantization or GPU speedup was evaluated. All deployment gates remain closed.

## Real application verification and demo

Use [DEPLOYMENT_VERIFICATION.md](DEPLOYMENT_VERIFICATION.md) for generated secrets, administrator bootstrap and PostgreSQL 17 Compose. Never overwrite an existing environment or volume. The local profile is loopback HTTP; production HTTPS remains separately unverified. `MAX_REQUEST_SIZE_MB=110` counts bytes before multipart spooling; metadata bodies are limited to256 KiB. Choose a budget above the configured video limit plus multipart overhead.

```sh
SAFETYLENS_REAL_CLIP=/tmp/safetylens-reproduce/urfall/fall-07-cam0.mp4 SAFETYLENS_POSE_MODEL=/tmp/safetylens-reproduce/models/pose.task npm --prefix frontend run test:e2e
```

Default browser delivery without these variables is explicitly synthetic. To verify actual learned delivery through the Docker verifier, set `SAFETYLENS_TEMPORAL_CHECKPOINT` and `SAFETYLENS_TEMPORAL_SHA256` and pass fall27 to `scripts/verify_compose.py`. The verifier creates private QA records/dumps on a dedicated test installation; it is not an operational-site command. Four-replay/MJPEG probes are in `scripts/verify_camera_load.py`; they do not establish physical RTSP or sustained fleet capacity. See [DEMO_GUIDE.md](DEMO_GUIDE.md).

## Final clean-install and metrics-freeze procedure

`scripts/prepare_local_env.py --output PATH` creates private first-run secrets using exclusive creation and0600 permissions; it never overwrites an existing file. The concise root quick start uses a persistent user configuration directory. Keep encryption keys/backups secure and independent of test data.

`python3 scripts/verify_clean_install.py --project safetylens-validation-UNIQUE --env-file /private/path/local.env --output /tmp/clean-install.json` refuses existing project containers/volumes before running the documented PostgreSQL17 profile. It verifies all services healthy and zero default users. Build layers may be reused; fresh data volumes were actually exercised. Default host ports must be free; do not stop unrelated installations. CI runs this probe on an isolated runner and uploads only the non-secret receipt.

`python3 scripts/freeze_project_metrics.py --check` verifies model/decision source and experiment artifact hashes plus the generated metrics document. `--write` is an explicit new freeze, only after review/verification; no inference or training happens during `--check`. A merge/documentation commit can change Git HEAD without changing the bound scientific source. The tested source revision and evidence remain traceable in the ledger.

Runtime/evaluation parity on the published test uses `scripts/verify_temporal_parity.py`; it loads the same checkpoint/cache/manifest/pose model, runs actual video inference and compares every event timestamp. No retraining or new accuracy claim is implied. Final test/source/clean-install/advisory artifacts are in `docs/evaluation/finalization/`.

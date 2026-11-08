# SafetyLens

**Computer vision evidence. Human-supervised response.**

SafetyLens connects local camera observations, preserved incident evidence, optional multimodal investigation, company procedures, explicit human approval, and traceable simulated response. It is an experimental applied-AI platform, not a certified safety or medical system.

The original hackathon implementation and contributor history are preserved. Team members reported first place at The Executable World Hackathon; competition recognition does not validate detector performance. See [historical project documentation](docs/HISTORICAL_README.md) and [historical baseline](docs/HISTORICAL_BASELINE.md).

## Enhanced platform

- Local MediaPipe pose estimation and temporal event logic, with a preserved legacy profile and conservative fall/person-down interpretation.
- Optional real ONNX person/hard-hat/vest inference, exclusive association, ambiguity handling and temporal review. **Experimental: no labeled PPE accuracy established; reference model license metadata conflicts.**
- Automatic authenticated detector delivery through a bounded persistent SQLite outbox, retry/backoff and UUID acknowledgement/deduplication.
- Camera registration/editing, facility/zone grouping labels, encrypted private sources, per-camera policies, heartbeat health and labeled latest-image previews.
- Secure-by-default local users, scrypt passwords, revocable sessions, CSRF/Origin checks and administrator/manager/operator/viewer roles.
- Operations overview, camera operations, searchable/paginated incident history, PPE review, data-backed analytics and versioned operator notes.
- Resumable database-backed SSE updates; explicit unavailable/empty states instead of silent mock success.
- Evidence-frame/clip investigation, optional OpenAI image-and-text analysis, lexical SOP retrieval and exact citation snapshots.
- Separate incident confirmation and selected-action approval; retry authorization checks; simulated-only execution; audited PDF/CSV reporting.
- H.264 playback derivatives preserve original evidence. Scoped retention can expire resolved media while keeping metadata/audit history.
- Additive Alembic migration, optional PostgreSQL Compose path, non-root containers, locked dependencies, CI and browser workflow tests.

## Actual detection evidence

A prespecified external check on **12 UR Fall camera-0 clips** found **2/6 falls detected** in both profiles. Legacy produced **1/6 negative-video alerts**; conservative produced **0/6**. This is a small video-presence check with unknown subject identities and no onset labels, not industrial validation. Low recall is an unresolved limitation. No thresholds were tuned on these test clips.

Raw predictions, parameters, model/data hashes, processing timings and confidence intervals are in [DETECTION_EVALUATION.md](docs/DETECTION_EVALUATION.md). No accuracy, response-time reduction, uptime or adoption number is invented. Scripted demo confidence and historical dashboard values are not empirical metrics.

## Architecture

Camera → local pose/optional PPE inference → temporal event → pre/post evidence → durable device outbox → authenticated FastAPI ingestion → local-CV analysis/incident → notification → evidence review → stored SOP retrieval → cited response draft → human confirmation/approval → simulated actions → audit/report.

Uploaded video can instead use explicitly scripted Demo AI or configured OpenAI image/text analysis. Real detector imports are not silently passed through scripted analysis. Planning currently uses deterministic policy templates, including the historical OpenAI compatibility setting; no external LLM planning call is implied.

Frontend: Next.js/React/TypeScript/Tailwind/Base UI/shadcn components. Backend: FastAPI/Pydantic/SQLAlchemy/SQLite. Optional PostgreSQL path. Vision: OpenCV, MediaPipe, ONNX Runtime. Infrastructure: Docker Compose, Alembic, pytest/unittest/Playwright. See [architecture](docs/ARCHITECTURE.md).

## Local setup

Use Python 3.12 and Node 22+. Keep existing private environment files unchanged.

```sh
python3.12 -m venv backend/.venv
uv pip sync --python backend/.venv/bin/python backend/requirements.lock.txt
cd backend
# Create .env from .env.example only on first setup.
.venv/bin/python -m alembic -c alembic.ini upgrade head
.venv/bin/python -m app.seed.run  # Optional historical demo data
.venv/bin/python -m app.manage create-user --username YOUR_USERNAME
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal: `cd frontend && npm ci && npm run dev`. Open [localhost:3000](http://localhost:3000). There is no default password. API/frontend origins and hostnames must match the configured allowed origins for cookie authentication.

## Cameras and live detection

Register a camera in Cameras & Zones, configure private server-side encryption/device credentials, and follow [CAMERA_PIPELINE.md](docs/CAMERA_PIPELINE.md). Run the detector in its separate environment using `detector/requirements-video.lock.txt`. Download model weights explicitly; no model is bundled or downloaded at startup. CPU pose inference was tested on the Mac host, but still required an OS graphics context.

```sh
PYTHONPATH=detector/src detector/.venv/bin/python -m safetylens_detector.worker \
  --backend http://127.0.0.1:8000 --camera-ids CAMERA_UUID \
  --pose-model /path/pose_landmarker_lite.task
```

Supply DETECTOR_API_TOKEN privately in the worker environment and scope it with server DETECTOR_CAMERA_IDS. Remote delivery requires HTTPS. Camera previews are labeled snapshots/replays, not a claimed high-FPS live-video gateway. Original webcam preview commands remain in [detector/README.md](detector/README.md).

## Verification

```sh
backend/.venv/bin/python -m pytest -c backend/pytest.ini backend/tests -q
PYTHONPATH=detector/src backend/.venv/bin/python -m unittest discover -s detector/tests -v
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Browser tests generate isolated credentials/databases, exercise actual playback, and complete a synthetic event's transport/review/approval/PDF workflow without sending external messages. Synthetic integration fixtures are not detection-evaluation data. [TESTING.md](docs/TESTING.md) and [RELEASE_VERIFICATION.md](docs/RELEASE_VERIFICATION.md) record actual results and unfinished work.

## Deployment and safeguards

`docker compose up --build` is the local HTTP profile; bootstrap an administrator interactively. See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for production flags and the optional PostgreSQL path. Docker/PostgreSQL runtime was not verified here because the daemon was unavailable.

Never place secrets in NEXT_PUBLIC variables or Git. Evidence/report access is authenticated; private camera sources are encrypted. Retention runs are explicit and scoped. No facial recognition, identity inference or employee productivity scoring. All consequential action execution remains simulated; no emergency services, messaging platform or physical equipment is contacted.

## Limitations and future work

Low measured recall; no disjoint PPE benchmark; unresolved reference-model license; single-pose tracking; no production camera-fleet benchmark; no browser video gateway/overlay transport; no tenant isolation or face blurring; no external dispatch; no certified audit ledger. These are research/engineering tasks, not hidden capabilities. See [SECURITY.md](docs/SECURITY.md), [MODEL_REGISTRY.md](docs/MODEL_REGISTRY.md), [platform audit](docs/PLATFORM_AUDIT.md) and [changelog](docs/CHANGELOG.md).

## Team and historical work

- Yug More — backend, primary application workflows and integration (historical team plan).
- Sean Aminov — original pose/video detector, temporal algorithm and detector evidence work.
- Abhinav GS — original demo support, guide and manual QA.

Enhancement commits preserve existing authorship and do not reattribute earlier contributions. Original screenshots remain under `docs/assets/demo/`; original screens remain under `/demo`, `/demo/incidents`, `/demo/settings`.

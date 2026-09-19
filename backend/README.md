# SafetyLens Backend (Stage 4)

FastAPI service providing typed REST contracts, SQLite persistence, seeded demo data, video processing, and multimodal incident analysis on extracted frames.

## Requirements

- Python 3.11+
- pip
- Virtual environment support

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Environment

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | API display name | `SafetyLens API` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `API_HOST` | Bind host | `127.0.0.1` |
| `API_PORT` | Bind port | `8000` |
| `DATABASE_URL` | SQLAlchemy URL | `sqlite:///./safetylens.db` |
| `FRONTEND_ORIGINS` | Comma-separated CORS origins | `http://localhost:3000` |
| `DEMO_MODE` | Marks responses as demo | `true` |
| `UPLOAD_DIRECTORY` | Stored upload directory | `./data/uploads` |
| `FRAME_DIRECTORY` | Extracted frame directory | `./data/frames` |
| `MAX_VIDEO_SIZE_MB` | Upload size limit | `100` |
| `MAX_VIDEO_DURATION_SECONDS` | Max clip duration | `120` |
| `FRAME_SAMPLE_COUNT` | Representative frames to sample | `10` |
| `AI_PROVIDER` | `demo` or `openai` | `demo` |
| `AI_DEMO_MODE` | Labels demo-oriented behavior | `true` |
| `OPENAI_API_KEY` | Required only for `openai` | empty |
| `VISION_MODEL` | Required only for `openai` | empty |
| `AI_REQUEST_TIMEOUT_SECONDS` | Provider timeout | `45` |
| `AI_MAX_RETRIES` | Provider retries | `2` |
| `AI_MAX_FRAMES` | Max frames sent to a provider | `8` |
| `AI_MAX_IMAGE_DIMENSION` | Max encode dimension | `1280` |

Do not commit `.env`. Keep `.env.example` tracked. Never put API keys in the repository.

Default `AI_PROVIDER=demo` runs deterministic local analysis with no credentials. Set `AI_PROVIDER=openai` plus `OPENAI_API_KEY` and `VISION_MODEL` only when intentionally using a real provider.

## Storage

Runtime directories are created automatically:

- `data/uploads/` — UUID-named uploaded videos
- `data/frames/` — JPEG evidence-candidate frames

These directories are gitignored. See `data/README.md` for local demo-source guidance.

Supported formats: **MP4, MOV, WebM**.

Prefer short clips (10–30 seconds) for demos.

## Database initialization and seeding

Tables are created automatically on API startup (including Stage 4 analysis tables). Seed Stage 2 demo data with:

```bash
python -m app.seed.run
```

The seed command is idempotent.

## Video-processing and analysis workflow

1. Client uploads multipart video + location (+ optional camera_id)
2. Backend stores the file, extracts metadata, and samples frames
3. When the video is `ready`, client calls `POST /api/videos/{asset_code}/analyze`
4. Background job selects up to `AI_MAX_FRAMES` frames and runs the configured provider
5. Structured results, evidence (frame codes + timestamps), and a pending review are stored
6. Client polls `GET /api/analyses/{analysis_code}` and may submit human review

Demo AI is explicitly labeled simulated. Real providers are labeled separately. Detector pose/heuristic scores are never treated as fall probability.

## Start the server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs:

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Tests

Tests use an isolated in-memory SQLite database and temporary media directories. They never modify development uploads or `safetylens.db`. External AI providers are mocked — no paid API calls.

```bash
pytest
```

## Key endpoints

### Stage 2

- `GET /api/health`
- `GET /api/dashboard/summary`
- `GET /api/dashboard/activity`
- `GET /api/cameras`
- `GET /api/cameras/{camera_id}`
- `GET /api/incidents`
- `GET /api/incidents/{incident_identifier}`
- `GET /api/procedures`
- `GET /api/procedures/{procedure_identifier}`
- `GET /api/system/status`
- `GET /api/demo/info`

### Stage 3

- `POST /api/videos/upload`
- `GET /api/videos`
- `GET /api/videos/{video_identifier}`
- `GET /api/videos/{video_identifier}/frames`
- `GET /api/videos/{video_identifier}/content`
- `GET /api/processing-jobs/{job_identifier}`
- `GET /api/frames/{frame_identifier}/content`

### Stage 4

- `GET /api/ai/provider`
- `POST /api/videos/{video_identifier}/analyze`
- `GET /api/videos/{video_identifier}/analyses`
- `GET /api/analyses/{analysis_identifier}`
- `POST /api/analyses/{analysis_identifier}/review`

## Troubleshooting OpenCV on macOS

- Use `opencv-python-headless` from `requirements.txt`
- If VideoWriter tests fail, confirm codec `mp4v` is available
- If uploads fail with `UNREADABLE_VIDEO`, verify the file opens in QuickTime/VLC
- Reinstall with `pip install --force-reinstall opencv-python-headless`

## Stage 4 limitations

- No SOP retrieval from analysis (Stage 5)
- No approval execution / notifications / PDF reports (Stage 6)
- No authentication
- No deletion endpoints
- No distributed job queue (in-process BackgroundTasks only)
- Live detector integration uses the existing upload + analyze contract when Sean’s clips are ready

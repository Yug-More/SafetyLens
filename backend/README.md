# SafetyLens Backend (Stage 3)

FastAPI service providing typed REST contracts, SQLite persistence, seeded demo data, and a video processing pipeline that prepares evidence frames for Stage 4 multimodal AI.

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

Do not commit `.env`. Keep `.env.example` tracked.

## Storage

Runtime directories are created automatically:

- `data/uploads/` — UUID-named uploaded videos
- `data/frames/` — JPEG evidence-candidate frames

These directories are gitignored. See `data/README.md` for local demo-source guidance.

Supported formats: **MP4, MOV, WebM**.

Prefer short clips (10–30 seconds) for demos.

## Database initialization and seeding

Tables are created automatically on API startup. Seed Stage 2 demo data with:

```bash
python -m app.seed.run
```

The seed command is idempotent.

## Video-processing workflow

1. Client uploads multipart video + location (+ optional camera_id)
2. Backend streams the file to disk with size enforcement
3. Extension, MIME type, and OpenCV decode checks run
4. Video + queued processing job records are created
5. Background task extracts metadata and samples frames
6. Job progress updates through validation → metadata → sampling → ready
7. Frontend polls the job and displays video + frame timeline

Stage 3 does **not** classify incidents or run multimodal AI.

## Start the server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs:

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Tests

Tests use an isolated in-memory SQLite database and temporary media directories. They never modify development uploads or `safetylens.db`.

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

Video content is served with `FileResponse`. Explicit HTTP Range support is not implemented in Stage 3; short demo clips still play in modern browsers.

## Troubleshooting OpenCV on macOS

- Use `opencv-python-headless` from `requirements.txt`
- If VideoWriter tests fail, confirm codec `mp4v` is available
- If uploads fail with `UNREADABLE_VIDEO`, verify the file opens in QuickTime/VLC
- Reinstall with `pip install --force-reinstall opencv-python-headless`

## Stage 3 limitations

- No multimodal AI / fall classification
- No SOP retrieval from uploaded video content
- No real notifications or action execution
- No authentication
- No deletion endpoints
- No distributed job queue (in-process BackgroundTasks only)

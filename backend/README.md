# SafetyLens Backend (Stage 2)

FastAPI service providing typed REST contracts, SQLite persistence, and seeded demo data for the SafetyLens operations console.

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

Do not commit `.env`. Keep `.env.example` tracked.

## Database initialization and seeding

Tables are created automatically on API startup. Seed demo data with:

```bash
python -m app.seed.run
```

The seed command is idempotent. Running it twice does not duplicate cameras, incidents, procedures, activity, or services.

## Start the server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Interactive docs:

- Swagger UI: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

## Tests

Tests use an isolated in-memory SQLite database and never modify `safetylens.db`.

```bash
pytest
```

## Demo mode

When `DEMO_MODE=true`:

- Seeded Redwood Distribution Center data is available
- Live monitoring, AI verification, and notifications are simulated
- No real alerts or emergency-service contact occurs

## Key endpoints

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

## Stage 2 limitations

- No video processing
- No multimodal AI
- No embeddings / retrieval pipeline
- No real notifications
- No approval execution
- No report generation
- No authentication

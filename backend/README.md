# SafetyLens Backend

FastAPI service for video processing, incident analysis, procedure retrieval, human approval, simulated execution, audit/PDF reports, detector event ingestion, and camera-specific PPE policies.

## Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed.run
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Startup creates missing tables and applies the supported additive SQLite column updates. Preserve and back up existing databases before schema changes; arbitrary schema changes require a reviewed migration. The confirmed demo reset below is available when you intentionally want to discard demo runtime data.

## Detector ingestion

Accepts version 1 detector event JSON and an evidence clip, then maps them into the upload → prepare → analyze pipeline. The local camera runner saves these files but does not automatically submit them; import them through the dashboard or this API.

| Endpoint | Purpose |
|---|---|
| `POST /api/detector/events` | Ingest event JSON + clip (`multipart`) |
| `GET /api/detector/events` | List recent handoffs |
| `GET /api/detector/events/{event_id}` | Read mapping / status |
| `POST /api/detector/events/{event_id}/retry` | Safe retry after failure |
| `POST /api/demo/reset` | Confirmed demo-state reset (`DEMO_MODE` only) |

### Contract rules

- `schema_version` must be `1.0`
- `event_id` is unique; duplicates reuse the existing asset/job/analysis mapping
- `source_id` is a detector label; `camera_id` must be a real Camera PK (e.g. `cam-04`) when provided
- `pose_quality` is landmark reliability — never copied into AI confidence
- `heuristic_score` is not calibrated probability
- Absolute detector workstation paths are never returned by the API
- Clip paths (when not uploaded) must resolve under `DETECTOR_EVENTS_DIRECTORY`

### Event-centered sampling

When a video is linked to a detector event with `clip_event_offset_seconds`, frame extraction and analysis frame selection bias samples around that offset while preserving pre/post context and ordinary upload behavior.

## Demo reset

Requires `confirmed=true` and `DEMO_MODE=true`. Deletes runtime videos/analyses/plans/executions/reports/detector mappings and files under configured upload/frame/report directories only, then re-seeds cameras/incidents/procedures.

## Providers and PPE policies

The default `AI_PROVIDER=demo` returns deterministic rehearsal results. Configure `AI_PROVIDER=openai`, `OPENAI_API_KEY`, and `VISION_MODEL` for frame-based model analysis. Planning is configured separately through `PLANNER_PROVIDER` and `PLANNER_MODEL`.

`GET /api/ppe-policies` lists active camera policies; `GET /api/cameras/{camera_id}/ppe-policy` returns a camera's requirements. The configured PPE demo and provider analysis share the human-review workflow. They do not add PPE inference to the local fall detector.

## Tests

```bash
pytest
```

No paid providers or real workplace side effects.

## Docker

From repo root:

```bash
docker compose up --build
```

## Limitations

- Simulated actions only
- Prototype auth
- Application-level audit append-only
- Detector MediaPipe extras are optional and platform-dependent (see `detector/README.md`)

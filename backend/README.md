# SafetyLens Backend (Stage 7)

FastAPI service covering Stages 1–7: video pipeline, multimodal analysis, procedure retrieval, human approval, simulated execution, audit/PDF reports, detector event handoff, and safe demo reset.

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

After schema changes, delete `safetylens.db` and re-seed.

## Stage 7 detector ingestion

Accepts Sean’s version 1 event JSON (+ evidence clip) and maps into the existing Stage 3 upload → prepare → Stage 4 analyze pipeline.

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

# SafetyLens Backend (Stage 6)

FastAPI service with typed REST contracts, SQLite persistence, video processing, multimodal analysis, procedure retrieval, grounded response planning, human approval, simulated action execution, append-only audit events, and PDF incident reports.

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

If upgrading an existing local SQLite file after Stage 6 schema changes, delete `safetylens.db` and re-seed (tests always use a fresh in-memory DB).

## Stage 6 environment

| Variable | Description | Default |
|---|---|---|
| `PROCEDURE_DIRECTORY` | Stored procedure originals | `./data/procedures` |
| `REPORT_DIRECTORY` | Generated PDF reports (gitignored) | `./data/reports` |
| `MAX_PROCEDURE_SIZE_MB` | Upload size limit | `10` |
| `PLANNER_PROVIDER` | `demo` or `openai` | `demo` |
| `PLANNER_MODEL` | Optional real planner model | empty |

Never commit `.env`, uploaded media, generated reports, or databases.

## Approval workflow

1. Only `completed` grounded response plans can be reviewed.
2. `insufficient_policy` and `failed` plans cannot be approved or executed.
3. `POST .../approve` requires `confirmed=true`, selected action IDs from that plan, reviewer name, optional notes.
4. Partial approval selects a subset of actions; rejection stores an optional reason.
5. Double approval and approval after execution starts are rejected (`409`).
6. Demo identity defaults to `demo-reviewer`. Production auth/RBAC is **not** implemented.

## Simulated executor

`SimulatedActionExecutor` runs only explicitly approved actions. Results always set `simulation=true` and use safe wording such as “Simulated medical-assistance request created for demonstration.”

Supported simulated action types include supervisor alert, medical assistance request, incident ticket, evidence preservation, area-isolation recommendation, and follow-up scheduling.

**No real** Slack, email, SMS, emergency services, or ticketing integrations are called.

### Idempotency

Each approved action gets a stable `idempotency_key` scoped to the approval + action. Repeated `POST .../execute` returns existing executions without creating duplicate simulated notifications or tickets. Successful actions are never re-run as new work; failed actions may be retried via `POST /api/executions/{id}/retry`.

## Audit events

`AuditEvent` rows are append-only through application APIs (no update/delete endpoints). Events cover analysis/plan lifecycle, approval, execution start/success/failure, retries, and report generation/download where practical.

This is an **application-level append-only prototype** on SQLite — not a legally immutable compliance ledger.

## Incident reports

After analysis, planning, and (typically) simulated execution:

- `POST /api/incidents/{id}/reports` persists report metadata and generates a PDF with reportlab
- Incomplete reports are explicitly labeled
- Regeneration is allowed when underlying execution state changes (`force_regenerate`)
- Download: `GET /api/reports/{id}/download` returns valid PDF bytes
- Filenames are sanitized; absolute storage paths are never exposed

## Stage 6 API

- `POST /api/response-plans/{id}/approve`
- `POST /api/response-plans/{id}/reject`
- `GET /api/response-plans/{id}/approval`
- `POST /api/response-plans/{id}/execute`
- `GET /api/response-plans/{id}/executions`
- `POST /api/executions/{id}/retry`
- `GET /api/incidents/{id}/audit`
- `POST /api/incidents/{id}/reports`
- `GET /api/incidents/{id}/reports`
- `GET /api/reports/{id}`
- `GET /api/reports/{id}/download`

Plus all Stage 1–5 endpoints.

### Example: approve and execute

```bash
curl -X POST http://127.0.0.1:8000/api/response-plans/PLAN-.../approve \
  -H 'Content-Type: application/json' \
  -d '{"selected_action_ids":["..."],"confirmed":true,"reviewer_name":"demo-reviewer","incident_identifier":"INC-2026-0042"}'

curl -X POST http://127.0.0.1:8000/api/response-plans/PLAN-.../execute \
  -H 'Content-Type: application/json' \
  -d '{"confirmed":true}'
```

## Tests

```bash
pytest
```

External AI/planner/action providers are mocked or simulated — no paid or real workplace calls.

## Limitations

- Actions are simulated only
- Authentication/authorization remain prototype limitations
- Audit immutability is application-level only
- No real emergency or workplace systems are contacted
- No live detector adapter automation (Sean’s track)
- Stage 7 is not started

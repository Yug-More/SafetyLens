# SafetyLens Backend (Stage 5)

FastAPI service with typed REST contracts, SQLite persistence, video processing, multimodal analysis, procedure ingestion, lexical retrieval, verified citations, and grounded response planning.

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

If upgrading an existing local SQLite file after Stage 5 schema changes, delete `safetylens.db` and re-seed (tests always use a fresh in-memory DB).

## Stage 5 environment

| Variable | Description | Default |
|---|---|---|
| `PROCEDURE_DIRECTORY` | Stored procedure originals | `./data/procedures` |
| `MAX_PROCEDURE_SIZE_MB` | Upload size limit | `10` |
| `MAX_PROCEDURE_TEXT_CHARS` | Extracted text cap | `200000` |
| `PROCEDURE_CHUNK_MAX_CHARS` | Chunk size target | `900` |
| `RETRIEVAL_TOP_K` | Max ranked chunks | `8` |
| `RETRIEVAL_MIN_SCORE` | Minimum lexical score | `0.08` |
| `PLANNER_PROVIDER` | `demo` or `openai` | `demo` |
| `PLANNER_MODEL` | Optional real planner model | empty |

Never commit `.env`, uploaded procedures, or databases.

## Procedure ingestion

Supported: **PDF, TXT, Markdown**. Validates extension/MIME, size, path traversal, empty/corrupt documents. Extracts text (pypdf for PDF), chunks deterministically by headings/numbered steps/length, stores metadata without absolute paths. Duplicate code or identical content hash is rejected.

Seeded sample: **SOP-FALL-4.2** — Worker Fall and Person-Down Response (sample company procedure, not legal advice).

## Retrieval

Deterministic **lexical** scoring over active procedure chunks (keyword + domain weights). No paid API required. Every returned match includes procedure/chunk identifiers, section/page when present, exact excerpt, score, and method=`lexical`.

## Citations

Plans only persist citations that:

1. Exist as stored `ProcedureChunk` rows
2. Were present in the retrieval match set for that analysis
3. Snapshot the exact stored chunk text

Unknown or mismatched citation IDs are rejected (`INVALID_CITATION`).

## Response plans

Demo planner maps fall analyses + retrieved SOP-FALL chunks to ordered recommendations (supervisor, medical, area control, evidence, documentation). Status may be `completed`, `insufficient_policy`, or `failed`. Recommendations are never executed in Stage 5.

## Stage 5 API

- `POST /api/procedures/upload`
- `GET /api/procedures`
- `GET /api/procedures/{id}`
- `GET /api/procedures/{id}/chunks`
- `POST /api/analyses/{id}/retrieve-procedures`
- `POST /api/analyses/{id}/response-plan`
- `GET /api/response-plans/{id}`

Plus all Stage 1–4 endpoints.

## Tests

```bash
pytest
```

External AI/planner providers are mocked — no paid calls.

## Limitations

- No approval/execution/notifications (Stage 6)
- No PDF incident reports (Stage 6)
- No live detector adapter automation
- No authentication / RBAC

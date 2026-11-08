# Platform audit — 2026-11-07

## Baseline

Commit `178f0f8a77f2f6c664822fe6ef09f62ff6342f15`. Fresh clone of the existing remote after the old workspace was removed; a source-only Desktop copy was left untouched. Source inventory with hashes is in `baseline-source-inventory.json`. Prior detailed admissions audit inspected this same commit.

- Detector: 44 unittest tests pass, Python 3.13; synthetic landmarks and mocked capture, not accuracy validation.
- Backend: 68 pytest tests pass, isolated Python 3.12.12.
- Frontend: baseline validation recorded in TESTING.md after completion. npm ci reports dependency advisories; no forced upgrade.

## Architecture and actual capabilities

Next/React/TypeScript client → FastAPI service layer → SQLAlchemy/SQLite. Uploaded evidence is decoded with OpenCV and sampled into JPEGs. Local MediaPipe VIDEO-mode single-pose tracking supplies a timestamp-driven heuristic fall state machine and pre/post buffer. Backend demo analysis is scripted; optional OpenAI image/text calls are real integrations but not independently evaluated. Lexical SOP ranking and deterministic templates produce cited drafts. Incident confirmation and selected-action approval gate a simulated executor. ReportLab produces reports.

## Defects and risks

No baseline login/RBAC; caller-controlled reviewer identity; unprotected media. Retry omits current confirmation gate. Report reuse can retain stale retry results. Explicit report plan can belong to another incident. Policy keyword matching falls back to unrelated text. OpenAI planner labels deterministic output as real generation. Detector event imports default to a seeded incident/camera; no automatic transport. Dashboard response time/health contain constants. Temporal stationary-person-down path cannot establish a falling motion. Model outputs are incompletely constrained. Camera metadata/monitor placeholders do not implement camera lifecycle. No durable task queue, frontend E2E suite, database migrations, or independent held-out evaluation. Demo reset deletes audit rows. SQLite count-based codes can race.

## Prioritized implementation

1. Preserve history and executable legacy behavior; document evidence boundaries.
2. Add conservative temporal classification, PPE inference adapter/association and benchmark tools; require weights/data provenance and avoid fabricated results.
3. Add persistent bounded detector outbox, authenticated acknowledgement, correct camera/incident mapping.
4. Harden confirmation/retry, citations, reports, output validation, storage, metrics.
5. Add authenticated operator console, camera configuration/health, data-backed analytics and event updates.
6. Add additive migrations, deployment profiles, regression/E2E tests, CI, reproducible dependency/evaluation records.

## Boundaries

No certified safety or medical system. Multi-person pose identities, model/data acquisition and visual testing depend on actual available tools/resources. Remaining gaps must stay explicit in final release notes.

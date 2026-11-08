# Enhancement changelog

## November 7, 2026 — feature/safetylens-platform-enhancement

### Preserved

Original temporal algorithm, demonstration screenshots, tests, providers and historical team documentation. Original overview/incidents/settings UI retained under `/demo`, `/demo/incidents`, `/demo/settings`. Baseline source hashes are recorded. Historical Git commits and contributor attribution are unchanged.

### Added

- Additive users, revocable opaque sessions, scrypt, CSRF/Origin checks, role-based routes, device token/camera scope, login throttling, encrypted private camera sources.
- Camera registration/edit/deletion guards, grouping labels, policy settings, latest snapshot preview and heartbeat health; separately runnable bounded multi-camera worker.
- Conservative event interpretation, experimental ONNX PPE inference, exclusive spatial association, ambiguity handling and temporal review.
- Durable bounded SQLite outbox, retry/backoff/acknowledgement and automatic detector-to-incident flow that avoids scripted analysis.
- Database-backed resumable SSE invalidation, data-backed operations/analytics/PPE pages, paginated/date-filtered history, evidence-linked investigation and versioned operator notes/assignment API.
- Scoped evidence-expiration preview/application, preserving metadata and audit history; CSV export auditing/formula escaping.
- Alembic adoption migration, optional PostgreSQL Compose path, non-root containers, dependency locks, CI and browser tests.
- External 12-clip evaluation with raw output and honest low-recall findings. Actual ONNX inference smoke test without invented PPE metrics.

### Fixed

Retry confirmation/approval revalidation; cross-incident report/plan associations; report invalidation after changed retry outcomes; arbitrary policy fallback; misrepresented planner provenance; review audit gaps; procedure upload buffering bound; detector clip size bound; finite event timestamps; caller-supplied reviewer spoofing in authenticated mode; concurrent count-based generated identifiers; missing explicit form submission; viewer logout; duplicate page headings and persisted notes labeling.

### Remaining

Low fall recall, no labeled disjoint PPE accuracy/AP/association benchmark, uncertain model licensing, incomplete multi-person pose tracking, no high-FPS browser video gateway/box overlays, no independent facility entity/floor plan, no organization tenancy, no face blurring, no external action integrations, no current Docker/PostgreSQL runtime verification. See DETECTION_EVALUATION.md, SECURITY.md and RELEASE_VERIFICATION.md for measured evidence and limits.

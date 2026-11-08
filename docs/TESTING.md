# Testing and reproducibility

## Baseline (before implementation)

Commit `178f0f8a77f2f6c664822fe6ef09f62ff6342f15`, restored from the existing remote. Python detector standard-library suite: 44 passed. Backend isolated Python 3.12.12: 68 passed in 7.74 seconds. Frontend `npm ci` completed; lint passed. Clean-checkout typecheck failed because LayoutProps had not been generated. Baseline build failed fetching Google fonts. No baseline industrial accuracy was implied.

## Automated verification

From the root:

```sh
backend/.venv/bin/python -m pytest -c backend/pytest.ini backend/tests -q
PYTHONPATH=detector/src backend/.venv/bin/python -m unittest discover -s detector/tests -v
npm --prefix frontend run lint
npm --prefix frontend run typecheck
npm --prefix frontend run build
npm --prefix frontend run test:e2e
```

Backend pytest adds authenticated session/CSRF/role/logout/expiry/rate-limit tests, camera encryption/lifecycle checks, scoped device delivery and local-CV provenance, stale-update protection, retry revocation, report refresh, retention, and migration adoption/repeatability. Existing 68 tests are preserved. The historical fixtures explicitly select insecure local demo mode; new security tests enable authentication and verify denied access. No tests are disabled to manufacture a pass.

Detector tests cover the original state machine plus durable outbox restart/ack/backoff/capacity/permanent failures, exclusive PPE association, ambiguous crowds, time persistence, uncertainty and confidence-interval edge cases. Box/transport tests are constructed behavioral tests, not detection accuracy measurements.

Browser tests use an isolated temporary database, generated per-run test passwords/device token, local API port 8107 and frontend port 3100. They verify actual login, camera registration, analytics, viewer restrictions/logout, mobile/tablet/desktop overflow, empty states, persistent notes, and actual outbox HTTP ingestion → human confirmation → selected approval → simulated execution → PDF download. The integration clip is explicitly synthetic and is never an evaluation sample. Playback must load metadata and advance currentTime; HTTP-only video checks are insufficient.

Playwright JSON/traces/screenshots are under ignored `frontend/test-results/`; selected successful screenshots and verification summary are retained under docs. Do not publish failed-login traces containing generated test credentials. CI installs its own isolated environment and never sends real external notifications. External provider tests remain mocked.

## Results and limits

See RELEASE_VERIFICATION.md for the exact final counts/commands and dependency audit. Earlier browser failures uncovered missing form submit types, viewer logout authorization, duplicate headings and implicit textarea labels; these were fixed and rerun. Disk ENOSPC temporarily interrupted a browser run; only task-generated caches/duplicate runtime packages were removed. No user documents were deleted.

The default Turbopack CSS subprocess failed to bind its internal local port; webpack is the verified builder. Fonts now use a system stack, requiring no Google fetch. Docker daemon was unavailable; Docker/PostgreSQL runtime checks are not claimed. External detection results and runtime failures are in DETECTION_EVALUATION.md, separate from software tests.

## Manual QA still needed

Long-duration physical webcam/RTSP reconnection; multiple simultaneous real cameras; crowded/moving-camera scenes; low-light and occlusion; keyboard/screen-reader audit of every historical dialog; full light theme; independent PPE labels; high-FPS browser transport and deployments behind a real HTTPS proxy. Automated viewport checks and inspected screenshots do not replace these tasks.

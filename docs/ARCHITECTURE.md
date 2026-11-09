# SafetyLens architecture — current implementation

The application uses Next.js App Router/React/TypeScript, FastAPI/Pydantic, SQLAlchemy/Alembic and SQLite or PostgreSQL. The frontend/backend/PostgreSQL 17 Compose profile has been exercised with actual-model evidence, database/service restarts, isolated restores and a fresh database migration. Earlier statements saying PostgreSQL was never run are superseded; historical reports remain preserved.

## Detection and frame transport

A separate CPU worker hosts up to four camera threads and a durable bounded SQLite outbox. Recorded input is decoded exhaustively with timestamp-based sampling. Live RTSP/network sources use OpenCV FFMPEG five-second open/read options and `LatestFrameCapture`: a daemon reader replaces one latest-frame slot, explicitly counts replaced stale frames and bounds consumer waiting. Actual local MJPEG disconnect/reconnect was tested. Native timeout support depends on the capture backend; this is not a physical RTSP qualification or general hard-real-time guarantee. Camera failure does not intentionally block the other worker threads; no distributed fleet scheduler is implemented.

MediaPipe Lite extracts normalized landmarks from a configured region. Optional up-to-four-pose geometric association maintains separate short-lived histories, abstains on ambiguity and expires missing tracks. Track IDs are ephemeral, not worker identity. The deployed default uses calibrated geometry/motion and temporal rules. An opt-in learned temporal classifier uses causal 62-feature histories and a validation-selected linear model. It remains experimental because the fresh test has excessive false alarms. Checkpoints are bounded/hash-pinned JSON; pose hash and feature version must match.

Offline PPE uses fixed ONNX inference, verified class maps and conservative region association across nine appearance classes. Eight configurable protective requirements are distinct from appearance observations. All deployment gates are closed; provider/demo review is separately labeled. Ordinary glasses/shoes/masks cannot establish equipment rating.

## Evidence and incident flow

Camera observations → temporal candidate → bounded pre/post evidence → completed clip with SHA256 → durable outbox retry → scoped device authentication → UUID/content validation → randomized protected storage → frame/playback preparation → local-CV analysis/incident/notification → operator review → stored lexical SOP retrieval → exact citation snapshot → deterministic response draft → incident confirmation and selected-action approval → simulated execution → audit/PDF.

Real detector events bypass scripted Demo AI. Optional OpenAI image/text interpretation remains a separate upload/reanalysis path; no live paid-provider result is claimed. Metadata is JSON descriptive data under an untrusted-content system instruction. Provider incident/PPE/frame output is checked; raw remote exception text is not logged/chained into public failures. These are defenses, not a claim to eliminate prompt injection. Retrieved procedures cannot execute code or authorize actions; plans remain deterministic templates and approval is enforced server-side.

## Policy and operator console

Camera JSON policies hold sampling, crop, evidence windows, retention, base PPE categories and conditional rules. Activity/role/time are explicit operator-supplied context, not visually inferred identity. Missing conditions remain unknown, overnight ranges are supported, and known nonmatches do not activate rules. Administrator preview is a pure resolution operation with no incident/action effects. The PPE page reads server-side gates/appearance metrics and supports real error/retry, not fabricated detections.

Database-backed SSE notifications cause typed client refetches. Camera previews are labeled snapshots, with sequential timeout-bounded polling to avoid overlapping downloads and object-URL leaks; there is no browser high-FPS video gateway. Human edits use versioned compare-and-swap and stale-update conflicts.

## Trust, persistence and recovery

Opaque revocable cookie sessions, scrypt, CSRF/Origin checks and administrator/manager/operator/viewer roles protect one shared installation. Device tokens have method/path scope plus camera allowlists. Camera sources are encrypted. Evidence is protected according to installation roles; multi-organization or per-user ownership isolation is not implemented. Pure ASGI byte counting bounds request bodies before multipart spooling (110 MiB configured multipart default,256 KiB metadata); reverse-proxy rate/concurrency/transport controls remain required for nonlocal deployment.

Additive migrations preserve historical records. Ordinary seed startup leaves initialized state and referenced SOP chunks intact. Persisted incomplete local-CV jobs resume in one API process, with per-video/idempotency safeguards. This is not a distributed lease/queue protocol. Evidence hashes provide transfer integrity, not trusted capture attestation; audit records are not an immutable certified ledger. External messages and physical actions remain unimplemented/simulated, and no safety certification is claimed.

Evidence and limits: [FINAL_VALIDATION_REPORT.md](FINAL_VALIDATION_REPORT.md), [FALL_DETECTION_EVALUATION.md](FALL_DETECTION_EVALUATION.md), [PPE_EVALUATION.md](PPE_EVALUATION.md), [SECURITY.md](SECURITY.md).

# Architecture

SafetyLens retains Next.js App Router/React/TypeScript, FastAPI services, Pydantic contracts, SQLAlchemy, SQLite and OpenCV. PostgreSQL is an optional configuration path; it was not run in this environment.

## Processing paths

1. Host camera worker: one to four independent camera threads, separate pose providers, timestamp-driven fall logic, optional ONNX PPE inference, exclusive person/PPE association, conservative temporal review, configurable pre/post buffer.
2. Durable delivery: completed evidence copied into a bounded SQLite outbox; HTTPS bearer delivery, UUID deduplication, explicit acknowledgement, persisted retry/backoff, blocked permanent errors and acknowledged-artifact pruning. Delivery is at-least-once, not distributed exactly-once.
3. API ingestion: scoped device credential validates camera ID; randomized bounded media storage; frame extraction; **local_cv** findings and a new incident/notification. Real events do not get reinterpreted by the scripted Demo AI provider.
4. Investigation: original optional OpenAI image/text provider remains available for uploads/reanalysis; frame references and supported classes are validated. Local CV, model interpretation, configured demo and human conclusions have separate provenance.
5. Response: stored SOP text/chunks → weighted lexical retrieval → deterministic, topic-matched action templates → exact citation snapshots → incident confirmation → selective approval → simulated execution → audit/PDF.
6. Operator console: cookie authentication; typed API calls/CSRF; resumable database-backed SSE change notifications trigger refetches, rather than carrying authoritative mutable incident snapshots to overwrite local state. Camera previews are latest JPEG snapshots, not high-FPS video streaming.

## Identity and access

Single-installation users have administrator, safety_manager, safety_operator or viewer roles. Opaque random sessions are stored hashed and expire/revoke server-side. Passwords use scrypt. CSRF and Origin checks guard browser mutations. Devices use a separate server-side token plus camera allowlist. Camera URLs are Fernet-encrypted and withheld from operator inventory responses.

## Persistence

Historical tables and screenshots remain. Additive platform tables store users/sessions, login throttles, camera configuration, incident operations and resumable change events. Alembic's frozen adoption migration creates missing tables/indexes without deleting baseline data. Existing SQLite column compatibility remains for historical databases. Installation backups and careful migration review are required before applying to valuable data.

## Known boundaries

No multi-organization tenancy, certified safety guarantee, authenticated physical actuator, stable multi-person pose identity, face recognition or employee productivity inference. Four camera threads are a resource cap, not a demonstrated four-camera performance guarantee. External actions remain simulated. Camera source credentials are disclosed only to scoped devices or installation administrators. Count-based generated codes were replaced by random suffixes to reduce concurrency collisions; PostgreSQL concurrency has not been benchmarked.

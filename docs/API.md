# API guide

OpenAPI is available at `/docs`. Historical endpoints remain; authenticated installations protect application reads and writes, including evidence/report content. `/api/health`, `/api/demo/info` and the login/session entry points are public as appropriate.

## Sessions and roles

POST `/api/auth/login` with username/password sets an HttpOnly session cookie and returns CSRF token/role. GET `/api/auth/me` restores session context. Send `X-CSRF-Token` for mutations, and use `credentials: include`. POST `/api/auth/logout` revokes the session, including for viewers. Administrator POST `/api/users` creates users; manager/admin GET `/api/users` lists assignable users; administrator PATCH `/api/users/{id}` changes active status/role and revokes sessions. The last administrator cannot be disabled/demoted.

## Cameras

GET `/api/camera-management` returns credential-free configuration, health, source type, facility/zone labels and policy. POST `/api/cameras`, PUT/DELETE `/api/cameras/{id}` manage cameras (administrator). Cameras with incident/media history cannot be deleted. GET `/api/cameras/{id}/snapshot` returns a recent JPEG or a structured unavailable error.

Devices: GET `/api/detector/config/{id}`, POST `/api/detector/heartbeat`, POST `/api/detector/snapshot/{id}` and multipart POST `/api/detector/events`. Send `Authorization: Bearer DEVICE_TOKEN`; server must allow the camera ID. Event schema 1.0 supports possible_person_down, prolonged_person_down and ppe_noncompliance; numeric scores are finite and bounded. Device events must upload evidence. Responses acknowledge mapped asset/event IDs; retries use the same event UUID. The device cannot approve actions or browse other application data.

## Investigation and operations

GET `/api/incidents` supports existing severity/status/camera/search/limit/offset plus `since`, `until` (ISO timestamps) and `ascending`. GET `/api/investigations/{incident_id}` returns incident, linked analysis/workflow and related camera incidents. GET/PUT `/api/incidents/{id}/operations` persists assignment, notes, acknowledgement and resolution. PUT requires the current integer `version`; conflicting updates return `STALE_VERSION` 409. Assign only active user IDs. Existing `/api/analyses/.../review` and `/api/response-plans/...` endpoints retain two-step confirmation/selected approval and simulated-only execution.

## Analytics, exports and updates

GET `/api/analytics?days=30` returns stored incident counts, review outcomes and a defined mean interval. Accuracy and PPE compliance accuracy are null without evaluation data. Historical seed records are explicitly included when in range. GET `/api/incidents-export` returns up to 10,000 CSV records and audits export; filter-aware exports beyond this bound remain future work. Existing incident PDF endpoints remain.

GET `/api/events` is authenticated SSE. `Last-Event-ID` or `after` resumes durable monotonically numbered updates. Event types: `update`, `session_expired`, `resync_required`; periodic comments maintain connectivity. Events carry identifiers/invalidation signals; clients refetch canonical state. Historical gaps request resynchronization. This is a database-backed stream, not Kafka or a durable external side-effect bus.

GET `/api/platform/config` returns safe provider/capability/settings metadata, never keys. Administrator POST `/api/retention` previews evidence expiration by default; `{apply:true, confirmed:true}` applies eligible expiration and audits it.

## Error envelope

`{"error":{"code":"...","message":"..."}}`. Important states: 401 authentication, 403 role/CSRF/camera scope, 409 stale state/mismatched incident/duplicate data, 413 size, 422 validation. HTTP 202 means received/queued, not that the detector was correct or the entire response completed.

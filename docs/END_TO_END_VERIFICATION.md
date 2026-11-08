# Actual detector-to-report verification

## What actually ran

The local isolated application starts the real FastAPI service (SQLite), Next.js frontend, authenticated sessions and database-backed SSE. `scripts/e2e_real_detector.py` configures a registered device-scoped replay camera through the HTTP camera API and launches the actual `safetylens_detector.worker` with MediaPipe CPU inference on the licensed UR Fall fall-07 composite clip and explicit RGB-region calibration. No detection event, pose or incident is invented or inserted directly into the database.

The worker confirms rapid-drop/person-down evidence, records the actual source frames through the pre/post buffer, writes a clip, enqueues it durably and submits multipart media/event data with a scoped bearer token. Backend validation, video preparation/playback derivative, local-CV analysis, incident workflow and operator notification execute normally. Browser assertions check that a matching operator notification exists, open the correct analysis/video, load/play actual video, confirm the incident, approve selected actions, execute simulated actions and download a PDF with the `%PDF` signature. The incident audit endpoint must contain at least four events. Seeded company procedures support deterministic citation-grounded planning; this test does not call external multimodal AI or prove a real company policy's correctness.

The first model-backed seven-case run passed. A broader eight-case run subsequently found a calibration input accessible-name defect; that failure is preserved in `evaluation/final/browser-intermediate-failure.json`, and the label was repaired. Final counts are in FINAL_RELEASE_REPORT.md and `evaluation/final/browser-summary.json`.

## Reproduce

Install the locked backend, detector and frontend environments; acquire the public clips and MediaPipe model explicitly. Keep media/weights outside Git. Run from root:

```sh
SAFETYLENS_REAL_CLIP=/tmp/safetylens-urfall20/fall-07.mp4 \
SAFETYLENS_POSE_MODEL=/path/pose_landmarker_lite.task \
npm --prefix frontend run test:e2e
```

Without those variables the transport case deliberately uses `scripts/e2e_detector_event.py`, which is a **synthetic** integration fixture. Do not call that default a model-backed test. The real fixture refuses missing events, missing rapid-drop evidence or unacknowledged delivery. Event logs and actual outbox records remain in a task-specific temporary folder; compact redacted outputs are retained in evaluation/final/real-worker-result.json.

## Step-specific boundaries

- Camera creation/edit/delete is verified through the browser and real APIs. The model-backed replay reconfigures seeded camera `cam-03`, whose ID is explicitly authorized by the test device token; the newly created CRUD-test camera is a separate test. No dynamically granted device scope is implied.
- Real recorded video is replayed offline as fast as inference permits. Worker wall time is not live fall-to-alert latency; source event times are relative to the clip. The recorded wall interval includes process/model startup, inference, clip encoding and acknowledgement.
- Finite EOF consumes a replay once; partial post-event windows carry an explicit truncation limitation rather than silently disappearing. Final delivery is attempted before worker shutdown; failures remain durable. Sustained physical webcam/RTSP interruption remains unverified.
- Notification existence, SSE cross-client refresh, human controls and PDF content type/signature are verified. Every PDF statement has not been independently fact-checked against video by a safety professional.
- This single actual fall proves a functioning integrated path, not broad CV accuracy or industrial readiness. External actions remain simulated.

## Frontend and security checks

Browser coverage includes real login/logout, viewer restrictions, camera CRUD/calibration round-trip, 390/820/1440 viewport overflow, explicit empty searches, persistent incident notes, analytics network-error recovery and loading all major operational/demo routes. No backend 5xx is accepted during the route smoke test. A full assistive-technology audit, every historical dialog, large fleet stress, light-theme assessment and external provider behavior remain unverified. Backend tests separately cover denied roles, CSRF/origin rejection, session expiration, device scope, optimistic incident versions, retention and migration adoption.

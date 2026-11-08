# Final product audit

Continuation baseline: `9c9315c28a43ead8ffebbafb68681def9fe0577a`, clean existing enhancement branch. Historical claims are rechecked, not treated as acceptance evidence.

## Confirmed blockers before this continuation

- README regression: two original inline screenshots and their captions, problem/solution narrative, staged-demo instructions and exact award wording disappeared from the main README. Original assets remain tracked; historical README alone is insufficient preservation in the primary presentation.
- Detection: conservative video-presence recall was 2/6. Frame-level diagnostic rerun is retained outside Git pending aggregate analysis; tracking loss and failed confirmation are separate observed failure classes. A synthetic transport/browser fixture does not verify an actual model-generated event.
- PPE: weights exist outside Git and ONNX inference loads; no labeled evaluation has yet established useful performance. Conflicting model-card/embedded licensing blocks commercial deployment. No deployment license is inferred from a manifest string.
- Camera worker: policies expose confidence and recording controls, but a live hardware fleet has never been validated. Browser preview is a latest-image interface, not streaming video with overlays. Missing models fail at runtime.
- Deployment: privileged Docker info still reports daemon unavailable at `/Users/amolair/.docker/run/docker.sock`. Only 2.5 GiB disk is free; image builds and additional runtimes may exceed it. Docker runtime must not be represented as passed.
- Setup: defaults depend on working directory; environment templates require first-use copying, administrator bootstrap and consistent localhost hostnames. Tests use isolated configured environments, which cannot alone prove the documented first-use path.

## Verification priorities

Restore primary README, reproduce individual misses with observations and inspect actual frames, freeze a justified candidate before acquiring untouched clips, run a labeled PPE benchmark with explicit training-overlap uncertainty, run actual recorded-media worker through authenticated application workflow, validate documented migrations/bootstrap/startup, expand browser coverage and preserve logs. Missing hardware/daemon/independent relation labels remain explicit acceptance blockers.

## Scope and evidence

Existing routes, services, migrations, detector engines, deployment and automated fixtures were inspected before edits. Historical implementation/report detail remains in PLATFORM_AUDIT.md and RELEASE_VERIFICATION.md; this document records newly established blockers rather than duplicating those inventories. Final gate outcomes belong in FINAL_RELEASE_REPORT.md.

## Additional reproduced integration defects

- Finite replay EOF was treated as camera failure: reconnect reopened the same file, generated fresh event UUIDs and could repeatedly report one recorded incident. EOF now consumes a replay once.
- Short clips could end before the requested post-event interval. Their active capture was discarded rather than delivered. Available frames now finalize with an explicit truncated-window limitation; shutdown also preserves partial evidence.
- A short replay could finish before the two-second transport tick. Final synchronous delivery is attempted; failures retain their durable queue entry.
- Worker replay sampling advanced from each rounded selected frame, unlike the evaluator's fixed sample clock, yielding fewer samples than configured. Replay now advances the fixed clock by its period.
- Docker Desktop was installed but stopped. Starting the application enabled daemon 28.5.1. The first build then failed because `docker-credential-desktop` was absent from shell PATH; a command-local Resources/bin PATH fixes discovery without editing personal Docker configuration.

## Final hardening phase baseline (November 7, 2026)

Clean branch at `0f9e920`, existing remote unchanged. Re-inspected current/historical README, prior commits/reports, complete detector modules, API/auth/database/approval/delivery paths, frontend components/routes, migrations, tests, model provenance and deployment. Baseline rerun: 81 backend tests pass (12.12s), 55 detector tests pass (.043s); frontend lint/typecheck/standalone production build pass. Browser baseline is recorded separately after completion. The current shell omits `/usr/local/bin` and `/opt/homebrew/bin`; command-local PATH restores installed Node/npm/gh/Docker. Temporary prior models/data have been removed outside Git; all retained evaluation artifacts remain intact. No assumption of cached weights is made.

Disk now has approximately 6.8 GiB available. Docker Desktop was stopped; starting the installed application restored daemon28.5.1. No broad cache cleanup or user-file deletion is needed. Full documented image builds can now be attempted. Historical F1 .8 and poor PPE measurements are verified in raw artifacts, not treated as new measurements. The top README award is moved immediately below the title with historically reported attribution; no independent corroboration is invented.

Confirmed research priorities remain intentional-reclining false alerts, partial-body/multi-person misses and poor reference PPE transfer. New work must keep previous clips as development diagnostics and freeze any candidate before new test predictions. No calibrated probability or workplace readiness follows from passing software tests.

## Confirmed failures and final disposition

- Frontend image: reproduce the documented Compose build; the standalone build lacked a `public` directory. `frontend/Dockerfile` now creates it before building. Full image/runtime verified; see DEPLOYMENT_VERIFICATION.md.
- Restart after SOP retrieval: seed code deleted chunks referenced by citations. `seed_data.seed_data(reset_existing=False)` now preserves an initialized database; only explicit demo reset requests replacement. Regression preserves chunk IDs/operator edits; actual PostgreSQL restart passed.
- Interrupted detector processing: persisted media could remain unfinished after process loss. Startup snapshots incomplete non-simulated jobs and `services/recovery.py` resumes them. Regression reconstructs a committed upload without its background task. This is single-process recovery, not distributed leasing.
- Duplicate spooled uploads: a second transaction could wait on the first insert while the first async read needed the same event loop. A per-UUID async ingress lock serializes that path. Two real HTTP uploads of a 4.25 MB clip returned the same asset without deadlock.
- Device scope and event integrity: method/path scope excludes reading incident listings; conflicting camera/source/type or declared SHA receives 409, tampered uploaded content receives 422. Tests cover these boundaries.
- Multi-person association: pose ordering is not identity. Experimental geometric tracking keeps separate histories, expires tracks and starts new IDs on ambiguous crossings. It is bounded and opt-in; no biometric identity or validated crowded-scene accuracy.
- Detection misses/false alarms: the newly frozen set exposed lower generalization (camera-0 recall .40). Full-pose and tracked alternatives did not establish a deployable winner. No thresholds were retuned against the test. Publisher annotations support offline delay analysis; misses are retained. See DETECTION_VALIDATION.md.
- PPE: licensing, preprocessing, classes and output decoding were inspected; neither evaluated model qualified. Local deployment is rejected by camera policy and worker, rather than hidden behind a demo. See PPE_VALIDATION.md.

Final backend suite: 84 passed; detector suite: 58 passed; browser suite: 8 passed, with one actual-model case repeated after the caption fix. Evidence and remaining acceptance gates are in FINAL_RELEASE_REPORT.md and PILOT_READINESS.md.

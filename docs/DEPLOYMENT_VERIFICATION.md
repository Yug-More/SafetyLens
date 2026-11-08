# Deployment verification — final hardening

## Supported configuration now exercised

The actual documented `docker-compose.yml` plus PostgreSQL override built and ran frontend standalone/Node22, backend/Python3.12 and **PostgreSQL17-alpine**. All three reported healthy. Host ports are now loopback-bound3000/8000; database port remains internal. This replaces the earlier environment-only blocker, preserved in PRODUCT_COMPLETION_BASELINE_REPORT.md and Git history. It does not establish production HTTPS or workplace readiness.

New disk availability permitted builds without deleting user files or research data. Docker Desktop was initially stopped and this shell omitted installed tool paths; command-local PATH and starting the installed application resolved those environment issues. No broad image/cache prune was performed.

## Actual defects found and fixed

1. Frontend's final COPY expected `/app/public`, but the checkout has no tracked directory. The builder now ensures that empty directory before building; both images complete.
2. Restart after actual SOP retrieval failed with PostgreSQL foreign-key violations: automatic seed code deleted referenced chunks. Normal seeding now preserves initialized records and operator edits; confirmed demo reset is separate. The source regression and actual repeated container restart pass.
3. Database reconnection now uses SQLAlchemy pre-ping. Interrupted local detector jobs have explicit single-process recovery, and completed processing is idempotent.
4. Final UI incorrectly kept a draft 'no actions executed' sentence after recorded simulated results. It now displays recorded-result count/outcome guidance, verified through actual standalone UI and a targeted browser regression.

The previous Linux npm optional-peer lockfile fix is retained. Runtime users remain non-root; Docker ignore files exclude private/local artifacts. No original data volume is replaced to make a test pass.

## Verified workflow and faults

`scripts/verify_compose.py` on a dedicated project processed an actual MediaPipe-generated recorded event and exercised authenticated ingestion, SHA-256 content verification, notification, actual browser playback, confirmation, selected approval, simulated execution, audit and valid PDF. Two different authenticated roles updated one incident version concurrently:200/409. During a backend outage, a reopened durable outbox retained its real event, recovered and reused the original asset after restart. PostgreSQL restart preserved the session and evidence mapping.

A private PostgreSQL custom dump restored to a brand-new verification database with ten detector records; those are test/replay records, not ten independent accidents. Separate media backup restored88 files to a new volume with identical per-file hashes, mode0600 archive. These quiescent component snapshots are **not** a coordinated point-in-time or offsite recovery guarantee. Encryption keys remain a separate required secret. No dumps, QA credentials, archives or weights are committed.

`scripts/verify_camera_load.py` ran four actual-model recorded replays and a controlled MJPEG outage/recovery. PERFORMANCE_REPORT.md describes exact scope and resource figures. Physical RTSP and sustained workplace streams remain unverified.

Raw redacted proof: `evaluation/hardening/compose-verification.json`, `camera-load.json`, `media-backup.json`. The full-stack restart initially failed on seeding and was fixed; this failure is not relabeled as a passing smoke test.

## Reproduce on an isolated local installation

Use a new Compose project and private env file containing generated `POSTGRES_PASSWORD`, `CAMERA_ENCRYPTION_KEY`, `DETECTOR_API_TOKEN` and an explicit `DETECTOR_CAMERA_IDS` list. Do not commit it. Keep an existing installation's keys/volumes unchanged.

```sh
# If the shell cannot find Docker Desktop's credential helper on macOS:
export PATH="/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:/opt/homebrew/bin:$PATH"
docker compose --env-file /private/path/verify.env -p safetylens-hardening -f docker-compose.yml -f docker-compose.postgres.yml up --build -d
docker compose --env-file /private/path/verify.env -p safetylens-hardening -f docker-compose.yml -f docker-compose.postgres.yml ps
docker compose --env-file /private/path/verify.env -p safetylens-hardening -f docker-compose.yml -f docker-compose.postgres.yml exec backend python -m app.manage create-user --username YOUR_USERNAME
```

Open `http://localhost:3000`. There is no default password. Match the browser hostname to its configured API/origins. The supported local profile is HTTP; nonlocal production needs a separately verified HTTPS proxy and secure cookies.

The automated full-stack verifier creates private QA accounts and requires the test device scope `cam-03`:

```sh
python3 scripts/acquire_final_validation.py --kind urfall --directory /tmp/safetylens-replay
backend/.venv/bin/python scripts/verify_compose.py --env-file /private/path/verify.env --project safetylens-hardening --clip /tmp/safetylens-replay/fall-07.mp4 --pose-model /path/pose_landmarker_lite.task --output-directory /tmp/unique-verification-run
backend/.venv/bin/python scripts/verify_media_backup.py --env-file /private/path/verify.env --output /tmp/unique-media-backup
```

Use a fresh output directory; private backups refuse overwriting an existing file. The load/MJPEG script additionally requires a private JSON QA credential file with `username`/`password`, creates test cameras, expands the test token scope and recreates the test backend. Its project is explicitly `safetylens-hardening`; do not run it against an operational installation.

```sh
backend/.venv/bin/python scripts/verify_camera_load.py --credentials /private/path/qa.json --env-file /private/path/verify.env --clip /tmp/safetylens-replay/fall-07.mp4 --model /path/pose_landmarker_lite.task --output /tmp/unique-load-test
```

## Limits and operations

Use one API process for the tested local recovery model. No distributed leases/worker fleet guarantee, rolling-upgrade qualification or load balancer was tested. First-run seeding initializes examples; restarting preserves existing records rather than refreshing a demonstration. If an existing customized database lacks sample SOPs, it is not overwritten—upload reviewed procedures normally. Do not disable authentication or drop volumes to make setup appear successful.

Test accounts/cameras and restored test volumes are isolated artifacts. Private backups/media remain local; model/data licensing and site privacy still apply. Container verification is an engineering milestone, not a production-security or industrial safety approval.

# Deployment verification

## Actual environment and reproduced failures

macOS arm64 / Apple M2 Pro; Docker Desktop daemon 28.5.1 after starting the installed application. Earlier daemon-unavailable reports remain historical, not current. Shell PATH lacked `docker-credential-desktop`; adding `/Applications/Docker.app/Contents/Resources/bin` to the command-local PATH resolved image metadata access. No personal Docker authentication settings were changed.

The backend Docker image **built successfully**, with locked Python 3.12 dependencies and non-root user. Its actual startup applied the additive migration and seeded the isolated database. A separate existing `postgres:16` image ran against a new task-specific named volume, connected via host loopback port 55432. The API container listened on loopback port 18000. Authenticated login/camera creation/inventory worked. The database and API were both restarted; the new camera and authenticated session survived, health returned 200 and the revision remained `0001_platform`. Raw output: `evaluation/final/container-results.json`.

Twenty sequential authenticated camera-inventory requests: minimum 9.617 ms, mean 12.121 ms, maximum 25.963 ms. These include local HTTP/database round trips and are a tiny warm single-client sample, not a production latency SLO or saturation benchmark. No SQL query throughput, CPU/GPU or peak-memory benchmark is claimed.

## Frontend build repair and remaining blocker

The actual Linux `node:22-alpine` builder (npm 10.9.9) rejected the host-produced lockfile: missing `@emnapi/runtime@1.11.3` and `@emnapi/core@1.11.3`. Host `npm install --package-lock-only` did not fully repair this cross-platform discrepancy. Regenerating the lockfile in an isolated Linux directory using the builder's npm repaired it; `npm ci --dry-run --ignore-scripts` then successfully resolved 658 packages. No dependency was disabled to hide the failure.

Missing Docker ignore files would have sent host node_modules, build artifacts and private environment files in the frontend context. New `.dockerignore` files exclude those paths. The frontend now builds a Next standalone runtime image with static/public assets, non-root execution and a health check; private build-time configuration remains separate from browser-public API URLs. This image design is **implemented but not fully built/run here**.

Available host disk fell from approximately 2.5 GiB before image pulls/builds to approximately 0.2 GiB. A fresh Linux node_modules/build would exceed that remaining capacity. The full frontend image build was stopped at the verified dependency-resolution stage rather than claiming a successful runtime. Only task-generated webpack caches were reclaimed. No unrelated images, volumes or user files were deleted. The existing Compose `postgres:17-alpine` profile was statically validated but **PostgreSQL 17 itself was not run**. PostgreSQL 16 runtime evidence must not be generalized to a full Compose17 pass.

Verification containers were stopped and removed after testing. Task-specific database/evidence volumes are retained; they do not replace application backups. Docker Desktop was left running; preexisting containers/images were untouched.

## Independent full-stack commands

After providing several GiB of free disk, generated private secrets and a new verification project:

```sh
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" # macOS helper discovery if needed
# Supply POSTGRES_PASSWORD, CAMERA_ENCRYPTION_KEY, DETECTOR_API_TOKEN privately.
docker compose -p safetylens-check -f docker-compose.yml -f docker-compose.postgres.yml config --quiet
docker compose -p safetylens-check -f docker-compose.yml -f docker-compose.postgres.yml up --build -d
docker compose -p safetylens-check -f docker-compose.yml -f docker-compose.postgres.yml ps
docker compose -p safetylens-check -f docker-compose.yml -f docker-compose.postgres.yml exec backend python -m app.manage create-user --username YOUR_USERNAME
# Visit http://localhost:3000 and sign in; verify media/review/report with a controlled clip.
docker compose -p safetylens-check -f docker-compose.yml -f docker-compose.postgres.yml restart
# Recheck health, records and media. Keep volumes; do not use down -v against real evidence.
```

The model-backed detector runs separately on the host with explicitly downloaded models and camera-scoped credentials. Hardware camera permissions, RTSP network access, headless Linux pose runtime and production HTTPS are separate unresolved checks. Secrets with reserved URI characters require correct database URL encoding. Use a proxy and secure cookies for any nonlocal deployment; the verified local profile uses HTTP and is not production authorization.

## Controlled observation protocol

Do not use this detector as a primary safety control. Before a supervised shadow evaluation: obtain workplace/privacy consent, define camera layout and authorized operators, minimize captured areas, configure evidence retention, rehearse false-alarm rejection and simulated response, verify offline/outbox warnings and storage bounds, and keep existing trained personnel/certified controls active. Record all candidate events and independently label missed events from continuous footage; measure camera-hours, onsets, reviewer agreement and failure recovery. Do not deploy the current reference PPE model. No controlled workplace pilot or regulatory approval has occurred.

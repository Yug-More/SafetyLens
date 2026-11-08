# Deployment and local development

## Verified development workflow

Python 3.12 and Node 22+ are the intended tools. Baseline verification used Python 3.12.12 and Node 24.11.1. The API and detector have separate locks/environments to avoid overlapping OpenCV distributions.

```sh
python3.12 -m venv backend/.venv
uv pip sync --python backend/.venv/bin/python backend/requirements.lock.txt
# Configure backend/.env from its template; retain any existing private values.
cd backend
.venv/bin/python -m alembic -c alembic.ini upgrade head
.venv/bin/python -m app.seed.run   # Optional historical demo records, not a live installation
.venv/bin/python -m app.manage create-user --username YOUR_USERNAME
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, `cd frontend && npm ci && npm run dev`. API URL defaults to localhost:8000; ensure both API and frontend use matching localhost/127.0.0.1 hostnames so SameSite cookies work. Backend FRONTEND_ORIGINS must include the exact frontend origin. The new build uses webpack because Turbopack's CSS worker could not bind its internal local port in this environment. System fonts remove the former Google-font build dependency.

No default administrator password is provided. `AUTH_ENABLED=false` is only an explicitly insecure local demo option, rejected with production environment. Do not use demo mode to bypass authentication on a public service.

## Containers

`docker compose up --build` starts the API/frontend with local HTTP authentication. Supply camera encryption/device secrets through private environment values when using workers. Run the bootstrap user CLI in the API container interactively. Containers run as non-root users; API startup applies Alembic before optionally seeding demo records. Persistent media/database uses the existing named volume.

An optional PostgreSQL path is `docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build`. Set POSTGRES_PASSWORD through a secret manager/private environment and URL-encode special characters when using a URL. No migration silently copies SQLite data to PostgreSQL. Back up and migrate valuable data through a separately reviewed process.

Docker daemon was not running during verification: image builds/container startup and PostgreSQL operation remain unverified. Compose configuration is validated separately where the CLI permits it.

## Production configuration requirements

Set ENVIRONMENT=production, AUTH_ENABLED=true and COOKIE_SECURE=true; serve behind HTTPS with same-site API/frontend and restrictive origins. Apply Alembic explicitly. Provide an organization-approved camera/model/data configuration, protected media volumes, backups, reviewed dependency advisories and monitoring. The application checks migration revision and security flags, but does not provide TLS termination, tenancy, full intrusion protection or certified industrial safety.

Browser public API variables are compiled into frontend builds. Rebuild for a different browser-reachable API origin. Do not put credentials in NEXT_PUBLIC variables.

## Detector

See CAMERA_PIPELINE.md and DETECTION_EVALUATION.md. Model weights/data are external. CPU inference was exercised on the Mac host; that runtime still required OS graphics context. Headless Linux camera/GPU support is not claimed as verified. The worker’s camera cap and bounded outbox control resources; production capacity must be benchmarked on actual cameras/hardware.

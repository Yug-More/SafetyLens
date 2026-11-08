#!/bin/sh
set -eu
python -m alembic -c /app/alembic.ini upgrade head
if [ "${DEMO_MODE:-false}" = "true" ]; then
  python -m app.seed.run
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

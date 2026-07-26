#!/usr/bin/env sh
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}"

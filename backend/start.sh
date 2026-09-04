#!/usr/bin/env sh
# Component: Backend -> Deployment -> Container entrypoint
# Belongs to: the CMD run by both backend/Dockerfile and backend/Dockerfile.light.
# Purpose: optionally runs Alembic migrations (gated by RUN_MIGRATIONS, set to "1" for a
# one-off deploy that needs a schema update) then starts the actual FastAPI server via
# uvicorn, binding to Render's dynamically assigned $PORT (falling back to 7860 locally).
set -e

if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Running database migrations..."
  alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}"

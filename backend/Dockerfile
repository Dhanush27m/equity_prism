# Component: Backend -> Deployment -> Local/self-hosted image
# Belongs to: used by `docker compose` for local/self-hosted development — the "heavy"
# counterpart to Dockerfile.light, kept as the local default (torch-based
# sentence-transformers, Redis, Celery all still work here since nothing in this image
# strips them out or forces the lightweight env profile).
# Purpose: a straightforward image build — installs the full requirements.txt (including
# sentence-transformers/torch) and runs uvicorn directly, no lightweight-profile env
# overrides baked in.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

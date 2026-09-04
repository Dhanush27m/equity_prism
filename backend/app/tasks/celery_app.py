"""
Component: Backend -> Tasks -> Celery app (local/self-hosted profile only)
Belongs to: the background-job runtime used when INGEST_MODE=celery (the local/self-
hosted default) — not used in the hosted/free-tier deployment, which uses FastAPI
BackgroundTasks instead (see api/routes/documents.py's _dispatch_ingestion).
Purpose: configures the Celery application (Redis broker + result backend) that a
separate worker process consumes tasks from.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "equity_prism",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.ingest"],
)

celery_app.conf.update(
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    task_default_queue="equity_prism",
)

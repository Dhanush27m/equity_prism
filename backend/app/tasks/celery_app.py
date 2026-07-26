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

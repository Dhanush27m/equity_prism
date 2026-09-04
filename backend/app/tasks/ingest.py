"""
Component: Backend -> Tasks -> Celery task (local/self-hosted profile only)
Belongs to: dispatched by api/routes/documents.py when INGEST_MODE=celery; consumed by
a separate Celery worker process (not the API process).
Purpose: the Celery task wrapper around the real ingestion work in
app/rag/ingestion.py's process_document — kept as a one-line adapter so the actual
logic has no Celery dependency and can also be called directly (as FastAPI
BackgroundTasks does in the hosted profile).
"""

from app.rag.ingestion import process_document
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.ingest.ingest_document", bind=True, max_retries=0)
def ingest_document(self, document_id: int) -> dict:
    return process_document(document_id)

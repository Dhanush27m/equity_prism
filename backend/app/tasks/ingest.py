from app.rag.ingestion import process_document
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.ingest.ingest_document", bind=True, max_retries=0)
def ingest_document(self, document_id: int) -> dict:
    return process_document(document_id)

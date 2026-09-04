"""
Component: Backend -> RAG Pipeline -> Ingestion (background processing)
Belongs to: the actual work function run for every uploaded PDF — invoked either as a
Celery task (app/tasks/ingest.py, local/self-hosted profile) or a FastAPI BackgroundTask
(app/api/routes/documents.py, hosted profile, INGEST_MODE=background).
Purpose: turns one uploaded PDF into embedded, searchable DocumentChunk rows, updating
the parent Document's status (pending -> processing -> ready/failed) as it goes.
Deliberately synchronous (plain SQLAlchemy Session, not async) since it's meant to run
off the request thread either via Celery or FastAPI's background threadpool.
"""

import os

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Document, DocumentChunk
from app.rag import embeddings
from app.rag.chunking import extract_and_chunk

settings = get_settings()
# A separate sync engine (DATABASE_URL_SYNC) since this module runs outside the async
# request lifecycle and needs its own plain SQLAlchemy Session.
_engine = create_engine(settings.database_url_sync, future=True, pool_pre_ping=True)


# Where an uploaded PDF is stored on disk, keyed by its Document row id.
def _document_path(document_id: int) -> str:
    return os.path.join(settings.upload_dir, f"{document_id}.pdf")


# Full ingestion pipeline for one document: marks it "processing", extracts+chunks its
# text, embeds every chunk, replaces any prior chunks for this document, and marks it
# "ready" (or "failed" with the error message truncated to 1000 chars, on any exception).
def process_document(document_id: int) -> dict:
    with Session(_engine) as session:
        document = session.scalar(select(Document).where(Document.id == document_id))
        if document is None:
            return {"document_id": document_id, "status": "missing"}
        document.status = "processing"
        document.error = None
        session.commit()

        try:
            path = _document_path(document_id)
            if not os.path.exists(path):
                raise FileNotFoundError(f"upload not found: {path}")

            num_pages, chunks = extract_and_chunk(path)
            if not chunks:
                raise ValueError("no extractable text in PDF")

            vectors = embeddings.embed_texts([c["content"] for c in chunks])

            session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            session.add_all(
                [
                    DocumentChunk(
                        document_id=document_id,
                        chunk_index=c["chunk_index"],
                        content=c["content"],
                        page_number=c["page_number"],
                        embedding=vec,
                    )
                    for c, vec in zip(chunks, vectors)
                ]
            )
            document.num_pages = num_pages
            document.num_chunks = len(chunks)
            document.status = "ready"
            session.commit()
            return {"document_id": document_id, "status": "ready", "chunks": len(chunks)}
        except Exception as exc:
            session.rollback()
            document = session.scalar(select(Document).where(Document.id == document_id))
            if document is not None:
                document.status = "failed"
                document.error = str(exc)[:1000]
                session.commit()
            return {"document_id": document_id, "status": "failed", "error": str(exc)}

import os

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models import Document, User

settings = get_settings()
router = APIRouter(prefix="/documents", tags=["documents"])


def _dispatch_ingestion(document_id: int, background_tasks: BackgroundTasks) -> None:
    if settings.ingest_mode == "celery":
        from app.tasks.celery_app import celery_app

        celery_app.send_task("app.tasks.ingest.ingest_document", args=[document_id])
    else:
        from app.rag.ingestion import process_document

        background_tasks.add_task(process_document, document_id)


def _serialize(doc: Document) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename,
        "status": doc.status,
        "num_pages": doc.num_pages,
        "num_chunks": doc.num_chunks,
        "error": doc.error,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


async def _local_user(db: AsyncSession) -> User:
    user = (await db.execute(select(User).where(User.username == "local"))).scalar_one_or_none()
    if user is None:
        user = User(username="local")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


@router.get("")
async def list_documents(db: AsyncSession = Depends(get_db)) -> dict:
    user = await _local_user(db)
    rows = (
        await db.execute(
            select(Document).where(Document.user_id == user.id).order_by(Document.created_at.desc())
        )
    ).scalars().all()
    return {"documents": [_serialize(d) for d in rows]}


@router.post("", status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    name = file.filename or "upload.pdf"
    if not name.lower().endswith(".pdf") and file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF uploads are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb} MB limit")

    user = await _local_user(db)
    document = Document(user_id=user.id, filename=name, status="pending")
    db.add(document)
    await db.commit()
    await db.refresh(document)

    os.makedirs(settings.upload_dir, exist_ok=True)
    path = os.path.join(settings.upload_dir, f"{document.id}.pdf")
    with open(path, "wb") as fh:
        fh.write(content)

    _dispatch_ingestion(document.id, background_tasks)
    return _serialize(document)


@router.get("/{document_id}")
async def get_document(document_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return _serialize(doc)


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)) -> None:
    doc = (await db.execute(select(Document).where(Document.id == document_id))).scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()
    path = os.path.join(settings.upload_dir, f"{document_id}.pdf")
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

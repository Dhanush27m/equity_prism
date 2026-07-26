from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk

RRF_K = 60


def _row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "document_id": row.document_id,
        "filename": row.filename,
        "content": row.content,
        "page_number": row.page_number,
    }


async def vector_search(db: AsyncSession, user_id: int, query_emb: list[float], k: int) -> list[dict]:
    distance = DocumentChunk.embedding.cosine_distance(query_emb)
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.content,
            DocumentChunk.page_number,
            Document.filename,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.user_id == user_id,
            Document.status == "ready",
            DocumentChunk.embedding.isnot(None),
        )
        .order_by(distance)
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()
    return [_row_to_dict(r) for r in rows]


async def fulltext_search(db: AsyncSession, user_id: int, query: str, k: int) -> list[dict]:
    tsv = func.to_tsvector("english", DocumentChunk.content)
    tsq = func.plainto_tsquery("english", query)
    rank = func.ts_rank(tsv, tsq)
    stmt = (
        select(
            DocumentChunk.id,
            DocumentChunk.document_id,
            DocumentChunk.content,
            DocumentChunk.page_number,
            Document.filename,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(
            Document.user_id == user_id,
            Document.status == "ready",
            tsv.op("@@")(tsq),
        )
        .order_by(rank.desc())
        .limit(k)
    )
    rows = (await db.execute(stmt)).all()
    return [_row_to_dict(r) for r in rows]


def rrf_merge(result_lists: list[list[dict]], limit: int) -> list[dict]:
    merged: dict[int, dict] = {}
    scores: dict[int, float] = {}
    for results in result_lists:
        for position, chunk in enumerate(results, start=1):
            cid = chunk["id"]
            scores[cid] = scores.get(cid, 0.0) + 1.0 / (RRF_K + position)
            if cid not in merged:
                merged[cid] = chunk
    ordered = sorted(merged.values(), key=lambda c: scores[c["id"]], reverse=True)
    for c in ordered:
        c["rrf_score"] = scores[c["id"]]
    return ordered[:limit]


async def hybrid_retrieve(
    db: AsyncSession, user_id: int, query: str, query_emb: list[float], k_each: int, limit: int
) -> list[dict]:
    vector_results = await vector_search(db, user_id, query_emb, k_each)
    fulltext_results = await fulltext_search(db, user_id, query, k_each)
    return rrf_merge([vector_results, fulltext_results], limit)

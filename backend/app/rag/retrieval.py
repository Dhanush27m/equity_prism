"""
Component: Backend -> RAG Pipeline -> Query-time retrieval
Belongs to: called from app/rag/pipeline.py's research() function.
Purpose: implements hybrid retrieval — a pgvector cosine-similarity search and a
Postgres full-text search, run independently and merged with Reciprocal Rank Fusion
(RRF) so results that rank well in either (or both) rise to the top without needing to
normalize the two searches' incompatible score scales.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Document, DocumentChunk

# RRF's rank-damping constant (a common default from the original RRF paper) — larger
# values reduce the influence of rank differences further down each list.
RRF_K = 60


# Normalizes one retrieved row (regardless of which search produced it) into the shared
# chunk dict shape both search functions and the pipeline use.
def _row_to_dict(row) -> dict:
    return {
        "id": row.id,
        "document_id": row.document_id,
        "filename": row.filename,
        "content": row.content,
        "page_number": row.page_number,
    }


# Semantic search: ranks the current user's ready-document chunks by pgvector cosine
# distance to the query embedding, closest k first.
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


# Keyword search: ranks the same scope of chunks by Postgres's built-in full-text search
# (to_tsvector/plainto_tsquery), highest ts_rank first. Catches exact-term matches that a
# pure vector search can under-rank.
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


# Reciprocal Rank Fusion: scores every chunk by summing 1/(RRF_K + rank) across each
# ranked list it appears in, then sorts by that combined score. A chunk appearing near
# the top of both lists scores higher than one appearing near the top of only one.
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


# Top-level entry point: runs both searches and merges them via RRF. Called once per
# document_research question.
async def hybrid_retrieve(
    db: AsyncSession, user_id: int, query: str, query_emb: list[float], k_each: int, limit: int
) -> list[dict]:
    vector_results = await vector_search(db, user_id, query_emb, k_each)
    fulltext_results = await fulltext_search(db, user_id, query, k_each)
    return rrf_merge([vector_results, fulltext_results], limit)

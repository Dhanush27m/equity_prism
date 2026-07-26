import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag import embeddings, reranker
from app.rag.retrieval import hybrid_retrieve

CANDIDATE_K = 20
TOP_N = 5
SNIPPET_CHARS = 320


def _snippet(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "…"


def _build_context(chunks: list[dict]) -> tuple[str, list[dict]]:
    blocks: list[str] = []
    citations: list[dict] = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(
            f"[{i}] (source: {c['filename']}, page {c['page_number']})\n{c['content'].strip()}"
        )
        citations.append(
            {
                "marker": i,
                "chunk_id": c["id"],
                "document_id": c["document_id"],
                "filename": c["filename"],
                "page_number": c["page_number"],
                "snippet": _snippet(c["content"]),
            }
        )
    return "\n\n".join(blocks), citations


async def research(db: AsyncSession, user_id: int, question: str) -> dict:
    query_emb = await asyncio.to_thread(embeddings.embed_query, question)
    candidates = await hybrid_retrieve(db, user_id, question, query_emb, CANDIDATE_K, CANDIDATE_K)
    if not candidates:
        return {"context": "", "citations": [], "chunk_ids": [], "top_chunks": []}
    top = await asyncio.to_thread(reranker.rerank, question, candidates, TOP_N)
    context, citations = _build_context(top)
    return {
        "context": context,
        "citations": citations,
        "chunk_ids": [c["id"] for c in top],
        "top_chunks": top,
    }

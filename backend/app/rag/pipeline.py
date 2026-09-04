"""
Component: Backend -> RAG Pipeline -> Query-time orchestration
Belongs to: the single entry point app/agents/document_research.py calls into.
Purpose: wires together query embedding, hybrid retrieval, optional reranking, and
context/citation formatting into one research() call that returns everything the
document_research agent's prompt and citation UI need.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.rag import embeddings, reranker
from app.rag.retrieval import hybrid_retrieve

settings = get_settings()

CANDIDATE_K = 20  # how many chunks each of vector/fulltext search retrieves before merge
TOP_N = 5  # how many chunks actually go into the LLM's context
SNIPPET_CHARS = 320  # citation preview length shown in the UI


# Trims a chunk's full content down to a short, whitespace-normalized preview for the
# citation UI (the LLM still sees the full chunk; only the UI snippet is truncated).
def _snippet(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= SNIPPET_CHARS else text[:SNIPPET_CHARS].rsplit(" ", 1)[0] + "…"


# Formats the final ranked chunks into (a) the numbered [n] context block fed to the LLM
# and (b) a parallel citations list (filename, page, snippet) surfaced to the frontend.
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


# Main entry point. Embeds the question, runs hybrid retrieval for CANDIDATE_K
# candidates, optionally reranks with a cross-encoder (RERANK_ENABLED — on locally, off
# in the hosted profile to keep the free-tier image lean) down to TOP_N, then formats
# the result. Returns an empty bundle (no LLM call needed) if nothing was retrieved.
async def research(db: AsyncSession, user_id: int, question: str) -> dict:
    query_emb = await asyncio.to_thread(embeddings.embed_query, question)
    candidates = await hybrid_retrieve(db, user_id, question, query_emb, CANDIDATE_K, CANDIDATE_K)
    if not candidates:
        return {"context": "", "citations": [], "chunk_ids": [], "top_chunks": []}
    if settings.rerank_enabled:
        top = await asyncio.to_thread(reranker.rerank, question, candidates, TOP_N)
    else:
        top = candidates[:TOP_N]
    context, citations = _build_context(top)
    return {
        "context": context,
        "citations": citations,
        "chunk_ids": [c["id"] for c in top],
        "top_chunks": top,
    }

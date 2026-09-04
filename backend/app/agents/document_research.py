"""
Component: Backend -> AI Orchestration Layer -> Specialist agent (LangGraph node)
Belongs to: one of the five parallel specialists dispatched by the router; the only one
that talks to the RAG subsystem (app/rag/*).
Purpose: answers questions from the user's uploaded PDF documents using hybrid retrieval
(app/rag/pipeline.py), with mandatory inline [n] citations back to the retrieved passages.
"""

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.llm.factory import complete
from app.models import RagTrace, User
from app.rag import pipeline

# System prompt: restricts the model to the retrieved excerpts only, requires inline
# [n] citation markers, and explicitly instructs it to say so rather than guess when the
# excerpts don't contain the answer.
SYS = (
    "You are a document research analyst answering questions over a user's uploaded financial "
    "documents (annual reports, filings, research notes). You are given numbered excerpts retrieved "
    "from those documents. Answer the question using ONLY the information in these excerpts. "
    "Cite every claim with the bracketed source marker it comes from, e.g. [1] or [2]. "
    "If the excerpts do not contain the answer, say so plainly and do not speculate. "
    "Be concise and factual, format in markdown. This is research, not personalised investment advice."
)


# Best-effort persistence of a RAG evaluation trace row (question/answer/chunks/citations)
# for later inspection — failures here are swallowed so a logging issue never breaks chat.
async def _persist_trace(question, answer, chunk_ids, citations, res, tracer) -> None:
    try:
        async with AsyncSessionLocal() as session:
            session.add(
                RagTrace(
                    question=question,
                    answer=answer,
                    chunk_ids=chunk_ids,
                    citations=citations,
                    model=res.model,
                    source=res.source,
                    trace_id=tracer.id if tracer else None,
                )
            )
            await session.commit()
    except Exception:
        pass


# LangGraph node entry point. Runs the hybrid RAG pipeline for the question, short-
# circuits with a fixed "nothing found" fragment (no LLM call) if retrieval returns zero
# chunks, otherwise generates a cited answer and persists an evaluation trace of it.
async def run(state: dict, config: dict | None = None) -> dict:
    tracer = (config or {}).get("configurable", {}).get("tracer")
    question = state["question"]

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.username == "local"))).scalar_one_or_none()
        if user is None:
            return {}
        bundle = await pipeline.research(session, user.id, question)

    if not bundle["chunk_ids"]:
        return {
            "fragments": [
                {
                    "agent": "document_research",
                    "title": "Document research",
                    "content": "No relevant passages were found in the uploaded documents for this question.",
                }
            ],
            "meta": [{"agent": "document_research", "model": None, "source": "no_context"}],
        }

    messages = [
        {"role": "system", "content": SYS},
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Retrieved document excerpts:\n{bundle['context']}\n\n"
                "Answer with inline [n] citations."
            ),
        },
    ]
    res = await complete(messages, temperature=0.2, max_tokens=1000, tracer=tracer, label="document_research")

    citations = [
        {
            "agent": "document_research",
            "type": "document",
            "marker": c["marker"],
            "chunk_id": c["chunk_id"],
            "document_id": c["document_id"],
            "filename": c["filename"],
            "page_number": c["page_number"],
            "label": f"{c['filename']} — p.{c['page_number']}",
            "snippet": c["snippet"],
        }
        for c in bundle["citations"]
    ]

    await _persist_trace(question, res.text, bundle["chunk_ids"], citations, res, tracer)

    return {
        "fragments": [
            {"agent": "document_research", "title": "Document research", "content": res.text}
        ],
        "meta": [
            {"agent": "document_research", "model": res.model, "source": res.source, "latency_ms": res.latency_ms}
        ],
        "citations": citations,
    }

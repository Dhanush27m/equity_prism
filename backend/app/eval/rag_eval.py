"""
Component: Backend -> Evaluation -> RAG pipeline evaluation harness
Belongs to: a standalone script (`python -m app.eval.rag_eval`), not called from the API.
Purpose: a self-built, RAGAS-style evaluation of the RAG pipeline — no external eval
library dependency. Seeds the synthetic corpus from app/eval/corpus.py as a fake
document, runs the real hybrid-retrieval pipeline against it, and scores the results on
three LLM-as-judge metrics: faithfulness, answer relevancy, and context precision.
"""

import argparse
import asyncio
import json
import math

from sqlalchemy import delete

from app.agents.document_research import SYS as ANSWER_SYS
from app.api.deps import get_local_user
from app.core.database import AsyncSessionLocal
from app.eval.corpus import EVAL_FILENAME, PAGES, QUESTIONS
from app.llm.factory import complete
from app.models import Document, DocumentChunk
from app.rag import embeddings, pipeline
from app.rag.chunking import chunk_pages


# Best-effort JSON parsing for LLM-judge responses: strips markdown code fences, then
# falls back to locating the outermost {...} span if the whole response isn't valid JSON.
def _parse_json(text: str, fallback):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return fallback
        return fallback


# Plain cosine similarity between two embedding vectors (used by answer_relevancy below).
def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# Inserts the synthetic corpus (app/eval/corpus.py) as a real, "ready" Document + chunked
# + embedded DocumentChunk rows for the local user, so the real pipeline.research() can
# run against it exactly as it would against a real upload. Deletes any prior eval
# document with the same filename first so re-runs don't accumulate duplicates.
async def seed_document(session) -> int:
    user = await get_local_user(session)
    await session.execute(
        delete(Document).where(
            Document.user_id == user.id, Document.filename == EVAL_FILENAME
        )
    )
    await session.commit()

    document = Document(
        user_id=user.id,
        filename=EVAL_FILENAME,
        status="ready",
        num_pages=len(PAGES),
    )
    session.add(document)
    await session.flush()

    chunks = chunk_pages(PAGES)
    vectors = await asyncio.to_thread(embeddings.embed_texts, [c["content"] for c in chunks])
    session.add_all(
        [
            DocumentChunk(
                document_id=document.id,
                chunk_index=c["chunk_index"],
                content=c["content"],
                page_number=c["page_number"],
                embedding=vec,
            )
            for c, vec in zip(chunks, vectors)
        ]
    )
    document.num_chunks = len(chunks)
    await session.commit()
    return document.id


# Removes the synthetic eval document (and its chunks, via cascade) once evaluation finishes.
async def cleanup_document(session, document_id: int) -> None:
    await session.execute(delete(Document).where(Document.id == document_id))
    await session.commit()


# Generates an answer the same way the real document_research agent would (same system
# prompt, same "answer from these excerpts with [n] citations" instruction).
async def generate_answer(question: str, context: str) -> str:
    messages = [
        {"role": "system", "content": ANSWER_SYS},
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"Retrieved document excerpts:\n{context}\n\n"
                "Answer with inline [n] citations."
            ),
        },
    ]
    res = await complete(messages, temperature=0.2, max_tokens=700)
    return res.text


# Metric 1 — Faithfulness: an LLM decomposes the generated answer into atomic factual
# statements, then a second LLM call judges each statement as supported/unsupported by
# the retrieved context. Score = fraction of statements that are supported.
async def faithfulness(question: str, answer: str, context: str) -> float:
    extract = [
        {
            "role": "system",
            "content": (
                "Break the ANSWER into a JSON array of atomic factual statements. "
                "Each statement must be self-contained and verifiable. "
                'Respond as {"statements": ["...", "..."]} with no other text.'
            ),
        },
        {"role": "user", "content": f"Question: {question}\nAnswer: {answer}"},
    ]
    res = await complete(extract, temperature=0.0, max_tokens=600, json_mode=True)
    statements = _parse_json(res.text, {"statements": []}).get("statements", [])
    statements = [s for s in statements if isinstance(s, str) and s.strip()]
    if not statements:
        return 0.0

    verdicts = [
        {
            "role": "system",
            "content": (
                "For each numbered statement decide if it can be directly inferred from the CONTEXT. "
                'Respond as JSON {"verdicts": [{"n": 1, "supported": true}, ...]} with no other text.'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Context:\n{context}\n\nStatements:\n"
                + "\n".join(f"{i + 1}. {s}" for i, s in enumerate(statements))
            ),
        },
    ]
    res = await complete(verdicts, temperature=0.0, max_tokens=600, json_mode=True)
    parsed = _parse_json(res.text, {"verdicts": []}).get("verdicts", [])
    supported = sum(1 for v in parsed if isinstance(v, dict) and v.get("supported"))
    return supported / len(statements)


# Metric 2 — Answer relevancy: the reverse-generation technique RAGAS itself uses. An
# LLM generates 3 questions that the answer would fully address; those are embedded and
# cosine-compared against the original question's embedding. Score = mean similarity —
# a high score means the answer is actually "about" what was asked, not just plausible text.
async def answer_relevancy(question: str, answer: str) -> float:
    gen = [
        {
            "role": "system",
            "content": (
                "Generate 3 questions that the given ANSWER would fully and directly answer. "
                'Respond as JSON {"questions": ["...", "...", "..."]} with no other text.'
            ),
        },
        {"role": "user", "content": f"Answer: {answer}"},
    ]
    res = await complete(gen, temperature=0.0, max_tokens=400, json_mode=True)
    generated = _parse_json(res.text, {"questions": []}).get("questions", [])
    generated = [q for q in generated if isinstance(q, str) and q.strip()]
    if not generated:
        return 0.0
    vectors = await asyncio.to_thread(embeddings.embed_texts, [question] + generated)
    q_vec, gen_vecs = vectors[0], vectors[1:]
    sims = [_cosine(q_vec, gv) for gv in gen_vecs]
    return sum(sims) / len(sims)


# Metric 3 — Context precision: an LLM judges each retrieved passage as relevant/not to
# the question, then scores with an average-precision-style formula that rewards
# relevant passages ranking earlier — measures retrieval quality independent of generation.
async def context_precision(question: str, chunks: list[dict]) -> float:
    if not chunks:
        return 0.0
    judge = [
        {
            "role": "system",
            "content": (
                "For each numbered passage decide if it is useful to answer the QUESTION. "
                'Respond as JSON {"verdicts": [{"n": 1, "relevant": true}, ...]} with no other text.'
            ),
        },
        {
            "role": "user",
            "content": (
                f"Question: {question}\n\nPassages:\n"
                + "\n\n".join(f"[{i + 1}] {c['content']}" for i, c in enumerate(chunks))
            ),
        },
    ]
    res = await complete(judge, temperature=0.0, max_tokens=200, json_mode=True)
    parsed = _parse_json(res.text, {"verdicts": []}).get("verdicts", [])
    by_n = {v.get("n"): bool(v.get("relevant")) for v in parsed if isinstance(v, dict)}
    relevances = [1 if by_n.get(i + 1) else 0 for i in range(len(chunks))]

    total_relevant = sum(relevances)
    if total_relevant == 0:
        return 0.0
    running = 0
    precision_sum = 0.0
    for k, rel in enumerate(relevances, start=1):
        if rel:
            running += 1
            precision_sum += running / k
    return precision_sum / total_relevant


# Top-level driver: seeds the corpus, runs the real pipeline + all three metrics for
# every question, prints a per-question and summary report, then always cleans up the
# seeded document (even on failure, via the finally block).
async def evaluate(questions: list[str]) -> None:
    async with AsyncSessionLocal() as session:
        print(f"Seeding evaluation corpus '{EVAL_FILENAME}' ({len(PAGES)} pages)...")
        document_id = await seed_document(session)

    rows: list[dict] = []
    try:
        for i, question in enumerate(questions, start=1):
            async with AsyncSessionLocal() as session:
                user = await get_local_user(session)
                bundle = await pipeline.research(session, user.id, question)
            context = bundle["context"]
            chunks = bundle["top_chunks"]

            answer = await generate_answer(question, context)
            faith = await faithfulness(question, answer, context)
            relevancy = await answer_relevancy(question, answer)
            precision = await context_precision(question, chunks)

            rows.append(
                {
                    "question": question,
                    "faithfulness": faith,
                    "answer_relevancy": relevancy,
                    "context_precision": precision,
                    "retrieved": len(chunks),
                }
            )
            print(
                f"[{i}/{len(questions)}] faith={faith:.2f} "
                f"relevancy={relevancy:.2f} precision={precision:.2f}  {question[:60]}"
            )
            await asyncio.sleep(2)
    finally:
        async with AsyncSessionLocal() as session:
            await cleanup_document(session, document_id)

    n = len(rows)
    avg = {
        m: sum(r[m] for r in rows) / n
        for m in ("faithfulness", "answer_relevancy", "context_precision")
    }
    print("\n" + "=" * 60)
    print("RAG EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Questions evaluated: {n}")
    print(f"Faithfulness      : {avg['faithfulness']:.3f}")
    print(f"Answer relevancy  : {avg['answer_relevancy']:.3f}")
    print(f"Context precision : {avg['context_precision']:.3f}")
    print("=" * 60)


# CLI entry point: `python -m app.eval.rag_eval [--limit N]`.
def main() -> None:
    parser = argparse.ArgumentParser(description="RAGAS-style evaluation of the Equity Prism RAG pipeline")
    parser.add_argument("--limit", type=int, default=len(QUESTIONS), help="number of questions to run")
    args = parser.parse_args()
    asyncio.run(evaluate(QUESTIONS[: args.limit]))


if __name__ == "__main__":
    main()

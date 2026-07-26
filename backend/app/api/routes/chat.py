import json
import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import synthesizer
from app.agents.graph import get_graph
from app.agents.snapshot import build_snapshot, resolve_symbols
from app.core.database import get_db
from app.llm.tracing import Tracer

router = APIRouter(prefix="/chat", tags=["chat"])

AGENTS_INFO = [
    {"id": "router", "name": "Router", "role": "Plans which specialists to run"},
    {"id": "company_analyst", "name": "Company Analyst", "role": "Deep single-stock analysis with bull/bear"},
    {"id": "comparator", "name": "Comparator", "role": "Side-by-side comparison of two or more stocks"},
    {"id": "sentiment", "name": "Sentiment", "role": "News-driven sentiment read"},
    {"id": "portfolio", "name": "Portfolio", "role": "Analyses the local portfolio holdings"},
    {"id": "document_research", "name": "Document Research", "role": "Answers from uploaded documents via RAG with citations"},
    {"id": "synthesizer", "name": "Synthesizer", "role": "Composes the final grounded answer"},
]


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    thread_id: str | None = None


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj, default=str)}\n\n"


def _compact_snapshot(snapshot: dict) -> dict:
    companies = {}
    for sym, co in snapshot.get("companies", {}).items():
        companies[sym] = {
            "name": co.get("name"),
            "sector": co.get("sector"),
            "current_price": co.get("current_price"),
            "has_metrics": co.get("metrics") is not None,
            "risk_score": (co.get("risk") or {}).get("score"),
            "news_count": len(co.get("news", []) or []),
        }
    return {
        "as_of": snapshot.get("as_of"),
        "symbols": snapshot.get("symbols", []),
        "companies": companies,
        "has_portfolio": bool(snapshot.get("portfolio")),
        "has_documents": bool(snapshot.get("has_documents")),
        "document_count": snapshot.get("document_count", 0),
    }


async def _run_graph(question: str, symbols: list[str], snapshot: dict, thread_id: str, tracer: Tracer):
    graph = get_graph()
    state = {
        "question": question,
        "symbols": symbols,
        "snapshot": snapshot,
        "fragments": [],
        "citations": [],
        "meta": [],
    }
    config = {"configurable": {"thread_id": thread_id, "tracer": tracer}}
    plan: dict = {}
    fragments: list[dict] = []
    citations: list[dict] = []
    agent_meta: list[dict] = []
    async for update in graph.astream(state, config=config, stream_mode="updates"):
        for node, payload in update.items():
            if not payload:
                continue
            if node == "router":
                plan = payload.get("plan", {})
                yield {"kind": "plan", "plan": plan}
            for frag in payload.get("fragments", []) or []:
                fragments.append(frag)
                yield {"kind": "fragment", "fragment": frag}
            for cit in payload.get("citations", []) or []:
                citations.append(cit)
            for m in payload.get("meta", []) or []:
                agent_meta.append(m)
    yield {"kind": "final", "plan": plan, "fragments": fragments, "citations": citations, "agent_meta": agent_meta}


@router.get("/agents")
async def agents() -> dict:
    return {"agents": AGENTS_INFO}


@router.post("/stream")
async def chat_stream(req: ChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    thread_id = req.thread_id or uuid.uuid4().hex
    symbols = await resolve_symbols(db, req.question)
    snapshot = await build_snapshot(db, symbols)

    async def generate():
        tracer = Tracer("chat", req.question, {"thread_id": thread_id, "symbols": symbols})
        yield _sse({"type": "status", "stage": "analyzing", "symbols": symbols, "thread_id": thread_id})
        yield _sse({"type": "snapshot", "snapshot": _compact_snapshot(snapshot)})

        fragments: list[dict] = []
        citations: list[dict] = []
        agent_meta: list[dict] = []
        async for ev in _run_graph(req.question, symbols, snapshot, thread_id, tracer):
            if ev["kind"] == "plan":
                yield _sse({"type": "plan", "plan": ev["plan"]})
            elif ev["kind"] == "fragment":
                frag = ev["fragment"]
                yield _sse({"type": "agent_result", "agent": frag["agent"], "title": frag["title"], "content": frag["content"]})
            elif ev["kind"] == "final":
                fragments = ev["fragments"]
                citations = ev["citations"]
                agent_meta = ev["agent_meta"]

        yield _sse({"type": "synthesis_start"})
        meta: dict = {}
        async for ev in synthesizer.stream(req.question, fragments, snapshot, tracer):
            if ev["type"] == "token":
                yield _sse({"type": "token", "content": ev["delta"]})
            elif ev["type"] == "meta":
                meta = ev["data"]

        tracer.flush()
        yield _sse(
            {
                "type": "done",
                "thread_id": thread_id,
                "agents": [f["agent"] for f in fragments],
                "citations": citations,
                "agent_meta": agent_meta,
                "synthesis": meta,
                "trace_id": tracer.id,
            }
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


@router.post("")
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)) -> dict:
    thread_id = req.thread_id or uuid.uuid4().hex
    symbols = await resolve_symbols(db, req.question)
    snapshot = await build_snapshot(db, symbols)
    tracer = Tracer("chat", req.question, {"thread_id": thread_id, "symbols": symbols})

    plan: dict = {}
    fragments: list[dict] = []
    citations: list[dict] = []
    agent_meta: list[dict] = []
    async for ev in _run_graph(req.question, symbols, snapshot, thread_id, tracer):
        if ev["kind"] == "final":
            plan = ev["plan"]
            fragments = ev["fragments"]
            citations = ev["citations"]
            agent_meta = ev["agent_meta"]

    result = await synthesizer.run(req.question, fragments, snapshot, tracer)
    tracer.flush()
    return {
        "thread_id": thread_id,
        "question": req.question,
        "symbols": symbols,
        "plan": plan,
        "answer": result.text,
        "fragments": fragments,
        "citations": citations,
        "agent_meta": agent_meta,
        "synthesis": {"model": result.model, "source": result.source, "latency_ms": result.latency_ms},
        "snapshot": _compact_snapshot(snapshot),
        "trace_id": tracer.id,
    }

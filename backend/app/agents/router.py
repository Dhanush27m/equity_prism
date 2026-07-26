import json

from app.llm.factory import complete

ALLOWED_AGENTS = {"company_analyst", "comparator", "sentiment", "portfolio", "document_research"}

ROUTER_SYS = (
    "You are the routing planner for an Indian-equity research assistant. "
    "Given a user question and context, decide which specialist agents should run. "
    "Available agents: "
    "company_analyst (deep single-stock analysis), "
    "comparator (compare two or more stocks), "
    "sentiment (news/market sentiment for the mentioned stocks), "
    "portfolio (analyse the user's holdings), "
    "document_research (answer from the user's uploaded documents/reports/filings via RAG). "
    "Rules: pick the smallest useful set. Use comparator only when 2+ symbols are present. "
    "Use company_analyst for single-stock depth. Add sentiment when the user asks about news, "
    "outlook, or recent developments. Only use portfolio when holdings exist. "
    "Use document_research when the user refers to an uploaded document/report/filing or asks a "
    "question that should be answered from documents, and documents are available. "
    'Respond with strict JSON: {"agents": ["..."], "reasoning": "one short sentence"}.'
)

SENTIMENT_HINTS = ("news", "sentiment", "outlook", "recent", "happening", "update", "latest", "buzz")
PORTFOLIO_HINTS = ("portfolio", "holding", "my stocks", "allocation", "p&l", "pnl", "profit", "invest")
DOCUMENT_HINTS = (
    "document", "report", "annual report", "filing", "pdf", "uploaded", "attachment",
    "transcript", "prospectus", "drhp", "10-k", "10k", "according to the",
)


def _deterministic_plan(question: str, symbols: list[str], snapshot: dict) -> dict:
    q = question.lower()
    agents: list[str] = []
    has_docs = bool(snapshot.get("has_documents"))
    if has_docs and any(h in q for h in DOCUMENT_HINTS):
        agents.append("document_research")
    if len(symbols) >= 2:
        agents.append("comparator")
    elif len(symbols) == 1:
        agents.append("company_analyst")
    if symbols and any(h in q for h in SENTIMENT_HINTS):
        agents.append("sentiment")
    if snapshot.get("portfolio") and any(h in q for h in PORTFOLIO_HINTS):
        agents.append("portfolio")
    if not agents:
        if symbols:
            agents.append("company_analyst")
        elif has_docs:
            agents.append("document_research")
    return {"agents": list(dict.fromkeys(agents)), "reasoning": "heuristic routing", "source": "deterministic"}


def _validate(agents: list[str], symbols: list[str], snapshot: dict) -> list[str]:
    out: list[str] = []
    for a in agents:
        if a not in ALLOWED_AGENTS:
            continue
        if a == "comparator" and len(symbols) < 2:
            continue
        if a == "company_analyst" and len(symbols) < 1:
            continue
        if a == "sentiment" and not symbols:
            continue
        if a == "portfolio" and not snapshot.get("portfolio"):
            continue
        if a == "document_research" and not snapshot.get("has_documents"):
            continue
        out.append(a)
    return list(dict.fromkeys(out))


async def run(state: dict, config: dict | None = None) -> dict:
    tracer = (config or {}).get("configurable", {}).get("tracer")
    question = state["question"]
    symbols = state.get("symbols", [])
    snapshot = state.get("snapshot", {})

    plan = _deterministic_plan(question, symbols, snapshot)

    try:
        context = {
            "symbols": symbols,
            "has_portfolio": bool(snapshot.get("portfolio")),
            "has_documents": bool(snapshot.get("has_documents")),
            "available_agents": sorted(ALLOWED_AGENTS),
        }
        messages = [
            {"role": "system", "content": ROUTER_SYS},
            {
                "role": "user",
                "content": f"User question: {question}\nContext: {json.dumps(context)}",
            },
        ]
        res = await complete(
            messages, temperature=0.0, max_tokens=250, json_mode=True, tracer=tracer, label="router"
        )
        obj = json.loads(res.text)
        agents = _validate(obj.get("agents", []), symbols, snapshot)
        if agents:
            plan = {
                "agents": agents,
                "reasoning": str(obj.get("reasoning", ""))[:280],
                "source": "llm",
            }
    except Exception:
        pass

    if tracer:
        tracer.event("router.plan", plan)
    return {"plan": plan}

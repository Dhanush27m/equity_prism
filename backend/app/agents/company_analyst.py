"""
Component: Backend -> AI Orchestration Layer -> Specialist agent (LangGraph node)
Belongs to: one of the five parallel specialists dispatched by the router.
Purpose: produces a bull/bear/verdict analysis of a single stock, grounded strictly in
the stored metrics + risk signals already pulled into the snapshot (never fetches or
invents its own numbers).
"""

import json

from app.llm.factory import complete

# System prompt: enforces the "only use snapshot numbers" grounding rule and the exact
# bull/bear/verdict markdown structure the synthesizer later expects to merge.
SYS = (
    "You are a sell-side equity research analyst covering Indian listed companies. "
    "Use ONLY the numbers in the verified data snapshot; never invent or estimate figures. "
    "If a metric is null or missing, write 'not available' rather than guessing. "
    "Ratios such as roe, roa, margins and dividend_yield are decimals (0.15 means 15%); "
    "debt_to_equity is already a percentage. "
    "Structure your answer in markdown as: a one-line summary, then **Bull case** (2-3 bullets), "
    "**Bear case** (2-3 bullets), then **Verdict** (2-3 balanced sentences; comment on valuation "
    "using P/E and P/B if available, and reference the risk signals). "
    "Keep it under 260 words. This is research, not personalised investment advice."
)


# LangGraph node entry point. No-ops (returns {}) if the router selected this agent
# without a resolved symbol, or if that symbol isn't in the snapshot. Otherwise calls the
# LLM with only that company's data and returns a fragment + citation + call metadata for
# the reducers in AgentState to merge in.
async def run(state: dict, config: dict | None = None) -> dict:
    tracer = (config or {}).get("configurable", {}).get("tracer")
    symbols = state.get("symbols", [])
    snapshot = state.get("snapshot", {})
    if not symbols:
        return {}
    sym = symbols[0]
    company = snapshot.get("companies", {}).get(sym)
    if not company:
        return {}

    context = json.dumps({sym: {k: v for k, v in company.items() if k != "news"}}, default=str)
    messages = [
        {"role": "system", "content": SYS},
        {
            "role": "user",
            "content": (
                f"Question: {state['question']}\n\n"
                f"Verified data snapshot (the only source of numbers):\n{context}\n\n"
                f"Analyse {sym} ({company.get('name')})."
            ),
        },
    ]
    res = await complete(messages, temperature=0.3, max_tokens=900, tracer=tracer, label="company_analyst")
    return {
        "fragments": [
            {"agent": "company_analyst", "title": f"Company analysis — {sym}", "content": res.text}
        ],
        "meta": [
            {"agent": "company_analyst", "model": res.model, "source": res.source, "latency_ms": res.latency_ms}
        ],
        "citations": [
            {"agent": "company_analyst", "type": "financials", "label": f"{sym} stored metrics & risk signals"}
        ],
    }

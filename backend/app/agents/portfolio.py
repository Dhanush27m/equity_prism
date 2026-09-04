"""
Component: Backend -> AI Orchestration Layer -> Specialist agent (LangGraph node)
Belongs to: one of the five parallel specialists dispatched by the router.
Purpose: reviews the local user's actual holdings (already priced into the snapshot) —
overall P&L, biggest winners/losers, concentration risk — without ever recommending a
specific buy/sell action.
"""

import json

from app.llm.factory import complete

# System prompt: explicitly forbids buy/sell recommendations, restricts the model to the
# supplied portfolio numbers only.
SYS = (
    "You are a portfolio analyst reviewing a retail investor's holdings. Use ONLY the supplied portfolio "
    "snapshot numbers; never invent figures. Cover: overall P&L (absolute and %), the biggest winners and "
    "losers by position, and concentration/diversification observations (single-name or sector weight). "
    "Give 2-3 balanced, data-grounded observations. Do not tell the user to buy or sell specific stocks; "
    "frame everything as research and note this is not personalised financial advice. "
    "Format as markdown under 240 words."
)


# LangGraph node entry point. No-ops if the local user has no holdings (snapshot.portfolio
# is None) — the router should already have excluded this agent in that case, this is the
# defensive second check.
async def run(state: dict, config: dict | None = None) -> dict:
    tracer = (config or {}).get("configurable", {}).get("tracer")
    portfolio = state.get("snapshot", {}).get("portfolio")
    if not portfolio:
        return {}

    context = json.dumps(portfolio, default=str)
    messages = [
        {"role": "system", "content": SYS},
        {
            "role": "user",
            "content": f"Question: {state['question']}\n\nPortfolio snapshot:\n{context}",
        },
    ]
    res = await complete(messages, temperature=0.3, max_tokens=800, tracer=tracer, label="portfolio")
    return {
        "fragments": [{"agent": "portfolio", "title": "Portfolio review", "content": res.text}],
        "meta": [{"agent": "portfolio", "model": res.model, "source": res.source, "latency_ms": res.latency_ms}],
        "citations": [{"agent": "portfolio", "type": "portfolio", "label": "Local portfolio holdings"}],
    }

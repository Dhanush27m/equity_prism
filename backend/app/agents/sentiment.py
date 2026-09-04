"""
Component: Backend -> AI Orchestration Layer -> Specialist agent (LangGraph node)
Belongs to: one of the five parallel specialists dispatched by the router.
Purpose: reads the recent news headlines already fetched into the snapshot and judges
sentiment (Positive/Neutral/Negative/Mixed) per symbol — never invents events or prices,
only reasons over the supplied headline titles/sources.
"""

import json

from app.llm.factory import complete

# System prompt: restricts the model to judging sentiment from the supplied headlines only.
SYS = (
    "You are a market-sentiment analyst. You are given recent news headlines for one or more Indian "
    "listed companies. Judge sentiment ONLY from the supplied headlines; do not invent events or prices. "
    "For each company give an overall sentiment label (Positive / Neutral / Negative / Mixed), 2-3 key "
    "themes drawn from the headlines, and note any headline that is clearly material. Reference headlines "
    "by their title. If there are no headlines for a company, say sentiment is inconclusive. "
    "Format as markdown, under 220 words. This is research, not investment advice."
)


# LangGraph node entry point. Builds a per-symbol headline payload from the snapshot's
# already-fetched news, also collects up to 3 headline links per symbol as citations.
# No-ops if none of the resolved symbols have any news attached.
async def run(state: dict, config: dict | None = None) -> dict:
    tracer = (config or {}).get("configurable", {}).get("tracer")
    symbols = state.get("symbols", [])
    companies = state.get("snapshot", {}).get("companies", {})

    payload: dict = {}
    citations: list[dict] = []
    for sym in symbols:
        articles = companies.get(sym, {}).get("news", []) or []
        payload[sym] = [{"title": a.get("title"), "source": a.get("source")} for a in articles]
        for a in articles[:3]:
            if a.get("link"):
                citations.append(
                    {"agent": "sentiment", "type": "news", "label": a.get("title"), "url": a.get("link")}
                )
    if not payload:
        return {}

    context = json.dumps(payload, default=str)
    messages = [
        {"role": "system", "content": SYS},
        {
            "role": "user",
            "content": f"Question: {state['question']}\n\nRecent headlines by symbol:\n{context}",
        },
    ]
    res = await complete(messages, temperature=0.3, max_tokens=700, tracer=tracer, label="sentiment")
    return {
        "fragments": [{"agent": "sentiment", "title": "News & sentiment", "content": res.text}],
        "meta": [{"agent": "sentiment", "model": res.model, "source": res.source, "latency_ms": res.latency_ms}],
        "citations": citations,
    }

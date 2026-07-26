import json

from app.llm.factory import complete

SYS = (
    "You are an equity strategist comparing Indian listed companies for a research client. "
    "Use ONLY the numbers in the verified data snapshot; never invent figures. Missing metrics are "
    "'not available'. Ratios such as roe, roa, margins and dividend_yield are decimals (0.15 = 15%); "
    "debt_to_equity is already a percentage. "
    "Structure in markdown: a one-line takeaway, then a compact comparison across Valuation (P/E, P/B), "
    "Profitability (ROE, margins), Leverage (D/E), and Growth (revenue/earnings growth) — a short "
    "markdown table is ideal. Then **Bull/Bear** one line each per company, and a **Relative verdict** "
    "naming which screens better on the data and the key caveats. Under 300 words. "
    "This is research, not personalised investment advice."
)


async def run(state: dict, config: dict | None = None) -> dict:
    tracer = (config or {}).get("configurable", {}).get("tracer")
    symbols = state.get("symbols", [])
    snapshot = state.get("snapshot", {})
    companies = snapshot.get("companies", {})
    subset = {s: {k: v for k, v in companies[s].items() if k != "news"} for s in symbols if s in companies}
    if len(subset) < 2:
        return {}

    context = json.dumps(subset, default=str)
    messages = [
        {"role": "system", "content": SYS},
        {
            "role": "user",
            "content": (
                f"Question: {state['question']}\n\n"
                f"Verified data snapshot (the only source of numbers):\n{context}\n\n"
                f"Compare: {', '.join(subset.keys())}."
            ),
        },
    ]
    res = await complete(messages, temperature=0.3, max_tokens=1100, tracer=tracer, label="comparator")
    return {
        "fragments": [
            {"agent": "comparator", "title": f"Comparison — {' vs '.join(subset.keys())}", "content": res.text}
        ],
        "meta": [
            {"agent": "comparator", "model": res.model, "source": res.source, "latency_ms": res.latency_ms}
        ],
        "citations": [
            {"agent": "comparator", "type": "financials", "label": f"Stored metrics for {', '.join(subset.keys())}"}
        ],
    }

import json

from app.llm.factory import complete

SYS = (
    "You are a portfolio analyst reviewing a retail investor's holdings. Use ONLY the supplied portfolio "
    "snapshot numbers; never invent figures. Cover: overall P&L (absolute and %), the biggest winners and "
    "losers by position, and concentration/diversification observations (single-name or sector weight). "
    "Give 2-3 balanced, data-grounded observations. Do not tell the user to buy or sell specific stocks; "
    "frame everything as research and note this is not personalised financial advice. "
    "Format as markdown under 240 words."
)


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

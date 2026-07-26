from app.llm.factory import complete, stream_complete

SYS = (
    "You are the lead analyst composing the final answer for a user of an equity research tool. "
    "Combine the specialist notes below into one cohesive, well-structured markdown answer. "
    "Rules: rely ONLY on the specialist notes and the verified data they cite; do not introduce new "
    "numbers or facts. Open with a direct 1-2 sentence answer to the user's question, then organised "
    "supporting detail with headings, then a short 'Data & sources' line describing what the answer is "
    "based on. Be balanced. End with a one-line disclaimer that this is research, not personalised "
    "investment advice. Keep it tight and readable."
)

GENERAL_SYS = (
    "You are a knowledgeable assistant for an Indian-equity research tool. The user's question did not "
    "map to a specific tracked NSE company. Answer the question helpfully and concisely from general "
    "financial knowledge, note that no specific tracked company was detected, and add a one-line "
    "disclaimer that this is educational information, not personalised investment advice."
)


def _build_messages(question: str, fragments: list[dict], snapshot: dict) -> list[dict]:
    if not fragments:
        return [
            {"role": "system", "content": GENERAL_SYS},
            {"role": "user", "content": question},
        ]
    notes = "\n\n".join(f"### {f['title']} (from {f['agent']})\n{f['content']}" for f in fragments)
    symbols = ", ".join(snapshot.get("symbols", [])) or "none"
    user = (
        f"User question: {question}\n\n"
        f"Symbols in scope: {symbols}\n\n"
        f"Specialist notes:\n{notes}"
    )
    return [
        {"role": "system", "content": SYS},
        {"role": "user", "content": user},
    ]


async def run(question: str, fragments: list[dict], snapshot: dict, tracer=None):
    messages = _build_messages(question, fragments, snapshot)
    return await complete(messages, temperature=0.3, max_tokens=1536, tracer=tracer, label="synthesizer")


async def stream(question: str, fragments: list[dict], snapshot: dict, tracer=None):
    messages = _build_messages(question, fragments, snapshot)
    async for ev in stream_complete(messages, temperature=0.3, max_tokens=1536, tracer=tracer, label="synthesizer"):
        yield ev

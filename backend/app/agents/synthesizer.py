"""
Component: Backend -> AI Orchestration Layer (LangGraph)
Belongs to: the final step of the chat pipeline, run after all specialist nodes finish.
Purpose: merges every specialist's fragment into one final, cohesive markdown answer.
Runs outside the LangGraph graph itself (called directly by the chat route) since it
needs to run once, after fan-out completes, not as a parallel graph node.
"""

from app.llm.factory import complete, stream_complete

# System prompt used when at least one specialist produced a fragment: combine notes,
# stay grounded in only what those notes say, end with the standard disclaimer.
SYS = (
    "You are the lead analyst composing the final answer for a user of an equity research tool. "
    "Combine the specialist notes below into one cohesive, well-structured markdown answer. "
    "Rules: rely ONLY on the specialist notes and the verified data they cite; do not introduce new "
    "numbers or facts. Open with a direct 1-2 sentence answer to the user's question, then organised "
    "supporting detail with headings, then a short 'Data & sources' line describing what the answer is "
    "based on. Be balanced. End with a one-line disclaimer that this is research, not personalised "
    "investment advice. Keep it tight and readable."
)

# System prompt used when the router found no relevant tracked company/data at all —
# answers from general knowledge instead of specialist notes.
GENERAL_SYS = (
    "You are a knowledgeable assistant for an Indian-equity research tool. The user's question did not "
    "map to a specific tracked NSE company. Answer the question helpfully and concisely from general "
    "financial knowledge, note that no specific tracked company was detected, and add a one-line "
    "disclaimer that this is educational information, not personalised investment advice."
)


# Builds the message list for the final LLM call: general fallback prompt if there are no
# specialist fragments, otherwise the grounded-synthesis prompt with all fragments serialized in.
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


# Non-streaming synthesis — used by the plain (non-SSE) POST /api/chat endpoint.
async def run(question: str, fragments: list[dict], snapshot: dict, tracer=None):
    messages = _build_messages(question, fragments, snapshot)
    return await complete(messages, temperature=0.3, max_tokens=1536, tracer=tracer, label="synthesizer")


# Streaming synthesis — used by POST /api/chat/stream to forward tokens over SSE as they
# are generated instead of waiting for the full answer.
async def stream(question: str, fragments: list[dict], snapshot: dict, tracer=None):
    messages = _build_messages(question, fragments, snapshot)
    async for ev in stream_complete(messages, temperature=0.3, max_tokens=1536, tracer=tracer, label="synthesizer"):
        yield ev

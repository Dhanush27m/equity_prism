"""
Component: Backend -> LLM Layer -> Observability
Belongs to: called from every LLM call site (llm/factory.py, agents/*, eval/rag_eval.py)
via the optional `tracer` argument threaded through the chat request.
Purpose: an optional, fully no-op-safe wrapper around LangFuse Cloud tracing. When
LANGFUSE_PUBLIC_KEY/SECRET_KEY are unset it silently does nothing (trace.id stays null);
when set, it logs every generation's model, tokens, latency, and an estimated USD cost.
"""

from app.core.config import get_settings

settings = get_settings()

_client = None
_resolved = False

# Hardcoded Groq per-model pricing (USD per 1M tokens) used to estimate generation cost
# in the LangFuse dashboard — Groq's API does not return cost directly.
MODEL_PRICING_USD_PER_1M = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
}


# Estimates USD cost for one generation from its token counts and the pricing table
# above; returns None for an unknown model rather than guessing a price.
def _cost(model: str, prompt_tokens: int, completion_tokens: int) -> dict | None:
    price = MODEL_PRICING_USD_PER_1M.get(model)
    if not price:
        return None
    input_cost = prompt_tokens / 1_000_000 * price["input"]
    output_cost = completion_tokens / 1_000_000 * price["output"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost,
    }


# Lazily constructs (once, memoized) the LangFuse client, or returns None if keys are
# unset or the LangFuse import/connection fails — every caller downstream treats a None
# client as "tracing disabled" rather than raising.
def _get_client():
    global _client, _resolved
    if _resolved:
        return _client
    _resolved = True
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    try:
        from langfuse import Langfuse

        _client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    except Exception:
        _client = None
    return _client


# One Tracer instance is created per chat/eval request and threaded through every LLM
# call site. Every method is wrapped in try/except so a LangFuse outage or SDK error can
# never break the actual chat request it's tracing.
class Tracer:
    def __init__(self, name: str, user_input, metadata: dict | None = None):
        self.client = _get_client()
        self.trace = None
        if self.client:
            try:
                self.trace = self.client.trace(name=name, input=user_input, metadata=metadata or {})
            except Exception:
                self.trace = None

    # True only when a real LangFuse trace was successfully opened.
    @property
    def enabled(self) -> bool:
        return self.trace is not None

    # The LangFuse trace id (surfaced to the frontend as `trace_id`), or None if disabled.
    @property
    def id(self):
        return getattr(self.trace, "id", None)

    # Logs one LLM call (prompt, output, token usage, latency, estimated cost) as a
    # generation nested under this request's trace.
    def generation(
        self,
        name: str,
        model: str,
        prompt,
        output,
        metadata: dict | None = None,
        usage: dict | None = None,
        latency_ms: int | None = None,
    ) -> None:
        if not self.trace:
            return
        try:
            meta = dict(metadata or {})
            if latency_ms is not None:
                meta["latency_ms"] = latency_ms
            kwargs: dict = {"name": name, "model": model, "input": prompt, "metadata": meta}
            if usage:
                prompt_tokens = usage.get("prompt_tokens") or 0
                completion_tokens = usage.get("completion_tokens") or 0
                usage_payload: dict = {
                    "input": prompt_tokens,
                    "output": completion_tokens,
                    "total": usage.get("total_tokens") or (prompt_tokens + completion_tokens),
                    "unit": "TOKENS",
                }
                cost = _cost(model, prompt_tokens, completion_tokens)
                if cost:
                    usage_payload.update(cost)
                kwargs["usage"] = usage_payload
            gen = self.trace.generation(**kwargs)
            gen.end(output=output)
        except Exception:
            pass

    # Logs a discrete, non-generation event (e.g. the router's chosen plan) on the trace.
    def event(self, name: str, data) -> None:
        if not self.trace:
            return
        try:
            self.trace.event(name=name, input=data)
        except Exception:
            pass

    # Attaches/overwrites the trace's overall output (e.g. the final synthesized answer).
    def update(self, output) -> None:
        if not self.trace:
            return
        try:
            self.trace.update(output=output)
        except Exception:
            pass

    # Flushes buffered trace data to LangFuse Cloud — called once at the end of a request
    # so tracing data isn't lost if the process exits before its background flush timer fires.
    def flush(self) -> None:
        if self.client:
            try:
                self.client.flush()
            except Exception:
                pass

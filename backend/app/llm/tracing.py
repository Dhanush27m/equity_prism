from app.core.config import get_settings

settings = get_settings()

_client = None
_resolved = False

MODEL_PRICING_USD_PER_1M = {
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
}


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


class Tracer:
    def __init__(self, name: str, user_input, metadata: dict | None = None):
        self.client = _get_client()
        self.trace = None
        if self.client:
            try:
                self.trace = self.client.trace(name=name, input=user_input, metadata=metadata or {})
            except Exception:
                self.trace = None

    @property
    def enabled(self) -> bool:
        return self.trace is not None

    @property
    def id(self):
        return getattr(self.trace, "id", None)

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

    def event(self, name: str, data) -> None:
        if not self.trace:
            return
        try:
            self.trace.event(name=name, input=data)
        except Exception:
            pass

    def update(self, output) -> None:
        if not self.trace:
            return
        try:
            self.trace.update(output=output)
        except Exception:
            pass

    def flush(self) -> None:
        if self.client:
            try:
                self.client.flush()
            except Exception:
                pass

"""
Component: Backend -> LLM Layer
Belongs to: the single choke point every agent, the router, and the synthesizer call
through (app/agents/*.py all import `complete`/`stream_complete` from here — nothing
calls Ollama or Groq directly).
Purpose: a minimal (httpx-based, no SDK) chat-completion client with a provider fallback
chain (Ollama first, Groq second) and retry-with-backoff, in both non-streaming and
streaming (SSE) forms.
"""

import asyncio
import json
import time
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

settings = get_settings()

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MAX_ATTEMPTS = 3


# Uniform result shape returned by complete() regardless of which provider answered.
@dataclass
class LLMResult:
    text: str
    model: str
    source: str
    latency_ms: int
    usage: dict | None = None


# One non-streaming call to Groq's OpenAI-compatible chat-completions endpoint.
async def _groq(messages: list[dict], temperature: float, max_tokens: int, json_mode: bool) -> tuple[str, dict]:
    payload: dict = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(GROQ_URL, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"] or ""
        return text, data.get("usage") or {}


# One non-streaming call to a local/self-hosted Ollama instance — the fallback path used
# when Groq is unavailable. In the deployed environment there is no reachable Ollama host,
# so this fails fast in production; it is a live path only in the local/self-hosted profile.
async def _ollama(messages: list[dict], temperature: float, max_tokens: int, json_mode: bool) -> tuple[str, dict]:
    payload: dict = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    if json_mode:
        payload["format"] = "json"
    async with httpx.AsyncClient(timeout=300) as client:
        r = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
        r.raise_for_status()
        data = r.json()
        text = data["message"]["content"] or ""
        usage = {
            "prompt_tokens": data.get("prompt_eval_count"),
            "completion_tokens": data.get("eval_count"),
        }
        return text, usage


async def complete(
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int = 1024,
    json_mode: bool = False,
    tracer=None,
    label: str = "llm",
) -> LLMResult:
    start = time.monotonic()
    errors: list[str] = []

    for attempt in range(MAX_ATTEMPTS):
        try:
            text, usage = await _ollama(messages, temperature, max_tokens, json_mode)
            latency = int((time.monotonic() - start) * 1000)
            result = LLMResult(text, settings.ollama_model, "ollama", latency, usage)
            if tracer:
                tracer.generation(label, result.model, messages, text, usage=usage, latency_ms=latency)
            return result
        except Exception as exc:
            errors.append(f"ollama({attempt}): {exc}")
            await asyncio.sleep(2**attempt)

    if settings.groq_api_key:
        for attempt in range(MAX_ATTEMPTS):
            try:
                text, usage = await _groq(messages, temperature, max_tokens, json_mode)
                latency = int((time.monotonic() - start) * 1000)
                result = LLMResult(text, settings.groq_model, "groq", latency, usage)
                if tracer:
                    tracer.generation(label, result.model, messages, text, usage=usage, latency_ms=latency)
                return result
            except Exception as exc:
                errors.append(f"groq({attempt}): {exc}")
                await asyncio.sleep(2**attempt)

    raise RuntimeError("LLM unavailable: " + " | ".join(errors[-4:]))


# Streams one Groq chat-completion response as an async generator of raw text deltas,
# parsing Groq's Server-Sent-Events wire format line by line; captures token usage from
# the final SSE chunk into usage_sink (mutated in place) since Groq only reports it there.
async def _groq_stream(messages: list[dict], temperature: float, max_tokens: int, usage_sink: dict):
    payload = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }
    headers = {"Authorization": f"Bearer {settings.groq_api_key}"}
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", GROQ_URL, json=payload, headers=headers) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if obj.get("usage"):
                    usage_sink.update(obj["usage"])
                choices = obj.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta", {}).get("content")
                if delta:
                    yield delta


# Streams one Ollama chat response the same way, for the fallback path.
async def _ollama_stream(messages: list[dict], temperature: float, max_tokens: int):
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": temperature, "num_predict": max_tokens},
    }
    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream("POST", f"{settings.ollama_base_url}/api/chat", json=payload) as r:
            r.raise_for_status()
            async for line in r.aiter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                delta = obj.get("message", {}).get("content")
                if delta:
                    yield delta
                if obj.get("done"):
                    break


async def stream_complete(
    messages: list[dict],
    *,
    temperature: float = 0.3,
    max_tokens: int = 1536,
    tracer=None,
    label: str = "synthesizer",
):
    collected: list[str] = []
    source: str | None = None
    model: str | None = None
    usage: dict = {}
    start = time.monotonic()

    started = False
    try:
        async for delta in _ollama_stream(messages, temperature, max_tokens):
            started = True
            collected.append(delta)
            yield {"type": "token", "delta": delta}
        source, model = "ollama", settings.ollama_model
    except Exception:
        if started:
            source, model = "ollama", settings.ollama_model
        else:
            collected.clear()

    if source is None and settings.groq_api_key:
        try:
            async for delta in _groq_stream(messages, temperature, max_tokens, usage):
                collected.append(delta)
                yield {"type": "token", "delta": delta}
            source, model = "groq", settings.groq_model
        except Exception as exc:
            yield {"type": "token", "delta": f"\n\n_(generation error: {exc})_"}
            source, model = "error", None

    if source is None:
        yield {"type": "token", "delta": "\n\n_(LLM unavailable — is Ollama running?)_"}
        source, model = "error", None

    text = "".join(collected)
    latency = int((time.monotonic() - start) * 1000)
    if tracer and model:
        tracer.generation(label, model, messages, text, usage=usage or None, latency_ms=latency)
    yield {"type": "meta", "data": {"model": model, "source": source, "chars": len(text), "latency_ms": latency}}

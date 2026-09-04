"""
Component: Backend -> Core -> Security
Belongs to: installed as FastAPI middleware from main.py (registered before the
observability middleware so a real request_id exists on 401 responses).
Purpose: a shared-password gate protecting every /api/* route (except /api/health) with
a single ACCESS_KEY, so a deployed demo doesn't burn the owner's Groq quota / expose
Supabase data to anyone who finds the URL. This is NOT a multi-user auth system — every
caller behind the gate shares the same "local" user's data.
"""

import hmac

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

settings = get_settings()

# Paths that skip the access-key check even when a key is configured.
EXEMPT_PATHS = {"/api/health"}


# Registers the access-key middleware — a no-op if ACCESS_KEY is unset (local dev).
def install(app: FastAPI) -> None:
    if not settings.access_key:
        return

    # Rejects any /api/* request (other than OPTIONS preflights and EXEMPT_PATHS) whose
    # X-Access-Key header doesn't match. Uses hmac.compare_digest instead of `!=` so the
    # comparison is constant-time and not vulnerable to a timing side-channel.
    @app.middleware("http")
    async def access_gate(request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or not path.startswith("/api") or path in EXEMPT_PATHS:
            return await call_next(request)
        provided = request.headers.get("x-access-key", "")
        if not hmac.compare_digest(provided, settings.access_key):
            request_id = getattr(request.state, "request_id", "-")
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "status": 401,
                        "message": "Invalid or missing access key",
                        "request_id": request_id,
                    }
                },
            )
        return await call_next(request)

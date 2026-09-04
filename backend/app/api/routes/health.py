"""
Component: Backend -> API Layer -> Health check
Belongs to: the one route exempt from the access-key gate (core/auth.py's
EXEMPT_PATHS) and from the keep-alive pinger's warm-up check.
Purpose: a liveness probe — confirms the process is up and answering HTTP, without
touching the database (so it stays fast/cheap and works even if Supabase is paused).
"""

from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


# Plain liveness check — no DB query, so it succeeds even when the database is
# unreachable (which is exactly when you most need to be able to tell the backend itself
# is still up).
@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "equity-prism-backend", "env": settings.app_env}

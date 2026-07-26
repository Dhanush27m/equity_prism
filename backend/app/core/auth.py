from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import get_settings

settings = get_settings()

EXEMPT_PATHS = {"/api/health"}


def install(app: FastAPI) -> None:
    if not settings.access_key:
        return

    @app.middleware("http")
    async def access_gate(request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS" or not path.startswith("/api") or path in EXEMPT_PATHS:
            return await call_next(request)
        provided = request.headers.get("x-access-key", "")
        if provided != settings.access_key:
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

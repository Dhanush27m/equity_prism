"""
Component: Backend -> Core -> Observability
Belongs to: installed as FastAPI middleware + exception handlers from main.py.
Purpose: gives every request a short correlation id (X-Request-ID), logs method/path/
status/latency for each one, and normalizes every error response (validation, HTTP,
unhandled) into one consistent JSON envelope: {"error": {status, message, request_id}}.
"""

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import get_settings

settings = get_settings()

logger = logging.getLogger("equity_prism")


# One-time root logger setup, driven by LOG_LEVEL.
def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.setLevel(level)


# Builds the standard error response body every handler below returns.
def _error_body(status_code: int, message: str, request_id: str, detail=None) -> dict:
    body = {"error": {"status": status_code, "message": message, "request_id": request_id}}
    if detail is not None:
        body["error"]["detail"] = detail
    return body


# Registers the request-logging middleware and the three exception handlers below.
def install(app: FastAPI) -> None:
    configure_logging()

    # Generates a per-request id, stores it on request.state (read back by other
    # middleware/handlers for correlation), logs the outcome, and echoes it as an
    # X-Request-ID response header. Also catches any exception that slips past FastAPI's
    # own handling and turns it into a clean 500 instead of a raw traceback response.
    @app.middleware("http")
    async def request_logger(request: Request, call_next):
        request_id = uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.monotonic()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = (time.monotonic() - start) * 1000
            logger.exception(
                "unhandled error rid=%s %s %s (%.0fms)",
                request_id,
                request.method,
                request.url.path,
                elapsed,
            )
            return JSONResponse(
                status_code=500,
                content=_error_body(500, "Internal server error", request_id),
            )
        elapsed = (time.monotonic() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "rid=%s %s %s -> %s (%.0fms)",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response

    # Normalizes any raised HTTPException (e.g. route-level 404s) into the standard envelope.
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", "-")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.status_code, str(exc.detail), request_id),
        )

    # Normalizes Pydantic/FastAPI request validation failures (422) into the standard envelope.
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "-")
        return JSONResponse(
            status_code=422,
            content=_error_body(
                422, "Request validation failed", request_id, detail=jsonable_encoder(exc.errors())
            ),
        )

    # Catch-all for any other unhandled exception raised inside a route.
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "-")
        logger.exception("unhandled exception rid=%s: %s", request_id, exc)
        return JSONResponse(
            status_code=500,
            content=_error_body(500, "Internal server error", request_id),
        )

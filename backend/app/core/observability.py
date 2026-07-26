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


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.setLevel(level)


def _error_body(status_code: int, message: str, request_id: str, detail=None) -> dict:
    body = {"error": {"status": status_code, "message": message, "request_id": request_id}}
    if detail is not None:
        body["error"]["detail"] = detail
    return body


def install(app: FastAPI) -> None:
    configure_logging()

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

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        request_id = getattr(request.state, "request_id", "-")
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.status_code, str(exc.detail), request_id),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        request_id = getattr(request.state, "request_id", "-")
        return JSONResponse(
            status_code=422,
            content=_error_body(
                422, "Request validation failed", request_id, detail=jsonable_encoder(exc.errors())
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        request_id = getattr(request.state, "request_id", "-")
        logger.exception("unhandled exception rid=%s: %s", request_id, exc)
        return JSONResponse(
            status_code=500,
            content=_error_body(500, "Internal server error", request_id),
        )

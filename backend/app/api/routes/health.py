from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "equity-prism-backend", "env": settings.app_env}

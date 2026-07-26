import asyncio

from fastapi import APIRouter

from app.services.market_data import get_indices

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/indices")
async def indices() -> dict:
    data = await asyncio.to_thread(get_indices)
    return {"indices": data}

import asyncio

from fastapi import APIRouter, Query

from app.services.news import get_news

router = APIRouter(prefix="/news", tags=["news"])


@router.get("/{symbol}")
async def news(symbol: str, limit: int = Query(default=20, ge=1, le=50)) -> dict:
    articles = await asyncio.to_thread(get_news, symbol.upper(), None, limit)
    return {"symbol": symbol.upper(), "count": len(articles), "articles": articles}

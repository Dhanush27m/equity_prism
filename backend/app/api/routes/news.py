"""
Component: Backend -> API Layer -> News
Belongs to: the News page's headline feed for a given symbol.
Purpose: a thin HTTP wrapper around services/news.get_news (Google News RSS), the same
function the sentiment specialist agent's snapshot data comes from.
"""

import asyncio

from fastapi import APIRouter, Query

from app.services.news import get_news

router = APIRouter(prefix="/news", tags=["news"])


# Returns recent, relevance-scored news articles for a symbol. Runs the synchronous RSS
# fetch/parse in a worker thread so it doesn't block the event loop.
@router.get("/{symbol}")
async def news(symbol: str, limit: int = Query(default=20, ge=1, le=50)) -> dict:
    articles = await asyncio.to_thread(get_news, symbol.upper(), None, limit)
    return {"symbol": symbol.upper(), "count": len(articles), "articles": articles}

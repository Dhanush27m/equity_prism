"""
Component: Backend -> API Layer -> Market indices
Belongs to: the Dashboard page's index cards (NIFTY 50, SENSEX, BANK NIFTY, INDIA VIX).
Purpose: a thin HTTP wrapper around services/market_data.get_indices — always fetched
live from yfinance (index levels change continuously, so there's no stored/cached copy).
"""

import asyncio

from fastapi import APIRouter

from app.services.market_data import get_indices

router = APIRouter(prefix="/market", tags=["market"])


# Returns current levels for the tracked indices. Runs the synchronous yfinance call in
# a worker thread (asyncio.to_thread) so it doesn't block the event loop.
@router.get("/indices")
async def indices() -> dict:
    data = await asyncio.to_thread(get_indices)
    return {"indices": data}

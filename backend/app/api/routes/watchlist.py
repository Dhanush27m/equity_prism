"""
Component: Backend -> API Layer -> Watchlist
Belongs to: the Dashboard's watchlist card and the Company/Screener pages' "watch" star.
Purpose: CRUD for the local user's tracked-symbols list, enriched with each symbol's
current price/market cap/P-E/ROE/risk score from stored data for display.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_local_user
from app.core.database import get_db
from app.models import Company, FinancialMetric, RiskSignal, WatchlistItem

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


class WatchlistAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)


# Lists the local user's watchlist, joining in each symbol's company/metric/risk data
# for the summary card shown on the dashboard.
@router.get("")
async def list_watchlist(db: AsyncSession = Depends(get_db)) -> dict:
    user = await get_local_user(db)
    items = (
        await db.execute(
            select(WatchlistItem).where(WatchlistItem.user_id == user.id).order_by(WatchlistItem.created_at)
        )
    ).scalars().all()
    out: list[dict] = []
    for item in items:
        company = (
            await db.execute(select(Company).where(Company.symbol == item.symbol))
        ).scalar_one_or_none()
        metric = None
        risk = None
        if company is not None:
            metric = (
                await db.execute(select(FinancialMetric).where(FinancialMetric.company_id == company.id))
            ).scalar_one_or_none()
            risk = (
                await db.execute(select(RiskSignal).where(RiskSignal.company_id == company.id))
            ).scalar_one_or_none()
        out.append(
            {
                "id": item.id,
                "symbol": item.symbol,
                "name": company.name if company else item.symbol,
                "sector": company.sector if company else None,
                "current_price": company.current_price if company else None,
                "market_cap": company.market_cap if company else None,
                "pe": metric.pe if metric else None,
                "roe": metric.roe if metric else None,
                "risk_score": risk.score if risk else None,
            }
        )
    return {"items": out}


# Adds a symbol to the watchlist; idempotent — returns status="exists" instead of
# creating a duplicate row if it's already there.
@router.post("", status_code=201)
async def add_watchlist(payload: WatchlistAdd, db: AsyncSession = Depends(get_db)) -> dict:
    user = await get_local_user(db)
    symbol = payload.symbol.upper()
    company = (await db.execute(select(Company).where(Company.symbol == symbol))).scalar_one_or_none()
    existing = (
        await db.execute(
            select(WatchlistItem).where(
                WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        return {"id": existing.id, "symbol": symbol, "status": "exists"}
    item = WatchlistItem(user_id=user.id, symbol=symbol, company_id=company.id if company else None)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": item.id, "symbol": symbol, "status": "added"}


# Removes a symbol from the watchlist.
@router.delete("/{symbol}", status_code=204)
async def remove_watchlist(symbol: str, db: AsyncSession = Depends(get_db)) -> None:
    user = await get_local_user(db)
    item = (
        await db.execute(
            select(WatchlistItem).where(
                WatchlistItem.user_id == user.id, WatchlistItem.symbol == symbol.upper()
            )
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Not in watchlist")
    await db.delete(item)
    await db.commit()

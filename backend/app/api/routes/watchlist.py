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

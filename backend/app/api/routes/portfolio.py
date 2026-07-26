from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_local_user
from app.core.database import get_db
from app.models import Company, PortfolioHolding

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


class HoldingAdd(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    quantity: float = Field(gt=0)
    avg_price: float = Field(gt=0)


async def _build(db: AsyncSession, user_id: int) -> dict:
    holdings = (
        await db.execute(
            select(PortfolioHolding).where(PortfolioHolding.user_id == user_id).order_by(PortfolioHolding.created_at)
        )
    ).scalars().all()
    rows: list[dict] = []
    invested_total = 0.0
    value_total = 0.0
    sector_values: dict[str, float] = defaultdict(float)
    for h in holdings:
        company = (await db.execute(select(Company).where(Company.symbol == h.symbol))).scalar_one_or_none()
        price = company.current_price if company and company.current_price else h.avg_price
        sector = (company.sector if company and company.sector else "Unknown")
        invested = h.quantity * h.avg_price
        value = h.quantity * price
        invested_total += invested
        value_total += value
        sector_values[sector] += value
        rows.append(
            {
                "id": h.id,
                "symbol": h.symbol,
                "name": company.name if company else h.symbol,
                "sector": sector,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "current_price": price,
                "invested": round(invested, 2),
                "current_value": round(value, 2),
                "pl": round(value - invested, 2),
                "pl_pct": round((value - invested) / invested * 100, 2) if invested else None,
            }
        )
    allocation = [
        {"sector": s, "value": round(v, 2), "pct": round(v / value_total * 100, 2) if value_total else 0.0}
        for s, v in sorted(sector_values.items(), key=lambda kv: kv[1], reverse=True)
    ]
    summary = {
        "invested": round(invested_total, 2),
        "current_value": round(value_total, 2),
        "pl": round(value_total - invested_total, 2),
        "pl_pct": round((value_total - invested_total) / invested_total * 100, 2) if invested_total else None,
        "holdings_count": len(rows),
    }
    return {"holdings": rows, "summary": summary, "sector_allocation": allocation}


@router.get("")
async def get_portfolio(db: AsyncSession = Depends(get_db)) -> dict:
    user = await get_local_user(db)
    return await _build(db, user.id)


@router.post("", status_code=201)
async def add_holding(payload: HoldingAdd, db: AsyncSession = Depends(get_db)) -> dict:
    user = await get_local_user(db)
    symbol = payload.symbol.upper()
    company = (await db.execute(select(Company).where(Company.symbol == symbol))).scalar_one_or_none()
    holding = PortfolioHolding(
        user_id=user.id,
        symbol=symbol,
        company_id=company.id if company else None,
        quantity=payload.quantity,
        avg_price=payload.avg_price,
    )
    db.add(holding)
    await db.commit()
    return await _build(db, user.id)


@router.delete("/{holding_id}", status_code=200)
async def remove_holding(holding_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    user = await get_local_user(db)
    holding = (
        await db.execute(
            select(PortfolioHolding).where(
                PortfolioHolding.id == holding_id, PortfolioHolding.user_id == user.id
            )
        )
    ).scalar_one_or_none()
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    await db.delete(holding)
    await db.commit()
    return await _build(db, user.id)

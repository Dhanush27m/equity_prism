import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Company, FinancialMetric, RiskSignal
from app.services.market_data import get_fundamentals, get_history, get_statement
from app.services.ratios import METRIC_FIELDS, compute_metrics, compute_risk

router = APIRouter(prefix="/companies", tags=["market"])

VALID_KINDS = {"income", "balance", "cashflow"}
VALID_PERIODS = {"1M", "3M", "6M", "1Y", "5Y", "MAX"}


@router.get("/{symbol}/history")
async def history(
    symbol: str,
    period: str = Query(default="1Y"),
    interval: str = Query(default="1d"),
) -> dict:
    period = period.upper()
    if period not in VALID_PERIODS:
        raise HTTPException(status_code=400, detail=f"period must be one of {sorted(VALID_PERIODS)}")
    candles = await asyncio.to_thread(get_history, symbol.upper(), period, interval)
    if not candles:
        raise HTTPException(status_code=404, detail=f"No price history for '{symbol}'")
    return {"symbol": symbol.upper(), "period": period, "interval": interval, "candles": candles}


@router.get("/{symbol}/fundamentals")
async def fundamentals(symbol: str) -> dict:
    data = await asyncio.to_thread(get_fundamentals, symbol.upper())
    if data.get("resolved_suffix") is None:
        raise HTTPException(status_code=404, detail=f"No fundamentals for '{symbol}'")
    return data


@router.get("/{symbol}/statements/{kind}")
async def statements(
    symbol: str,
    kind: str,
    period_type: str = Query(default="annual", pattern="^(annual|quarterly)$"),
) -> dict:
    if kind not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {sorted(VALID_KINDS)}")
    return await asyncio.to_thread(get_statement, symbol.upper(), kind, period_type)


@router.get("/{symbol}/ratios")
async def ratios(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
    symbol = symbol.upper()
    row = (
        await db.execute(
            select(FinancialMetric)
            .join(Company, FinancialMetric.company_id == Company.id)
            .where(Company.symbol == symbol)
        )
    ).scalar_one_or_none()
    if row is not None:
        data = {f: getattr(row, f) for f in METRIC_FIELDS}
        return {"symbol": symbol, "source": "stored", "updated_at": row.updated_at, **data}
    metrics = await asyncio.to_thread(compute_metrics, symbol)
    metrics["source"] = "live"
    return metrics


@router.get("/{symbol}/risk")
async def risk(symbol: str, db: AsyncSession = Depends(get_db)) -> dict:
    symbol = symbol.upper()
    row = (
        await db.execute(
            select(RiskSignal)
            .join(Company, RiskSignal.company_id == Company.id)
            .where(Company.symbol == symbol)
        )
    ).scalar_one_or_none()
    if row is not None:
        return {"symbol": symbol, "source": "stored", "score": row.score, "signals": row.signals}
    metrics = await asyncio.to_thread(compute_metrics, symbol)
    return {"symbol": symbol, "source": "live", **compute_risk(metrics)}

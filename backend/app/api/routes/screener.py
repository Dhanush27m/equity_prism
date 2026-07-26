from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.screener import screen

router = APIRouter(prefix="/screener", tags=["screener"])


@router.get("")
async def run_screener(
    sector: str | None = Query(default=None),
    market_cap_min: int | None = Query(default=None),
    market_cap_max: int | None = Query(default=None),
    pe_min: float | None = Query(default=None),
    pe_max: float | None = Query(default=None),
    roe_min: float | None = Query(default=None),
    roe_max: float | None = Query(default=None),
    dividend_yield_min: float | None = Query(default=None),
    sort_by: str = Query(default="market_cap"),
    desc: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    filters = {
        "sector": sector,
        "market_cap_min": market_cap_min,
        "market_cap_max": market_cap_max,
        "pe_min": pe_min,
        "pe_max": pe_max,
        "roe_min": roe_min,
        "roe_max": roe_max,
        "dividend_yield_min": dividend_yield_min,
        "sort_by": sort_by,
        "desc": desc,
        "limit": limit,
    }
    results = await screen(db, filters)
    return {"count": len(results), "results": results}

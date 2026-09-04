"""
Component: Backend -> Services -> Screener
Belongs to: called from api/routes/screener.py.
Purpose: builds and runs one filtered/sorted SQL query over Company LEFT JOIN
FinancialMetric — entirely stored data, no live yfinance calls per row (so screening
stays fast regardless of how many filters are applied).
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, FinancialMetric

# Which columns a `sort_by` query param is allowed to map to.
SORTABLE = {
    "market_cap": Company.market_cap,
    "pe": FinancialMetric.pe,
    "roe": FinancialMetric.roe,
    "dividend_yield": FinancialMetric.dividend_yield,
    "symbol": Company.symbol,
}


# Applies every provided filter as a WHERE clause, sorts by the requested column, and
# returns the matching rows shaped for the Screener table. Uses an outer join so a
# company with no FinancialMetric row yet still appears (with null ratio fields) rather
# than being silently excluded.
async def screen(db: AsyncSession, filters: dict[str, Any]) -> list[dict]:
    stmt = select(Company, FinancialMetric).join(
        FinancialMetric, FinancialMetric.company_id == Company.id, isouter=True
    )

    if filters.get("sector"):
        stmt = stmt.where(Company.sector == filters["sector"])
    if filters.get("market_cap_min") is not None:
        stmt = stmt.where(Company.market_cap >= filters["market_cap_min"])
    if filters.get("market_cap_max") is not None:
        stmt = stmt.where(Company.market_cap <= filters["market_cap_max"])
    if filters.get("pe_min") is not None:
        stmt = stmt.where(FinancialMetric.pe >= filters["pe_min"])
    if filters.get("pe_max") is not None:
        stmt = stmt.where(FinancialMetric.pe <= filters["pe_max"])
    if filters.get("roe_min") is not None:
        stmt = stmt.where(FinancialMetric.roe >= filters["roe_min"])
    if filters.get("roe_max") is not None:
        stmt = stmt.where(FinancialMetric.roe <= filters["roe_max"])
    if filters.get("dividend_yield_min") is not None:
        stmt = stmt.where(FinancialMetric.dividend_yield >= filters["dividend_yield_min"])

    sort_col = SORTABLE.get(filters.get("sort_by", "market_cap"), Company.market_cap)
    stmt = stmt.order_by(sort_col.desc() if filters.get("desc", True) else sort_col.asc())
    stmt = stmt.limit(filters.get("limit", 50))

    result = await db.execute(stmt)
    rows: list[dict] = []
    for company, metric in result.all():
        rows.append(
            {
                "symbol": company.symbol,
                "name": company.name,
                "sector": company.sector,
                "market_cap": company.market_cap,
                "current_price": company.current_price,
                "pe": metric.pe if metric else None,
                "roe": metric.roe if metric else None,
                "dividend_yield": metric.dividend_yield if metric else None,
            }
        )
    return rows

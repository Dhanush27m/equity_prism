from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.company import Company
from app.schemas.company import CompanyOut

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=list[CompanyOut])
async def list_companies(
    sector: str | None = Query(default=None),
    search: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[Company]:
    stmt = select(Company)
    if sector:
        stmt = stmt.where(Company.sector == sector)
    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Company.name).like(pattern) | func.lower(Company.symbol).like(pattern)
        )
    stmt = stmt.order_by(Company.symbol).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{symbol}", response_model=CompanyOut)
async def get_company(symbol: str, db: AsyncSession = Depends(get_db)) -> Company:
    stmt = select(Company).where(Company.symbol == symbol.upper())
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company '{symbol}' not found")
    return company

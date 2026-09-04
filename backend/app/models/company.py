"""
Component: Backend -> Data Layer -> ORM model
Belongs to: the core reference table every other model/route joins against (via symbol
or company_id) — seeded once by app/seed/seed_companies.py.
Purpose: one row per tracked Nifty 50 company: identity (symbol/name/sector/industry)
and the last-refreshed current_price/market_cap (kept warm by services/refresh.py).
"""

from sqlalchemy import BigInteger, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    sector: Mapped[str | None] = mapped_column(String(128), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(128), nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    exchange: Mapped[str] = mapped_column(String(16), default="NSE")
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)

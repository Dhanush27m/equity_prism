"""
Component: Backend -> Data Layer -> ORM model
Belongs to: the Company page's statements tabs (income/balance/cashflow).
Purpose: stores one full financial statement (as raw JSONB, one row per
company/type/period) — currently statements are always served live from yfinance
(see api/routes/market.py), so this table exists for future stored-first serving but
isn't the active read path yet.
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FinancialStatement(Base):
    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "statement_type", "period_type", "period_end", name="uq_financial_period"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    statement_type: Mapped[str] = mapped_column(String(16))  # "income" | "balance" | "cashflow"
    period_type: Mapped[str] = mapped_column(String(16))  # "annual" | "quarterly"
    period_end: Mapped[date] = mapped_column(Date)
    data: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

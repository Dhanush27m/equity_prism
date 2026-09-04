# Component: Backend -> Data Layer -> ORM model package
# Belongs to: every module that does `from app.models import X` instead of reaching into
# individual model files.
# Purpose: re-exports every SQLAlchemy model class from one place, and — just as
# importantly — ensures every model module is imported (and therefore registered on
# Base.metadata) before Alembic autogenerate or `Base.metadata.create_all` run.

from app.models.base import Base
from app.models.company import Company
from app.models.document import Document, DocumentChunk
from app.models.financials import FinancialStatement
from app.models.metrics import FinancialMetric, RiskSignal
from app.models.portfolio import PortfolioHolding
from app.models.rag import RagTrace
from app.models.user import User
from app.models.watchlist import WatchlistItem

__all__ = [
    "Base",
    "Company",
    "Document",
    "DocumentChunk",
    "FinancialMetric",
    "FinancialStatement",
    "PortfolioHolding",
    "RagTrace",
    "RiskSignal",
    "User",
    "WatchlistItem",
]

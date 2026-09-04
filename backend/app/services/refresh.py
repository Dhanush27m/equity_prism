"""
Component: Backend -> Services -> Batch data refresh script
Belongs to: run manually (`python -m app.services.refresh`, ~5-7 min for the full Nifty
50) — see DEPLOY.md Step 2. Not called from the API. This is what keeps the "stored"
data api/routes/market.py's /ratios and /risk endpoints serve actually up to date.
Purpose: for every seeded company, re-fetches fundamentals, recomputes ratios/risk
(via services/ratios.py), and upserts the results into FinancialMetric/RiskSignal —
the stored-first data every specialist agent's snapshot is grounded in.
"""

import time

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Company, FinancialMetric, RiskSignal
from app.services.market_data import get_fundamentals
from app.services.ratios import compute_metrics, compute_risk

settings = get_settings()
engine = create_engine(settings.database_url_sync, future=True)


# Updates a Company row's core fields (name/sector/industry/market_cap/price/currency)
# from freshly fetched fundamentals, only overwriting fields that actually came back
# non-empty (so a partial/failed fetch never blanks out previously-good data).
def _update_company_core(session: Session, company: Company, fundamentals: dict) -> None:
    name = fundamentals.get("longName")
    if name:
        company.name = name
    if fundamentals.get("sector"):
        company.sector = fundamentals["sector"]
    if fundamentals.get("industry"):
        company.industry = fundamentals["industry"]
    if fundamentals.get("marketCap"):
        company.market_cap = fundamentals["marketCap"]
    price = fundamentals.get("currentPrice") or fundamentals.get("regularMarketPrice") or fundamentals.get("previousClose")
    if price:
        company.current_price = price
    if fundamentals.get("currency"):
        company.currency = fundamentals["currency"]


# Creates or updates the one FinancialMetric row for a company from a freshly computed
# metrics dict.
def _upsert_metric(session: Session, company_id: int, metrics: dict) -> None:
    row = session.scalar(select(FinancialMetric).where(FinancialMetric.company_id == company_id))
    if row is None:
        row = FinancialMetric(company_id=company_id)
        session.add(row)
    for field in (
        "pe", "forward_pe", "pb", "ps", "roe", "roa", "roce", "debt_to_equity",
        "current_ratio", "quick_ratio", "gross_margin", "operating_margin", "net_margin",
        "revenue_growth", "earnings_growth", "dividend_yield", "fcf_yield", "eps", "beta",
    ):
        setattr(row, field, metrics.get(field))


# Creates or updates the one RiskSignal row for a company from a freshly computed risk dict.
def _upsert_risk(session: Session, company_id: int, risk: dict) -> None:
    row = session.scalar(select(RiskSignal).where(RiskSignal.company_id == company_id))
    if row is None:
        row = RiskSignal(company_id=company_id)
        session.add(row)
    row.score = risk["score"]
    row.signals = risk["signals"]


# Full refresh for one company: fetch -> compute -> upsert -> commit.
def refresh_symbol(session: Session, company: Company) -> dict:
    fundamentals = get_fundamentals(company.symbol)
    _update_company_core(session, company, fundamentals)
    metrics = compute_metrics(company.symbol)
    risk = compute_risk(metrics)
    _upsert_metric(session, company.id, metrics)
    _upsert_risk(session, company.id, risk)
    session.commit()
    return {"metrics": metrics, "risk": risk}


# Entry point: refreshes every seeded company in turn, printing progress; a per-symbol
# failure is caught, rolled back, and logged rather than aborting the whole run. A 1s
# sleep between symbols throttles against yfinance rate limits.
def main() -> None:
    with Session(engine) as session:
        companies = list(session.scalars(select(Company).order_by(Company.symbol)))
        total = len(companies)
        for i, company in enumerate(companies, start=1):
            try:
                result = refresh_symbol(session, company)
                score = result["risk"]["score"]
                roe = result["metrics"].get("roe")
                print(f"[{i:>2}/{total}] {company.symbol:<12} roe={roe} risk_score={score}", flush=True)
            except Exception as exc:
                session.rollback()
                print(f"[{i:>2}/{total}] {company.symbol:<12} ERROR {type(exc).__name__}: {str(exc)[:60]}", flush=True)
            time.sleep(1.0)
    print("Refresh complete.", flush=True)


if __name__ == "__main__":
    main()

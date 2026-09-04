"""
Component: Backend -> AI Orchestration Layer (data grounding)
Belongs to: runs before the LangGraph graph is invoked (called from app/api/routes/chat.py).
Purpose: this is the project's core anti-hallucination mechanism — it resolves which
tracked companies a question mentions and pre-fetches every number/fact any agent could
need (stored metrics, risk signals, news, portfolio, document availability) into one
"snapshot" dict. Agents are then instructed to use ONLY this snapshot, never to invent data.
"""

import asyncio
import re
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Company, Document, FinancialMetric, PortfolioHolding, RiskSignal, User
from app.services.news import get_news
from app.services.ratios import METRIC_FIELDS

# Common words in company names that would cause false-positive symbol matches
# (e.g. "bank" appearing in many different bank names) and so are excluded from
# the name-token matching in resolve_symbols below.
GENERIC_TOKENS = {
    "bank", "limited", "india", "indian", "industries", "company", "corporation",
    "services", "enterprises", "power", "steel", "cement", "auto", "life", "insurance",
    "finance", "financial", "consumer", "products", "paints", "technologies", "infotech",
    "systems", "motors", "petroleum", "chemicals", "healthcare", "pharma", "labs", "mahindra",
}

MAX_SYMBOLS = 4


# Pure token-matching symbol resolver: scans the question text for a company's ticker or
# a distinctive word from its name (no LLM call — fast, free, and deterministic).
async def resolve_symbols(db: AsyncSession, question: str) -> list[str]:
    rows = (await db.execute(select(Company.symbol, Company.name))).all()
    q_tokens = set(re.findall(r"[a-z0-9]+", question.lower()))
    hits: list[str] = []
    for symbol, name in rows:
        if symbol.lower() in q_tokens:
            hits.append(symbol)
            continue
        for tok in re.findall(r"[a-z]+", (name or "").lower()):
            if len(tok) >= 4 and tok not in GENERIC_TOKENS and tok in q_tokens:
                hits.append(symbol)
                break
    ordered: list[str] = []
    for h in hits:
        if h not in ordered:
            ordered.append(h)
    return ordered[:MAX_SYMBOLS]


# Builds the portfolio agent's data: prices every holding of the single local user
# against each company's stored current_price and computes invested/value/P&L per row.
async def _portfolio_snapshot(db: AsyncSession) -> dict | None:
    user = (await db.execute(select(User).where(User.username == "local"))).scalar_one_or_none()
    if user is None:
        return None
    holdings = (
        await db.execute(select(PortfolioHolding).where(PortfolioHolding.user_id == user.id))
    ).scalars().all()
    if not holdings:
        return None
    rows: list[dict] = []
    invested_total = 0.0
    value_total = 0.0
    for h in holdings:
        company = (await db.execute(select(Company).where(Company.symbol == h.symbol))).scalar_one_or_none()
        price = company.current_price if company and company.current_price else h.avg_price
        invested = h.quantity * h.avg_price
        value = h.quantity * price
        invested_total += invested
        value_total += value
        rows.append(
            {
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "current_price": price,
                "invested": round(invested, 2),
                "current_value": round(value, 2),
                "pl": round(value - invested, 2),
                "pl_pct": round((value - invested) / invested * 100, 2) if invested else None,
            }
        )
    return {
        "holdings": rows,
        "totals": {
            "invested": round(invested_total, 2),
            "current_value": round(value_total, 2),
            "pl": round(value_total - invested_total, 2),
            "pl_pct": round((value_total - invested_total) / invested_total * 100, 2) if invested_total else None,
        },
    }


# Main entry point: for each resolved symbol, loads its stored Company/FinancialMetric/
# RiskSignal rows and up to 5 recent news headlines (all symbols fetched concurrently via
# asyncio.gather), then attaches portfolio and document-availability context. The
# returned dict is the single source of truth every specialist agent's prompt is built from.
async def build_snapshot(db: AsyncSession, symbols: list[str]) -> dict:
    companies: dict[str, dict] = {}
    for sym in symbols:
        company = (await db.execute(select(Company).where(Company.symbol == sym))).scalar_one_or_none()
        if company is None:
            continue
        metric = (
            await db.execute(select(FinancialMetric).where(FinancialMetric.company_id == company.id))
        ).scalar_one_or_none()
        risk = (
            await db.execute(select(RiskSignal).where(RiskSignal.company_id == company.id))
        ).scalar_one_or_none()
        companies[sym] = {
            "name": company.name,
            "sector": company.sector,
            "industry": company.industry,
            "market_cap": company.market_cap,
            "current_price": company.current_price,
            "currency": company.currency,
            "metrics": {f: getattr(metric, f) for f in METRIC_FIELDS} if metric else None,
            "risk": {"score": risk.score, "signals": risk.signals} if risk else None,
        }

    resolved = [s for s in symbols if s in companies]
    if resolved:
        news_lists = await asyncio.gather(
            *[asyncio.to_thread(get_news, s, companies[s]["name"], 5) for s in resolved]
        )
        for sym, articles in zip(resolved, news_lists):
            companies[sym]["news"] = [
                {
                    "title": a.get("title"),
                    "source": a.get("source"),
                    "published": a.get("published"),
                    "link": a.get("link"),
                    "relevance": a.get("relevance"),
                }
                for a in articles[:5]
            ]

    portfolio = await _portfolio_snapshot(db)
    doc_count = await _ready_document_count(db)
    return {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "symbols": list(companies.keys()),
        "companies": companies,
        "portfolio": portfolio,
        "has_documents": doc_count > 0,
        "document_count": doc_count,
    }


# Counts the local user's fully-ingested ("ready") documents — used to decide whether the
# router is allowed to select the document_research agent at all.
async def _ready_document_count(db: AsyncSession) -> int:
    user = (await db.execute(select(User).where(User.username == "local"))).scalar_one_or_none()
    if user is None:
        return 0
    count = await db.scalar(
        select(func.count(Document.id)).where(
            Document.user_id == user.id, Document.status == "ready"
        )
    )
    return int(count or 0)

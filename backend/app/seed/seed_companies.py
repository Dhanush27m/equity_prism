import time

import yfinance as yf
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Company, User
from app.seed.nifty50 import NIFTY_50_SYMBOLS

settings = get_settings()
engine = create_engine(settings.database_url_sync, future=True)


def fetch_info(symbol: str, retries: int = 3) -> dict:
    for suffix in (".NS", ".BO"):
        info: dict = {}
        for attempt in range(retries):
            try:
                info = yf.Ticker(f"{symbol}{suffix}").info or {}
            except Exception:
                info = {}
            if info.get("longName") or info.get("shortName") or info.get("marketCap"):
                break
            time.sleep(1.0 * (attempt + 1))
        if info.get("longName") or info.get("shortName") or info.get("marketCap"):
            break
    name = info.get("longName") or info.get("shortName") or symbol
    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose")
    return {
        "name": name,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("marketCap"),
        "currency": info.get("currency") or "INR",
        "current_price": price,
    }


def ensure_default_user(session: Session) -> None:
    existing = session.scalar(select(User).where(User.username == "local"))
    if existing is None:
        session.add(User(username="local"))
        session.commit()


def upsert_company(session: Session, symbol: str, data: dict) -> str:
    company = session.scalar(select(Company).where(Company.symbol == symbol))
    if company is None:
        company = Company(symbol=symbol, name=data["name"], exchange="NSE")
        session.add(company)
        action = "created"
    else:
        action = "updated"
    company.name = data["name"]
    company.sector = data["sector"]
    company.industry = data["industry"]
    company.market_cap = data["market_cap"]
    company.currency = data["currency"]
    company.current_price = data["current_price"]
    session.commit()
    return action


def main() -> None:
    with Session(engine) as session:
        ensure_default_user(session)
        total = len(NIFTY_50_SYMBOLS)
        for i, symbol in enumerate(NIFTY_50_SYMBOLS, start=1):
            data = fetch_info(symbol)
            action = upsert_company(session, symbol, data)
            cap = data["market_cap"] or 0
            print(
                f"[{i:>2}/{total}] {symbol:<12} {action:<8} {data['name'][:40]:<40} cap={cap}",
                flush=True,
            )
            time.sleep(1.0)
    print("Seed complete.")


if __name__ == "__main__":
    main()

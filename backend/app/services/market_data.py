import math
from typing import Any

import pandas as pd
import yfinance as yf

from app.services.yf_session import cache_get, cache_set

SUFFIXES = [".NS", ".BO"]

HISTORY_TTL = 1800
INFO_TTL = 21600
STATEMENT_TTL = 43200
INDEX_TTL = 300

PERIOD_MAP = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "5Y": "5y", "MAX": "max"}

INDICES = [
    {"key": "NIFTY50", "name": "NIFTY 50", "ticker": "^NSEI"},
    {"key": "SENSEX", "name": "SENSEX", "ticker": "^BSESN"},
    {"key": "BANKNIFTY", "name": "BANK NIFTY", "ticker": "^NSEBANK"},
    {"key": "INDIAVIX", "name": "INDIA VIX", "ticker": "^INDIAVIX"},
]


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.date().isoformat()
    return value


def _ticker(symbol: str, suffix: str) -> yf.Ticker:
    return yf.Ticker(f"{symbol}{suffix}")


def resolve_info(symbol: str) -> tuple[dict, str | None]:
    for suffix in SUFFIXES:
        try:
            info = _ticker(symbol, suffix).info or {}
        except Exception:
            info = {}
        if info.get("longName") or info.get("marketCap") or info.get("regularMarketPrice"):
            return info, suffix
    return {}, None


def get_fundamentals(symbol: str) -> dict:
    key = f"fund:{symbol}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    info, suffix = resolve_info(symbol)
    keys = [
        "longName", "sector", "industry", "marketCap", "currency", "exchange",
        "currentPrice", "regularMarketPrice", "previousClose", "open", "dayHigh", "dayLow",
        "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "volume", "averageVolume", "beta",
        "trailingPE", "forwardPE", "priceToBook", "dividendYield", "trailingEps",
        "returnOnEquity", "returnOnAssets", "debtToEquity", "currentRatio", "quickRatio",
        "grossMargins", "operatingMargins", "profitMargins", "revenueGrowth", "earningsGrowth",
        "totalRevenue", "ebitda", "freeCashflow", "bookValue", "priceToSalesTrailing12Months",
    ]
    out = {k: _clean(info.get(k)) for k in keys}
    out["symbol"] = symbol
    out["resolved_suffix"] = suffix
    if suffix is not None:
        cache_set(key, out, INFO_TTL)
    return out


def get_history(symbol: str, period: str = "1Y", interval: str = "1d") -> list[dict]:
    yf_period = PERIOD_MAP.get(period.upper(), "1y")
    key = f"hist:{symbol}:{yf_period}:{interval}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    df = pd.DataFrame()
    used_suffix = None
    for suffix in SUFFIXES:
        try:
            df = _ticker(symbol, suffix).history(period=yf_period, interval=interval)
        except Exception:
            df = pd.DataFrame()
        if not df.empty:
            used_suffix = suffix
            break
    candles: list[dict] = []
    for idx, row in df.iterrows():
        candles.append(
            {
                "time": idx.date().isoformat(),
                "open": _clean(round(float(row["Open"]), 2)),
                "high": _clean(round(float(row["High"]), 2)),
                "low": _clean(round(float(row["Low"]), 2)),
                "close": _clean(round(float(row["Close"]), 2)),
                "volume": int(row["Volume"]) if not math.isnan(row["Volume"]) else 0,
            }
        )
    if candles and used_suffix is not None:
        cache_set(key, candles, HISTORY_TTL)
    return candles


def _index_quote(ticker: str) -> dict:
    df = pd.DataFrame()
    try:
        df = yf.Ticker(ticker).history(period="5d", interval="1d")
    except Exception:
        df = pd.DataFrame()
    if df.empty or "Close" not in df:
        return {"value": None, "change": None, "change_pct": None}
    closes = [float(c) for c in df["Close"].tolist() if not math.isnan(c)]
    if not closes:
        return {"value": None, "change": None, "change_pct": None}
    last = closes[-1]
    prev = closes[-2] if len(closes) >= 2 else last
    change = last - prev
    change_pct = (change / prev * 100) if prev else 0.0
    return {
        "value": round(last, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
    }


def get_indices() -> list[dict]:
    key = "indices:in"
    cached = cache_get(key)
    if cached is not None:
        return cached
    out: list[dict] = []
    for idx in INDICES:
        quote = _index_quote(idx["ticker"])
        out.append({"key": idx["key"], "name": idx["name"], "ticker": idx["ticker"], **quote})
    if any(i["value"] is not None for i in out):
        cache_set(key, out, INDEX_TTL)
    return out


def _statement_df(symbol: str, kind: str, period_type: str) -> pd.DataFrame:
    quarterly = period_type == "quarterly"
    attr = {
        ("income", False): "income_stmt",
        ("income", True): "quarterly_income_stmt",
        ("balance", False): "balance_sheet",
        ("balance", True): "quarterly_balance_sheet",
        ("cashflow", False): "cashflow",
        ("cashflow", True): "quarterly_cashflow",
    }[(kind, quarterly)]
    for suffix in SUFFIXES:
        try:
            df = getattr(_ticker(symbol, suffix), attr)
        except Exception:
            df = pd.DataFrame()
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return pd.DataFrame()


def get_statement(symbol: str, kind: str, period_type: str = "annual") -> dict:
    key = f"stmt:{symbol}:{kind}:{period_type}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    df = _statement_df(symbol, kind, period_type)
    if df.empty:
        return {"symbol": symbol, "kind": kind, "period_type": period_type, "periods": [], "rows": {}}
    periods = [c.date().isoformat() if hasattr(c, "date") else str(c) for c in df.columns]
    rows = {
        str(item): [_clean(None if pd.isna(v) else float(v)) for v in df.loc[item].tolist()]
        for item in df.index
    }
    out = {
        "symbol": symbol,
        "kind": kind,
        "period_type": period_type,
        "periods": periods,
        "rows": rows,
    }
    cache_set(key, out, STATEMENT_TTL)
    return out

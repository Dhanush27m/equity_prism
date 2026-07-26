from typing import Any

from app.services.market_data import get_fundamentals, get_statement

METRIC_FIELDS = [
    "pe", "forward_pe", "pb", "ps", "roe", "roa", "roce", "debt_to_equity",
    "current_ratio", "quick_ratio", "gross_margin", "operating_margin", "net_margin",
    "revenue_growth", "earnings_growth", "dividend_yield", "fcf_yield", "eps", "beta",
]


def _latest(stmt: dict, *names: str) -> float | None:
    rows = stmt.get("rows", {})
    for name in names:
        values = rows.get(name)
        if values:
            for v in values:
                if v is not None:
                    return float(v)
    return None


def _derived(symbol: str) -> dict[str, float | None]:
    income = get_statement(symbol, "income", "annual")
    balance = get_statement(symbol, "balance", "annual")
    cashflow = get_statement(symbol, "cashflow", "annual")

    net_income = _latest(income, "Net Income", "Net Income Common Stockholders", "NetIncome")
    ebit = _latest(income, "EBIT", "Operating Income", "OperatingIncome")
    total_assets = _latest(balance, "Total Assets", "TotalAssets")
    equity = _latest(
        balance, "Stockholders Equity", "Total Stockholder Equity",
        "Total Equity Gross Minority Interest", "StockholdersEquity",
    )
    current_assets = _latest(balance, "Current Assets", "Total Current Assets")
    current_liabilities = _latest(balance, "Current Liabilities", "Total Current Liabilities")
    fcf = _latest(cashflow, "Free Cash Flow", "FreeCashFlow")
    if fcf is None:
        ocf = _latest(cashflow, "Operating Cash Flow", "Total Cash From Operating Activities")
        capex = _latest(cashflow, "Capital Expenditure", "Capital Expenditures")
        if ocf is not None and capex is not None:
            fcf = ocf + capex

    def ratio(num: float | None, den: float | None) -> float | None:
        if num is None or not den:
            return None
        return round(num / den, 4)

    roce = None
    if ebit is not None and total_assets is not None and current_liabilities is not None:
        capital_employed = total_assets - current_liabilities
        if capital_employed > 0:
            roce = round(ebit / capital_employed, 4)

    return {
        "roe": ratio(net_income, equity),
        "roa": ratio(net_income, total_assets),
        "roce": roce,
        "current_ratio": ratio(current_assets, current_liabilities),
        "fcf": fcf,
    }


def compute_metrics(symbol: str) -> dict[str, Any]:
    f = get_fundamentals(symbol)
    d = _derived(symbol)
    market_cap = f.get("marketCap")
    fcf = f.get("freeCashflow") if f.get("freeCashflow") is not None else d["fcf"]
    fcf_yield = round(fcf / market_cap, 4) if fcf and market_cap else None
    return {
        "symbol": symbol,
        "pe": f.get("trailingPE"),
        "forward_pe": f.get("forwardPE"),
        "pb": f.get("priceToBook"),
        "ps": f.get("priceToSalesTrailing12Months"),
        "roe": f.get("returnOnEquity") if f.get("returnOnEquity") is not None else d["roe"],
        "roa": f.get("returnOnAssets") if f.get("returnOnAssets") is not None else d["roa"],
        "roce": d["roce"],
        "debt_to_equity": f.get("debtToEquity"),
        "current_ratio": f.get("currentRatio") if f.get("currentRatio") is not None else d["current_ratio"],
        "quick_ratio": f.get("quickRatio"),
        "gross_margin": f.get("grossMargins"),
        "operating_margin": f.get("operatingMargins"),
        "net_margin": f.get("profitMargins"),
        "revenue_growth": f.get("revenueGrowth"),
        "earnings_growth": f.get("earningsGrowth"),
        "dividend_yield": f.get("dividendYield"),
        "fcf_yield": fcf_yield,
        "eps": f.get("trailingEps"),
        "beta": f.get("beta"),
    }


def compute_risk(metrics: dict[str, Any]) -> dict[str, Any]:
    signals: list[dict[str, str]] = []

    def flag(code: str, label: str, severity: str) -> None:
        signals.append({"code": code, "label": label, "severity": severity})

    de = metrics.get("debt_to_equity")
    if de is not None and de > 150:
        flag("high_leverage", f"High leverage (D/E {de:.0f}%)", "high")
    cr = metrics.get("current_ratio")
    if cr is not None and cr < 1:
        flag("weak_liquidity", f"Weak liquidity (current ratio {cr:.2f})", "high")
    om = metrics.get("operating_margin")
    if om is not None and om < 0.05:
        flag("margin_pressure", f"Thin operating margin ({om * 100:.1f}%)", "medium")
    eg = metrics.get("earnings_growth")
    if eg is not None and eg < 0:
        flag("earnings_decline", f"Declining earnings ({eg * 100:.1f}%)", "medium")
    rg = metrics.get("revenue_growth")
    if rg is not None and rg < 0:
        flag("revenue_decline", f"Declining revenue ({rg * 100:.1f}%)", "medium")
    fy = metrics.get("fcf_yield")
    if fy is not None and fy < 0:
        flag("negative_fcf", "Negative free cash flow", "high")

    severity_weight = {"high": 2, "medium": 1, "low": 1}
    score = sum(severity_weight.get(s["severity"], 1) for s in signals)
    return {"score": score, "signals": signals}

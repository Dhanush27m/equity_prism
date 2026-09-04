# Component: Backend -> Data seeding -> Static reference list
# Belongs to: app/seed/seed_companies.py (initial seed) and app/services/refresh.py
# (iterates the already-seeded Company rows, not this list directly).
# Purpose: the universe of NSE ticker symbols this project tracks — the Nifty 50 index
# constituents. LTIM and TATAMOTORS currently have no live Yahoo Finance data (a symbol
# change / demerger); their rows are seeded with name/sector but null metrics rather
# than being dropped from this list.

NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "SBIN",
    "BHARTIARTL", "ITC", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI",
    "HCLTECH", "SUNPHARMA", "TATAMOTORS", "NTPC", "ULTRACEMCO", "BAJFINANCE",
    "WIPRO", "POWERGRID", "ONGC", "TATASTEEL", "ADANIENT", "ADANIPORTS",
    "JSWSTEEL", "TECHM", "NESTLEIND", "TITAN", "BAJAJFINSV", "INDUSINDBK",
    "GRASIM", "CIPLA", "APOLLOHOSP", "DRREDDY", "COALINDIA", "BPCL", "EICHERMOT",
    "HEROMOTOCO", "DIVISLAB", "TATACONSUM", "SBILIFE", "BRITANNIA", "LTIM",
    "HINDALCO", "M&M", "BAJAJ-AUTO", "SHRIRAMFIN", "HDFCLIFE",
]

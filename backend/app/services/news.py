"""
Component: Backend -> Services -> External data (news)
Belongs to: called from api/routes/news.py (News page) and app/agents/snapshot.py (feeds
the sentiment specialist agent's grounded context).
Purpose: fetches and relevance-scores news headlines for a symbol via Google News RSS
(no paid news API) — resilient parsing (feedparser degrades gracefully on malformed
feeds) and cached (services/yf_session.py) since RSS fetches are relatively slow.
"""

import feedparser

from app.services.market_data import get_fundamentals
from app.services.yf_session import cache_get, cache_set

NEWS_TTL = 1800
RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


# Splits a company name into meaningful search/matching tokens, dropping short and
# generic words (the same idea as snapshot.py's GENERIC_TOKENS, applied to relevance
# scoring instead of symbol resolution).
def _tokens(name: str) -> list[str]:
    stop = {"limited", "ltd", "the", "and", "india", "industries", "company", "corporation"}
    return [t.lower() for t in name.replace("&", " ").split() if len(t) > 3 and t.lower() not in stop]


# Scores how relevant one headline is to the company: fraction of name tokens present in
# the title+summary, plus a bonus if the ticker symbol itself appears. Falls back to a
# coarse 1.0/0.5 split when there are no usable name tokens at all.
def _relevance(title: str, summary: str, tokens: list[str], symbol: str) -> float:
    text = f"{title} {summary}".lower()
    if not tokens:
        return 1.0 if symbol.lower() in text else 0.5
    hits = sum(1 for t in tokens if t in text)
    return round(min(1.0, hits / max(1, len(tokens)) + (0.3 if symbol.lower() in text else 0)), 2)


# Main entry point: fetches Google News RSS for the company's name, scores and sorts
# results by relevance, and caches the result for NEWS_TTL seconds. Falls back to
# looking up the company name via get_fundamentals if not provided. Returns an empty
# list (never raises) on a feed-parsing failure.
def get_news(symbol: str, name: str | None = None, limit: int = 20) -> list[dict]:
    key = f"news:{symbol}:{limit}"
    cached = cache_get(key)
    if cached is not None:
        return cached
    if not name:
        name = get_fundamentals(symbol).get("longName") or symbol
    query = f'"{name}" stock'.replace(" ", "+")
    feed = feedparser.parse(RSS_URL.format(query=query))
    tokens = _tokens(name)
    articles: list[dict] = []
    for entry in feed.entries[:limit]:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        source = entry.get("source", {}).get("title") if entry.get("source") else None
        articles.append(
            {
                "title": title,
                "link": entry.get("link"),
                "published": entry.get("published"),
                "source": source,
                "summary": summary,
                "relevance": _relevance(title, summary, tokens, symbol),
            }
        )
    articles.sort(key=lambda a: a["relevance"], reverse=True)
    if articles:
        cache_set(key, articles, NEWS_TTL)
    return articles

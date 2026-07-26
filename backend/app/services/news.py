import feedparser

from app.services.market_data import get_fundamentals
from app.services.yf_session import cache_get, cache_set

NEWS_TTL = 1800
RSS_URL = "https://news.google.com/rss/search?q={query}&hl=en-IN&gl=IN&ceid=IN:en"


def _tokens(name: str) -> list[str]:
    stop = {"limited", "ltd", "the", "and", "india", "industries", "company", "corporation"}
    return [t.lower() for t in name.replace("&", " ").split() if len(t) > 3 and t.lower() not in stop]


def _relevance(title: str, summary: str, tokens: list[str], symbol: str) -> float:
    text = f"{title} {summary}".lower()
    if not tokens:
        return 1.0 if symbol.lower() in text else 0.5
    hits = sum(1 for t in tokens if t in text)
    return round(min(1.0, hits / max(1, len(tokens)) + (0.3 if symbol.lower() in text else 0)), 2)


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

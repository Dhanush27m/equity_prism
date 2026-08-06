# Equity Prism — Links

All URLs for the deployed project: the live app, backend API, endpoints, and external services.

---

## Live app

| Service | URL | Notes |
|---------|-----|-------|
| **App (frontend)** | https://equity-prism.vercel.app | The shareable link — open, enter the access key, use it |
| **Backend API** | https://equity-prism-api.onrender.com | FastAPI on Render |
| **API health** | https://equity-prism-api.onrender.com/api/health | Liveness check (no key needed) |

> All API routes except `/api/health` require the `X-Access-Key` header (the app sends it automatically after you enter the access key at the gate).

---

## Hosting dashboards (owner)

| Platform | Purpose | URL |
|----------|---------|-----|
| **Vercel** | Frontend hosting | https://vercel.com/dashboard |
| **Render** | Backend hosting | https://dashboard.render.com |
| **Supabase** | Postgres + pgvector database | https://supabase.com/dashboard |
| **Groq** | LLM API key & usage | https://console.groq.com |
| **LangFuse Cloud** | Agent tracing (optional) | https://cloud.langfuse.com |

---

## API endpoints (base: https://equity-prism-api.onrender.com/api)

### Health
- `GET /api/health`

### Companies & fundamentals
- `GET /api/companies` · `?sector=` · `?search=`
- `GET /api/companies/{symbol}`
- `GET /api/companies/{symbol}/history?period=1M|3M|6M|1Y|5Y|MAX&interval=1d`
- `GET /api/companies/{symbol}/fundamentals`
- `GET /api/companies/{symbol}/statements/{income|balance|cashflow}?period_type=annual|quarterly`
- `GET /api/companies/{symbol}/ratios`
- `GET /api/companies/{symbol}/risk`

### Market, news, screener
- `GET /api/market/indices`
- `GET /api/news/{symbol}`
- `GET /api/screener?sector=&market_cap_min=&market_cap_max=&pe_min=&pe_max=&roe_min=&roe_max=&dividend_yield_min=&sort_by=&desc=&limit=`

### Chat (multi-agent)
- `GET /api/chat/agents`
- `POST /api/chat`
- `POST /api/chat/stream` (SSE)

### Documents (RAG)
- `POST /api/documents` (multipart PDF upload)
- `GET /api/documents`
- `GET /api/documents/{id}`
- `DELETE /api/documents/{id}`

### Watchlist & portfolio
- `GET /api/watchlist` · `POST /api/watchlist` · `DELETE /api/watchlist/{symbol}`
- `GET /api/portfolio` · `POST /api/portfolio` · `DELETE /api/portfolio/{id}`

---

## External services & data sources

| What | Link |
|------|------|
| Groq API console (LLM key) | https://console.groq.com |
| Groq docs | https://console.groq.com/docs |
| yfinance (market data) | https://github.com/ranaroussi/yfinance |
| Google News RSS (news source) | https://news.google.com/rss |

---

## Tech & framework docs

| Component | Link |
|-----------|------|
| Next.js 15 | https://nextjs.org/docs |
| React 19 | https://react.dev |
| Tailwind CSS v4 | https://tailwindcss.com/docs |
| TradingView Lightweight Charts | https://tradingview.github.io/lightweight-charts/ |
| Recharts | https://recharts.org |
| TanStack Query | https://tanstack.com/query/latest |
| Zustand | https://zustand-demo.pmnd.rs |
| FastAPI | https://fastapi.tiangolo.com |
| SQLAlchemy 2 (async) | https://docs.sqlalchemy.org/en/20/ |
| Alembic | https://alembic.sqlalchemy.org |
| LangGraph | https://langchain-ai.github.io/langgraph/ |
| LangFuse | https://langfuse.com/docs |
| pgvector | https://github.com/pgvector/pgvector |
| fastembed | https://github.com/qdrant/fastembed |
| RAGAS (metric definitions) | https://docs.ragas.io |

---

## Project docs (in this repo)

| File | Purpose |
|------|---------|
| [README.md](./README.md) | Overview, architecture, tech stack, endpoints |
| [DEPLOY.md](./DEPLOY.md) | Free hosting guide (Vercel + Render + Supabase) |
| [USER_GUIDE.md](./USER_GUIDE.md) | How to use the app, feature by feature |
| [LICENSE](./LICENSE) | MIT license |

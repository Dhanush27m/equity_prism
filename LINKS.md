# Equity Prism — Links

All URLs for the project: local services, frontend pages, API endpoints, and external references.
These are **local development** URLs — the app runs entirely on your machine via Docker Compose (backend) and `npm run dev` (frontend). Nothing is publicly deployed.

---

## Local services

| Service | URL | Notes |
|---------|-----|-------|
| **Frontend (app)** | http://localhost:3001 | Next.js UI — start with `cd frontend && npm run dev` |
| **Backend API** | http://localhost:8000 | FastAPI |
| **API health** | http://localhost:8000/api/health | Liveness check |
| **API docs (Swagger UI)** | http://localhost:8000/docs | Interactive, try endpoints in-browser |
| **API docs (ReDoc)** | http://localhost:8000/redoc | Read-only reference |
| **OpenAPI schema** | http://localhost:8000/openapi.json | Raw spec |
| **LangFuse (tracing UI)** | http://localhost:3000 | Agent traces: tokens, latency, cost |
| **Ollama** | http://localhost:11434 | Local LLM fallback (`llama3.1:8b`) |
| **PostgreSQL** | localhost:5432 | DBs: `equity_prism` (app), `langfuse` |
| **Redis** | localhost:6379 | db0 cache · db1 Celery broker · db2 Celery result |

---

## Frontend pages (http://localhost:3001)

| Page | URL |
|------|-----|
| Dashboard | http://localhost:3001/ |
| Company (dynamic) | http://localhost:3001/company/RELIANCE |
| Prism Chat | http://localhost:3001/chat |
| Compare | http://localhost:3001/compare |
| Portfolio | http://localhost:3001/portfolio |
| Documents | http://localhost:3001/documents |
| Screener | http://localhost:3001/screener |
| News | http://localhost:3001/news |
| Settings | http://localhost:3001/settings |

> Company pages are dynamic — swap `RELIANCE` for any seeded Nifty 50 symbol (e.g. `TCS`, `INFY`, `HDFCBANK`).

---

## API endpoints (base: http://localhost:8000/api)

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
| Groq API console (get/manage the LLM key) | https://console.groq.com |
| Groq docs | https://console.groq.com/docs |
| yfinance (Yahoo Finance market data) | https://github.com/ranaroussi/yfinance |
| Google News RSS (news source) | https://news.google.com/rss |
| Ollama (model registry) | https://ollama.com/library/llama3.1 |

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
| LangFuse (self-hosted) | https://langfuse.com/docs |
| Celery | https://docs.celeryq.dev |
| pgvector | https://github.com/pgvector/pgvector |
| TimescaleDB | https://docs.timescale.com |
| sentence-transformers | https://www.sbert.net |
| RAGAS (metric definitions) | https://docs.ragas.io |

---

## Project docs (in this repo)

| File | Purpose |
|------|---------|
| [README.md](./README.md) | As-built overview, architecture, setup, deviations |
| [DEPLOY.md](./DEPLOY.md) | Free hosting guide (Vercel + Render + Supabase) |
| [USER_GUIDE.md](./USER_GUIDE.md) | How to use the app, feature by feature |
| [LICENSE](./LICENSE) | MIT license |
| [equity_prism_prompt.md](./equity_prism_prompt.md) | Original 7-phase build spec |
| [equity_prism_improvements.md](./equity_prism_improvements.md) | Architecture decisions from reference-repo research |
| [equity_prism_similar_resources.md](./equity_prism_similar_resources.md) | Reference resources |
| [.env.example](./.env.example) | Environment variable template |

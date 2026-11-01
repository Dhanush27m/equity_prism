# Equity Prism

A full-stack **AI-powered equity research platform** for Indian stock markets (NSE/BSE). A LangGraph multi-agent system analyzes stocks, compares companies, tracks sentiment, manages portfolios, and answers questions over uploaded financial documents using RAG — running entirely on your local machine.

---

## What it does

Ask questions in plain English and a team of specialist AI agents collaborates to answer, grounding every number in verified data. Nine screens cover the full research workflow:

- **Dashboard** — live indices, watchlist, portfolio summary, quick-ask
- **Company** — candlestick + volume chart, key metrics, financial statements, risk signals
- **Prism Chat** — streaming multi-agent AI analyst with agent badges + citations
- **Compare** — 2–5 stocks side by side with metric charts and an AI verdict
- **Portfolio** — holdings with live P&L, sector allocation, AI analysis
- **Documents** — upload PDFs and ask questions about them (RAG, with page citations)
- **Screener** — filter the Nifty 50 by fundamentals
- **News** — headlines with a sentiment read
- **Settings**

---

## Architecture

```
        ┌──────────────────────────────────────────────┐
        │        Next.js 15 frontend (port 3001)        │
        │  dashboard·company·chat·screener·compare       │
        │  ·portfolio·documents·news·settings            │
        └───────────────────────┬───────────────────────┘
                                │ /api/* proxy
        ┌───────────────────────▼───────────────────────┐
        │         FastAPI backend (port 8000)            │
        │  routes: companies·market·news·screener·chat   │
        │   ·documents·indices·watchlist·portfolio        │
        │  LangGraph agents + SSE chat                   │
        │  RAG pipeline (background-task ingest)         │
        │  in-memory cache                               │
        └───────────┬───────────────────────┬────────────┘
                    │                       │
           ┌────────▼────────┐      ┌───────▼────────┐
           │   PostgreSQL     │      │     Ollama      │
           │   + pgvector     │      │  llama3.1:8b    │
           └──────────────────┘      └─────────────────┘
   embeddings: sentence-transformers (all-MiniLM-L6-v2, 384-dim)
   external data: yfinance (NSE `.NS` / BSE `.BO`) · Google News RSS
```

**Multi-agent flow:** a **verified-data snapshot** (stored metrics + risk + news + portfolio + document availability) is built first, then `START → Router → [specialist(s), fanned out in parallel] → END`, then the **Synthesizer** streams the final grounded answer. The Router is an LLM planner with a deterministic heuristic fallback; specialists (Company Analyst, Comparator, Sentiment, Portfolio, Document Research) may only use numbers/passages from the snapshot or retrieved evidence.

**RAG flow:** PDF upload → background task extracts text (pdfplumber) → chunks (1000/200, page-tagged) → embeds with **sentence-transformers** (`all-MiniLM-L6-v2`, 384-dim) → stores in pgvector. Query time: **hybrid retrieval** (pgvector cosine + Postgres full-text) merged with **Reciprocal Rank Fusion** → top-5 passages → grounded answer with `[n]` citations (filename + page).

---

## Tech stack

**Frontend:** Next.js 15 (App Router, React 19) · Tailwind v4 · TradingView Lightweight Charts · Recharts · TanStack Query · Zustand · react-markdown · lucide-react

**Backend:** FastAPI · SQLAlchemy 2 (async) · Alembic · pydantic-settings

**Agents:** LangGraph (StateGraph + `MemorySaver` checkpointer, parallel `Send` fan-out) · custom async LLM factory (httpx)

**LLM:** Ollama — Llama 3.1 8B (`llama3.1:8b`), 3× retry with backoff, streaming + non-streaming

**RAG:** pdfplumber (extract) · LangChain `RecursiveCharacterTextSplitter` 1000/200 (chunk) · sentence-transformers `all-MiniLM-L6-v2` (embed, 384-dim) · pgvector cosine + Postgres full-text · Reciprocal Rank Fusion · cross-encoder reranker

**Database:** PostgreSQL + `pgvector`

**Observability & eval:** request logging + global error envelope · self-contained RAGAS-style RAG eval (faithfulness / answer-relevancy / context-precision) · optional LangFuse tracing (per-agent tokens, latency, cost)

---

## Prerequisites

1. **PostgreSQL 16+** with the `pgvector` extension enabled
2. **Ollama** running locally with the model pulled: `ollama pull llama3.1:8b`
3. **Python 3.11+** and **Node.js 18+**

---

## Quick start

```bash
# 1. Clone and set up backend
cd backend
cp ../.env.example ../.env     # edit DB password
pip install -r requirements.txt
alembic upgrade head           # run migrations
python -m app.seed.companies   # seed Nifty 50 data
uvicorn app.main:app --port 8000 --reload

# 2. In a second terminal — start frontend
cd frontend
npm install
npm run dev                    # starts on port 3001
```

Open **http://localhost:3001** — no access key needed.

---

## API endpoints

Base: `http://localhost:8000/api`

- `GET /api/health`
- `GET /api/companies` · `?sector=` · `?search=` · `GET /api/companies/{symbol}`
- `GET /api/companies/{symbol}/history?period=1M|3M|6M|1Y|5Y|MAX&interval=1d`
- `GET /api/companies/{symbol}/fundamentals`
- `GET /api/companies/{symbol}/statements/{income|balance|cashflow}?period_type=annual|quarterly`
- `GET /api/companies/{symbol}/ratios` (ROE/ROA/ROCE/D-E/current/margins/growth/FCF-yield)
- `GET /api/companies/{symbol}/risk` (rule-based flags + score)
- `GET /api/news/{symbol}` (Google News RSS + relevance)
- `GET /api/screener?sector=&market_cap_min=&market_cap_max=&pe_min=&pe_max=&roe_min=&roe_max=&dividend_yield_min=&sort_by=&desc=&limit=`
- `GET /api/chat/agents` · `POST /api/chat` · `POST /api/chat/stream` (SSE)
- `POST /api/documents` (multipart PDF) · `GET /api/documents` · `GET /api/documents/{id}` · `DELETE /api/documents/{id}`
- `GET /api/market/indices` (NIFTY 50, SENSEX, BANK NIFTY, INDIA VIX)
- `GET /api/watchlist` · `POST /api/watchlist` · `DELETE /api/watchlist/{symbol}`
- `GET /api/portfolio` · `POST /api/portfolio` · `DELETE /api/portfolio/{id}`

---

## Data coverage

- 50 Nifty 50 companies seeded.
- **48/50** carry full metrics + risk signals. **LTIM** and **TATAMOTORS** are currently unavailable on Yahoo Finance (symbol change / demerger) — name and sector are set, numeric fields intentionally left null (never fabricated).

---

## Observability & evaluation

**RAG evaluation (RAGAS-style, self-contained).** `app/eval/rag_eval.py` seeds a synthetic annual-report corpus, runs the live RAG pipeline, and computes three metrics using the app's own LLM + embeddings (no external eval service):

- **Faithfulness** — answer decomposed into atomic claims, each checked for support against retrieved context.
- **Answer relevancy** — questions generated back from the answer and cosine-compared to the original.
- **Context precision** — each retrieved passage judged for relevance, scored by rank (average precision).

**Tracing (optional, LangFuse).** Every LLM call is wrapped by a `Tracer`; with keys set, each generation logs model, prompt/completion tokens, latency, and estimated USD cost. With keys blank the tracer no-ops.

**Errors & logging.** Each request gets a short request id (`X-Request-ID`); all errors return a consistent JSON envelope `{"error": {status, message, request_id}}`.

---

## Repository layout

```
equity_prism/
├─ backend/                     FastAPI service
│  ├─ app/
│  │  ├─ main.py                app factory + router registration
│  │  ├─ agents/               LangGraph: router · 5 specialists · synthesizer · snapshot
│  │  ├─ api/routes/           companies·market·news·screener·chat·documents·
│  │  │                        indices·watchlist·portfolio·health
│  │  ├─ core/                 config · database (async engine)
│  │  ├─ llm/                  Ollama factory (retry + streaming) · LangFuse tracer
│  │  ├─ rag/                  chunking · embeddings · hybrid retrieval · ingestion
│  │  ├─ services/             market_data (yfinance) · news (RSS) · ratios · refresh · screener
│  │  ├─ models/ · schemas/    SQLAlchemy models · Pydantic schemas
│  │  ├─ seed/                 Nifty 50 list + company seeder
│  │  └─ eval/                 self-contained RAGAS-style RAG eval
│  ├─ alembic/                 migrations (enables pgvector)
│  └─ requirements.txt         dependencies
├─ frontend/                    Next.js 15 app
│  └─ src/
│     ├─ app/                  9 routes: dashboard·company·chat·compare·portfolio·
│     │                        documents·screener·news·settings
│     ├─ components/           UI (charts, tables, agent badges)
│     └─ lib/                  API client + hooks
├─ README.md
└─ LICENSE
```

---

## License

MIT — see [LICENSE](./LICENSE).

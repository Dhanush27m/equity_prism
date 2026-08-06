# Equity Prism

A live, full-stack **AI-powered equity research platform** for Indian stock markets (NSE/BSE). A LangGraph multi-agent system analyzes stocks, compares companies, tracks sentiment, manages portfolios, and answers questions over uploaded financial documents using RAG.

**🔗 Live app:** https://equity-prism.vercel.app &nbsp;·&nbsp; **API:** https://equity-prism-api.onrender.com/api/health

> The app is deployed and shareable — open the link, enter the access key, and use it in the browser. Nothing to install.

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

## Architecture (deployed)

```
        ┌──────────────────────────────────────────────┐
        │        Next.js 15 frontend — Vercel           │
        │  dashboard·company·chat·screener·compare       │
        │  ·portfolio·documents·news·settings            │
        │  (access-key gate; calls backend by absolute URL)
        └───────────────────────┬───────────────────────┘
                                │ HTTPS  (NEXT_PUBLIC_API_BASE)
        ┌───────────────────────▼───────────────────────┐
        │         FastAPI backend — Render (Docker)      │
        │  routes: companies·market·news·screener·chat   │
        │   ·documents·indices·watchlist·portfolio        │
        │  LangGraph agents + SSE chat                     │
        │  RAG pipeline (FastAPI background-task ingest)   │
        │  in-memory cache · access-key middleware         │
        └───────────┬───────────────────────┬────────────┘
                    │                       │
           ┌────────▼────────┐      ┌───────▼────────┐
           │   Supabase       │      │     Groq        │
           │ Postgres+pgvector│      │  Llama 3.3 70B  │
           └──────────────────┘      └─────────────────┘
   embeddings: fastembed (ONNX all-MiniLM-L6-v2, 384-dim, in-process)
   external data: yfinance (NSE `.NS` / BSE `.BO`) · Google News RSS
```

**Multi-agent flow:** a **verified-data snapshot** (stored metrics + risk + news + portfolio + document availability) is built first, then `START → Router → [specialist(s), fanned out in parallel] → END`, then the **Synthesizer** streams the final grounded answer. The Router is an LLM planner with a deterministic heuristic fallback; specialists (Company Analyst, Comparator, Sentiment, Portfolio, Document Research) may only use numbers/passages from the snapshot or retrieved evidence.

**RAG flow:** PDF upload → FastAPI background task extracts text (pdfplumber) → chunks (1000/200, page-tagged) → embeds with **fastembed** (`all-MiniLM-L6-v2`, 384-dim) → stores in pgvector. Query time: **hybrid retrieval** (pgvector cosine + Postgres full-text) merged with **Reciprocal Rank Fusion** → top-5 passages → grounded answer with `[n]` citations (filename + page).

---

## Tech stack

**Frontend (Vercel):** Next.js 15 (App Router, React 19) · Tailwind v4 · TradingView Lightweight Charts · Recharts · TanStack Query · Zustand · react-markdown · lucide-react

**Backend (Render, Docker):** FastAPI · SQLAlchemy 2 (async) · Alembic · pydantic-settings

**Agents:** LangGraph (StateGraph + `MemorySaver` checkpointer, parallel `Send` fan-out) · custom async LLM factory (httpx)

**LLM:** Groq API — Llama 3.3 70B (`llama-3.3-70b-versatile`), 3× retry with backoff, streaming + non-streaming

**RAG:** pdfplumber (extract) · LangChain `RecursiveCharacterTextSplitter` 1000/200 (chunk) · **fastembed** ONNX `all-MiniLM-L6-v2` (embed, 384-dim, no torch) · pgvector cosine + Postgres full-text · Reciprocal Rank Fusion

**Database:** Supabase — PostgreSQL + `pgvector`

**Observability & eval:** request logging + global error envelope · self-contained RAGAS-style RAG eval (faithfulness / answer-relevancy / context-precision) · optional LangFuse Cloud tracing (per-agent tokens, latency, cost)

Backend image: **`backend/Dockerfile.light`** (fastembed, no torch, listens on `$PORT`), deployed via **`render.yaml`**.

---

## Hosted profile (how the free deployment works)

The backend is env-switched into a lightweight profile that fits free tiers:

| Concern | Local-heavy default | Hosted profile |
|---|---|---|
| Embeddings | sentence-transformers (torch, ~2 GB) | **fastembed** ONNX (~300 MB image), `EMBEDDING_BACKEND=fastembed` |
| Re-ranker | cross-encoder | disabled, `RERANK_ENABLED=false` |
| Cache | Redis | in-process, `CACHE_BACKEND=memory` |
| PDF ingestion | Celery worker | FastAPI background task, `INGEST_MODE=background` |
| Database | local Postgres | Supabase pooler, `DB_POOLED=true` + `DB_SSL=true` |
| Access | open | shared-password gate, `ACCESS_KEY` + `NEXT_PUBLIC_REQUIRE_ACCESS_KEY=1` |

Full deploy runbook: **[DEPLOY.md](./DEPLOY.md)**.

---

## API endpoints

Base: `https://equity-prism-api.onrender.com/api` (all non-health routes require the `X-Access-Key` header)

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

- 50 Nifty 50 companies seeded into Supabase.
- **48/50** carry full metrics + risk signals. **LTIM** and **TATAMOTORS** are currently unavailable on Yahoo Finance (symbol change / demerger) — name and sector are set, numeric fields intentionally left null (never fabricated).

---

## Observability & evaluation

**RAG evaluation (RAGAS-style, self-contained).** `app/eval/rag_eval.py` seeds a synthetic annual-report corpus, runs the live RAG pipeline, and computes three metrics using the app's own LLM + embeddings (no external eval service):

- **Faithfulness** — answer decomposed into atomic claims, each checked for support against retrieved context.
- **Answer relevancy** — questions generated back from the answer and cosine-compared to the original.
- **Context precision** — each retrieved passage judged for relevance, scored by rank (average precision).

A representative run (hosted fastembed profile) scored **faithfulness ≈ 1.00, answer-relevancy ≈ 0.86, context-precision ≈ 1.00**.

**Tracing (optional, LangFuse Cloud).** Every LLM call is wrapped by a `Tracer`; with keys set, each generation logs model, prompt/completion tokens, latency, and estimated USD cost. With keys blank the tracer no-ops and `trace_id` is `null`.

**Errors & logging.** Each request gets a short request id (`X-Request-ID`); all errors return a consistent JSON envelope `{"error": {status, message, request_id}}`.

---

## Free-tier trade-offs

- **Render** backend sleeps after ~15 min idle → first visit takes ~50–60 s to wake (cold start).
- **Supabase** free project pauses after ~7 days idle → open the app weekly (or click **Restore** in the Supabase dashboard) to wake it.
- **yfinance** from datacenter IPs may be throttled; seeded data still displays.

---

## License

MIT — see [LICENSE](./LICENSE).

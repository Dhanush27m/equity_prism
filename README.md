# Equity Prism

A local, full-stack AI-powered equity research platform for Indian stock markets (NSE/BSE). A LangGraph multi-agent system analyzes stocks, compares companies, tracks sentiment, manages portfolios, and answers questions over uploaded financial documents using RAG. Everything runs locally via Docker Compose — no deployment.

> **This README tracks the _as-built_ state and is updated at the end of every phase.** Where the running stack deviates from the original spec (to fix bugs or adopt better approaches), the change is called out in **Deviations from the original spec** below.

---

## Build status

| Phase | Scope | Status |
|------:|-------|--------|
| 1 | Infrastructure (Docker Compose, DBs, extensions, Ollama, LangFuse) | ✅ Done |
| 2 | Backend foundation (models, Alembic, seed 50 Nifty stocks, company API) | ✅ Done |
| 3 | Data layer (yfinance services, ratios, risk signals, news, screener) | ✅ Done |
| 4 | Multi-agent system (LangGraph agents, LLM factory, SSE chat, LangFuse) | ✅ Done |
| 5 | RAG pipeline (PDF ingest, hybrid retrieval + RRF, rerank, citations) | ✅ Done |
| 6 | Frontend (Next.js 15, 8 pages + app shell) | ✅ Done |
| 7 | Observability + polish (trace completeness, RAG eval, error handling, docs, license) | ✅ Done |

---

## Architecture

```
                          ┌──────────────────────────────────────────┐
                          │      Next.js 15 frontend (:3001, live)     │
                          │  dashboard·company·chat·screener·compare   │
                          │  ·portfolio·documents·news·settings        │
                          └───────────────────────┬────────────────────┘
                                                  │ /api/* (proxy → :8000)
                          ┌───────────────────────▼────────────────────┐
                          │                FastAPI backend               │
                          │ routes: companies·market·news·screener·chat  │
                          │  ·documents·indices·watchlist·portfolio       │
                          │  (Phase 4) LangGraph agents + SSE chat        │
                          │  (Phase 5) RAG pipeline + Celery worker       │
                          │  services: market_data · ratios · news …      │
                          └───┬───────────┬───────────┬───────────┬──────┘
                              │           │           │           │
                        ┌─────▼───┐  ┌────▼────┐  ┌───▼────┐  ┌───▼─────┐
                        │Postgres │  │  Redis  │  │ Ollama │  │ LangFuse│
                        │+pgvector│  │ cache + │  │ llama  │  │ tracing │
                        │+timescale│ │ celery  │  │ 3.1:8b │  │(optional)│
                        └─────────┘  └─────────┘  └────────┘  └─────────┘
                              ▲            ▲
                        ┌─────┴────────────┴─────┐
                        │  Celery worker (ingest)│  PDF → chunk → embed (local MiniLM)
                        └────────────────────────┘
       external: yfinance (NSE `.NS`/BSE `.BO`) · Google News RSS · Groq API (Llama 3.3 70B)
```

Multi-agent flow (Phase 4, live): a **verified-data snapshot** (stored metrics + risk + news + portfolio + document availability) is built first, then `START → Router → [specialist(s), fanned out in parallel] → END`, then the **Synthesizer** streams the final grounded answer. The Router is an LLM planner with a deterministic heuristic fallback; specialists (Company Analyst, Comparator, Sentiment, Portfolio, Document Research) may only use numbers/passages from the snapshot or retrieved evidence. Graph state uses a LangGraph `MemorySaver` checkpointer keyed by `thread_id`. LangFuse tracing wraps every LLM call but is **optional** — it silently no-ops until keys are provided; when enabled, each generation carries its model, prompt/completion token counts, latency, and an estimated USD cost (Groq priced per model; Ollama treated as free/local).

RAG flow (Phase 5, live): PDF upload → Celery worker extracts (pdfplumber) → chunks (1000/200, page-tagged) → embeds locally (`all-MiniLM-L6-v2`, 384-d) → stores in pgvector. Query time: **hybrid retrieval** (pgvector cosine via HNSW + Postgres full-text via GIN) merged with **Reciprocal Rank Fusion** → **cross-encoder rerank** (`ms-marco-MiniLM-L-6-v2`) → top-5 passages → grounded answer with `[n]` citations (filename + page). Every document answer is recorded in the `rag_traces` evidence table (question → exact chunk IDs + citations).

---

## Tech stack (as built)

**Backend:** FastAPI · SQLAlchemy 2 (async) · Alembic · pydantic-settings · Celery + Redis
**Agents:** LangGraph (StateGraph + `MemorySaver` checkpointer, parallel `Send` fan-out) · custom async LLM factory (httpx, no LangChain provider glue)
**LLM:** Groq API (Llama 3.3 70B `llama-3.3-70b-versatile`) primary → Ollama (`llama3.1:8b`) fallback, 3× retry with 1/2/4s backoff, streaming + non-streaming
**RAG:** pdfplumber (extract) · LangChain `RecursiveCharacterTextSplitter` 1000/200 (chunk) · sentence-transformers `all-MiniLM-L6-v2` (embed, local, 384-d) · pgvector HNSW + Postgres GIN full-text · Reciprocal Rank Fusion · cross-encoder `ms-marco-MiniLM-L-6-v2` rerank (local) · Celery worker for async ingestion
**Database:** PostgreSQL 16 via `timescale/timescaledb-ha:pg16` with `pgvector` + `timescaledb` extensions. Two DBs: `equity_prism` (app), `langfuse` (observability).
**Cache/Queue:** Redis 7 (db0 cache · db1 Celery broker · db2 Celery result)
**Data:** yfinance **1.5.2** · feedparser (Google News RSS) · user-uploaded PDFs
**Observability:** LangFuse self-hosted (`langfuse/langfuse:2`, Python SDK `langfuse 2.53.9`) — optional, auto-disabled when keys are blank; each LLM generation records model, token usage, latency, and estimated cost · request logging + global error envelope · self-contained RAGAS-style RAG eval (faithfulness / answer-relevancy / context-precision)
**Frontend (live):** Next.js 15 (App Router, React 19) · Tailwind v4 (CSS-first, class dark mode) · TradingView Lightweight Charts 4 · Recharts · TanStack Query · Zustand (chat history in localStorage) · react-markdown · lucide-react. Runs on **:3001**, proxies `/api/*` → `:8000`. UI primitives are hand-rolled in shadcn style (see deviations).

Pinned backend deps: `fastapi 0.115.6`, `uvicorn 0.34.0`, `pydantic 2.10.5`, `sqlalchemy 2.0.37`, `asyncpg 0.30.0`, `psycopg[binary] 3.2.4`, `alembic 1.14.1`, `pgvector 0.3.6`, `redis 5.2.1`, `httpx 0.28.1`, `yfinance 1.5.2`, `pandas 2.2.3`, `feedparser 6.0.11`, `langgraph 0.2.62`, `langfuse 2.53.9`, `celery 5.4.0`, `python-multipart 0.0.20`, `pdfplumber 0.11.4`, `langchain-text-splitters 0.3.4`, `sentence-transformers 3.3.1`.

---

## Docker services

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| db | timescale/timescaledb-ha:pg16 | 5432 | pgvector + timescaledb; DBs `equity_prism`, `langfuse` |
| redis | redis:7-alpine | 6379 | cache + Celery broker |
| ollama | ollama/ollama | 11434 | `llama3.1:8b` pulled |
| langfuse | langfuse/langfuse:2 | 3000 | LLM tracing UI |
| backend | ./backend (python:3.12-slim) | 8000 | FastAPI (uvicorn) |
| worker | equity-prism-backend:latest | — | Celery worker for async PDF ingestion (shares the backend image) |

All volumes/networks are prefixed `equity-prism_`. Volumes: `db_data`, `redis_data`, `ollama_data`, `hf_cache` (local embed/rerank models), `uploads` (shared backend↔worker PDF store). Frontend (Phase 6) runs outside Docker via `npm run dev`.

---

## Backend layout

```
backend/app/
  core/        config.py (pydantic-settings), database.py (async engine/session),
               observability.py (request logging + request-id + global error envelope)
  models/      user, company, financials, portfolio, document (+chunk w/ Vector(384)),
               watchlist, metrics (FinancialMetric, RiskSignal), rag (RagTrace)
  schemas/     company, …
  services/    yf_session (Redis cache), market_data (OHLCV/fundamentals/statements,
               .NS→.BO fallback), ratios (metrics + risk engine), news (RSS+relevance),
               screener, refresh (populate metrics + risk)
  llm/         factory (Groq→Ollama, retry/backoff, complete + stream_complete),
               tracing (optional LangFuse Tracer, no-ops without keys)
  rag/         embeddings (MiniLM 384-d), reranker (cross-encoder), chunking (pdfplumber
               + RecursiveCharacterTextSplitter, page-tagged), retrieval (vector + full-text
               + RRF merge), pipeline (retrieve → rerank → context + citations)
  tasks/       celery_app (Redis broker db1 / result db2), ingest (extract→chunk→embed→store)
  agents/      state (AgentState TypedDict), snapshot (symbol resolve + verified-data
               snapshot builder + has_documents), router (LLM planner + deterministic fallback),
               company_analyst, comparator, sentiment, portfolio, document_research,
               synthesizer, graph (StateGraph + MemorySaver + parallel Send dispatch)
  seed/        nifty50 (symbol list), seed_companies (upsert 50 stocks)
  eval/        corpus (synthetic annual-report pages + questions),
               rag_eval (RAGAS-style faithfulness / answer-relevancy / context-precision)
  api/         deps (local user), routes/ (health, companies, market, news, screener,
               chat, documents, indices, watchlist, portfolio)
  alembic/     migrations (7817517903cd initial, 002e0f3c7c67 metrics+risk,
               c4f1a2b3d5e6 rag_traces + HNSW/GIN chunk indexes)
```

## Frontend layout

```
frontend/src/
  app/          layout (providers + shell), page (dashboard), company/[symbol],
                chat, compare, portfolio, documents, screener, news, settings
  components/   app-shell, sidebar, header (stock search), providers (QueryClient +
                theme), price-chart (Lightweight Charts), markdown, citations,
                common (Delta/MetricCard/badges), states, ui/ (card, button, badge,
                input, table, tabs, skeleton, spinner)
  lib/          api (fetch + SSE streamChat), hooks (TanStack Query per endpoint),
                types, utils (INR/%/date formatters), store (zustand chat history),
                use-chat (SSE → store)
```

8 pages: **Dashboard** (indices, watchlist, portfolio summary, quick-ask) · **Company** (candlestick+volume chart, metrics, statement tabs, risk) · **Prism Chat** (SSE streaming, agent badges, citations, history sidebar) · **Compare** (2–5 picker, metric bar charts, AI verdict) · **Portfolio** (add/remove, live P&L, sector donut, Analyze) · **Documents** (drag-drop upload, status, RAG Q&A) · **Screener** (filters, sortable table) · **News** (sentiment gauge, headline badges). Plus **Settings**.

---

## API endpoints (current)

- `GET /api/health`
- `GET /api/companies` · `?sector=` · `?search=` · `GET /api/companies/{symbol}`
- `GET /api/companies/{symbol}/history?period=1M|3M|6M|1Y|5Y|MAX&interval=1d`
- `GET /api/companies/{symbol}/fundamentals`
- `GET /api/companies/{symbol}/statements/{income|balance|cashflow}?period_type=annual|quarterly`
- `GET /api/companies/{symbol}/ratios` (ROE/ROA/ROCE/D-E/current/margins/growth/FCF-yield)
- `GET /api/companies/{symbol}/risk` (rule-based flags + score)
- `GET /api/news/{symbol}` (Google News RSS + relevance)
- `GET /api/screener?sector=&market_cap_min=&market_cap_max=&pe_min=&pe_max=&roe_min=&roe_max=&dividend_yield_min=&sort_by=&desc=&limit=`
- `GET /api/chat/agents` (metadata for the 6 agents, incl. Document Research)
- `POST /api/chat` (multi-agent answer, JSON: plan, per-agent fragments, citations, agent_meta, synthesis, trace_id)
- `POST /api/chat/stream` (SSE: `status → snapshot → plan → agent_result… → synthesis_start → token… → done`)
- `POST /api/documents` (multipart PDF upload → enqueues async ingestion; returns doc row)
- `GET /api/documents` (list with status: pending/processing/ready/failed, num_pages, num_chunks)
- `GET /api/documents/{id}` · `DELETE /api/documents/{id}` (cascades chunks + removes file)
- `GET /api/market/indices` (NIFTY 50, SENSEX, BANK NIFTY, INDIA VIX — value + day change)
- `GET /api/watchlist` · `POST /api/watchlist` · `DELETE /api/watchlist/{symbol}`
- `GET /api/portfolio` (holdings w/ live P&L + summary + sector allocation) · `POST /api/portfolio` · `DELETE /api/portfolio/{id}`

---

## Data coverage

- 50 Nifty 50 companies seeded.
- **48/50** carry full live metrics + risk signals. **LTIM** and **TATAMOTORS** are currently unavailable on Yahoo Finance (404 under `.NS`/`.BO`; Tata Motors demerger and the LTIMindtree symbol change) — their name/sector are set, numeric fields intentionally left null (never fabricated). They backfill automatically once Yahoo serves them.

---

## RAG pipeline (document research)

Ask questions over your own uploaded PDFs (annual reports, filings, research notes). Routed through the **same** `/api/chat` endpoint — the Router classifies document questions as `document_research`.

1. **Ingestion (async, Celery worker):** `pdfplumber` extracts text per page → `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap) chunks it, tagging each chunk with its page → `all-MiniLM-L6-v2` embeds locally (384-d) → chunks + vectors stored in `document_chunks` (pgvector). Document status flows `pending → processing → ready` (or `failed` with an error message).
2. **Hybrid retrieval:** pgvector cosine similarity (HNSW index) **and** Postgres full-text search (`to_tsvector`/`plainto_tsquery`, GIN index) run independently, then merge via **Reciprocal Rank Fusion** (k=60) with de-duplication.
3. **Rerank:** the cross-encoder `ms-marco-MiniLM-L-6-v2` re-scores the merged candidates and keeps the top 5.
4. **Grounded answer + citations:** the Document Research agent answers using **only** the retrieved passages, with inline `[n]` markers. Citations (filename + page + snippet + chunk id) are returned alongside the answer, and every answer is logged to the `rag_traces` evidence table (question → exact chunk IDs).

Models are downloaded once on first use and cached in the `equity-prism_hf_cache` volume (shared by backend and worker).

---

## Observability & evaluation

**Tracing (LangFuse, optional).** Every LLM call is wrapped by a `Tracer`. When LangFuse keys are set, each generation is logged with its **model, prompt/completion token counts, latency, and an estimated USD cost** (Groq priced per model in `llm/tracing.py`; local Ollama treated as free). Streaming synthesis captures usage via Groq's `include_usage` stream option. With keys blank the tracer no-ops and `trace_id` is `null` — nothing else changes.

**Request logging & errors.** `core/observability.py` installs a middleware that assigns each request a short **request id** (returned as `X-Request-ID`) and logs `method path -> status (ms)`. All errors return a consistent JSON envelope `{"error": {"status", "message", "request_id", "detail?}}` — `HTTPException`, request-validation (422), and any unhandled exception (500, logged with a stack trace) alike.

**RAG evaluation (RAGAS-style, self-contained).** `python -m app.eval.rag_eval` seeds a synthetic 5-page annual report, runs the live RAG pipeline over 7 questions, and computes three RAGAS metrics using the app's own LLM + embeddings (no external eval service, no reference answers needed):

- **Faithfulness** — answer is decomposed into atomic claims; each is checked for support against the retrieved context.
- **Answer relevancy** — questions are generated back from the answer and cosine-compared (MiniLM) to the original question.
- **Context precision** — each retrieved passage is judged for relevance and scored by rank (average precision).

The temporary corpus is cleaned up afterward. A representative run scored **faithfulness ≈ 1.00, answer-relevancy ≈ 0.85, context-precision ≈ 1.00**.

---

## Setup & run

Prerequisites: Docker Desktop, and a free Groq API key from https://console.groq.com.

```bash
# 1. Configure environment
cp .env.example .env
#    then set GROQ_API_KEY in .env
#    LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY are OPTIONAL — the multi-agent chat
#    works without them; add them later to enable tracing (see note below).

# 2. Start the stack (db, redis, ollama, langfuse, backend, worker)
#    First build installs torch + sentence-transformers — allow several minutes.
docker compose up -d --build

# 3. Pull the local LLM fallback model
docker exec equity-prism_ollama ollama pull llama3.1:8b

# 4. Create the schema
docker exec equity-prism_backend alembic upgrade head

# 5. Seed the 50 Nifty stocks (uses yfinance)
docker exec equity-prism_backend python -m app.seed.seed_companies

# 6. Populate financial metrics + risk signals (~5-7 min)
docker exec equity-prism_backend python -m app.services.refresh

# 7. Start the frontend (outside Docker, on port 3001)
cd frontend
npm install
npm run dev      # → http://localhost:3001
```

Verify: backend health at http://localhost:8000/api/health, LangFuse UI at http://localhost:3000.

Try the multi-agent chat:

```bash
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"Compare TCS and Infosys, and what is the latest news sentiment?"}'
```

Try document research (RAG):

```bash
# Upload a PDF (first ingestion also downloads the local embedding model, ~90 MB)
curl -s -X POST http://localhost:8000/api/documents -F "file=@/path/to/report.pdf"
# Poll until status is "ready"
curl -s http://localhost:8000/api/documents
# Ask about it — the Router routes this to document_research and returns citations
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"According to the uploaded report, what was total revenue and the key risks?"}'
```

Run the RAG evaluation (seeds its own corpus, cleans up after):

```bash
docker exec equity-prism_backend python -m app.eval.rag_eval
```

**Enable LangFuse tracing (optional):** open http://localhost:3000, create an account + a project, copy the Public/Secret keys from Project Settings → API Keys into `.env` (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`), then `docker compose up -d backend worker`. Once enabled, traces show per-agent generations with token counts, latency, and cost. Without keys, chat still works and `trace_id` is simply `null`.

> Refresh tip: run the metrics refresh with **no concurrent** `docker compose build/up` — recreating the backend container mid-run kills the `docker exec` (exit 137).

---

## Deploy for free (shareable link)

The app can be hosted at **$0** on **Vercel** (frontend) + **Hugging Face Spaces** (backend, 16 GB free) + **Supabase** (Postgres + pgvector) + **Groq** (LLM). The **same code** runs locally and hosted — a "hosted profile" is switched on purely by env vars, so `docker compose` locally is untouched:

- `CACHE_BACKEND=memory` (no Redis) · `INGEST_MODE=background` (no Celery worker — PDF ingest runs as a FastAPI background task) · Ollama dropped (Groq only)
- `DB_POOLED=true` + `DB_SSL=true` for Supabase's pooler (asyncpg `statement_cache_size=0`); only `pgvector` is required (the initial migration enables it)
- `NEXT_PUBLIC_API_BASE` points the browser at the remote backend (CORS open); `ACCESS_KEY` + `NEXT_PUBLIC_REQUIRE_ACCESS_KEY=1` add a shared-password gate so a public URL can't burn your Groq quota
- Backend HF image: `backend/Dockerfile.hf` (CPU-only torch, listens on `$PORT`)

**Full step-by-step: [DEPLOY.md](./DEPLOY.md).** Trade-offs on free tiers: cold starts (~30–60 s wake), Supabase's ~7-day idle pause, and possible yfinance throttling from datacenter IPs.

---

## Deviations from the original spec (kept intentionally)

- **App database name is `equity_prism`** (underscore), not the spec's hyphenated form — avoids Postgres identifier-quoting friction.
- **yfinance upgraded 0.2.54 → 1.5.2.** 0.2.54 had a fatal cookie/crumb bug (`AttributeError: 'str' object has no attribute 'name'`) that masqueraded as rate-limiting. 1.5.2 with the default session is stable and does not throttle on rapid calls. **`curl_cffi` was removed** (an earlier workaround, no longer needed and could re-trigger the cookie bug).
- Ratios engine computes ROE/ROA/current-ratio/ROCE/FCF from financial statements when yfinance's `info` omits them.
- **LangFuse is optional, not a hard dependency.** The `Tracer` wrapper no-ops when keys are blank, so the multi-agent system runs fully without it (the original spec implied LangFuse was required to build Phase 4). Add keys any time to light up tracing.
- **The LLM factory is a thin custom async client (httpx), not LangChain chat models.** Groq and Ollama are called directly for tighter control over retry/backoff, JSON mode, and token streaming; LangGraph is still used for the agent graph itself.
- **`sentence-transformers` pulls in full CUDA `torch`.** The image is several GB and the first build is slow; inference runs on CPU regardless (no GPU needed). A CPU-only torch pin can slim it later — deferred to keep the locked stack simple.
- **Document research reuses the `/api/chat` endpoint** (Router classifies `document_research`) rather than a separate Q&A route, matching the spec's "same chat endpoint" instruction. A dedicated `rag_traces` evidence table was added (beyond the base spec) for citation auditing.
- **Frontend pinned to Next.js 15 / React 19 / Tailwind v4.** `create-next-app@latest` now ships Next 16; pinned back to 15 to honor the locked stack. Tailwind v4 uses CSS-first config (`@custom-variant dark`, `@theme inline` tokens) instead of `tailwind.config.js`.
- **UI primitives are hand-rolled in shadcn style, not the `shadcn/ui` CLI.** Equivalent Card/Button/Badge/Table/Tabs/Input/Skeleton components live in `components/ui`, styled with the Tailwind token system — avoids the interactive `shadcn init`/Radix dependency while keeping the same look and API.
- **`dividend_yield` is stored in percent units** (e.g. 0.47 = 0.47%), unlike `roe`/margins which are fractions — the frontend formats it accordingly. **News sentiment badges use a lightweight client-side keyword heuristic**; the LLM-grounded sentiment read lives in the chat Sentiment agent (linked via "Deep sentiment via AI").
- **Two new backend route groups added for the UI**: `watchlist` and `portfolio` CRUD (models existed since Phase 2), plus `market/indices` (yfinance `^NSEI`/`^BSESN`/`^NSEBANK`/`^INDIAVIX`).
- **RAG evaluation implements the RAGAS metric definitions in-house rather than depending on the `ragas` library.** The `ragas` package assumes an OpenAI-style judge and pulls a heavy LangChain/datasets tree; instead `app/eval/rag_eval.py` computes faithfulness, answer-relevancy, and context-precision using the project's existing Groq/Ollama LLM factory and local MiniLM embeddings — no external eval dependency, and it runs fully offline-capable against the live pipeline.

---

## License

MIT — see [LICENSE](./LICENSE).

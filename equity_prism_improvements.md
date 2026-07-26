# Equity Prism — Improvements & Completion Plan

Ideas distilled from six reference projects (TradingAgents, LangAlpha, FinSight-AI, Financial_Agentic_RAG, 11-agent Financial Research Analyst, ai-equity) and mapped onto our **locked stack** (FastAPI · LangGraph · SQLAlchemy async · Celery/Redis · PostgreSQL+pgvector+TimescaleDB · Groq→Ollama · Next.js 15). Nothing here substitutes the locked stack — these are enhancements that fit inside it.

Legend: **[IN-SPEC]** already required by the build spec, improved here · **[ADOPT]** low-cost addition worth doing now · **[OPTIONAL]** post-MVP differentiator.

---

## 1. Multi-agent system (Phase 4) — make reasoning explicit and grounded

- **[IN-SPEC] Router as a planner, not just a classifier.** Besides the query type + symbols, have the Router emit a small structured "plan" (which specialists to call, in what order, extracted params). LangAlpha's planning-first flow reduces wasted LLM/data calls. Keep our `START → Router → specialist(s) → Synthesizer → END`, but allow the Router to fan out to multiple specialists when a query needs it (e.g. "analyze and compare").
- **[ADOPT] Verified-data grounding.** Before an agent reasons, assemble a "data snapshot" dict (quote, ratios, statement lines, news list) and pass it in the prompt as the ONLY source of numbers. Instruct agents to never invent figures. TradingAgents anchors every numeric claim to a verified snapshot — this is the cheapest hallucination guard.
- **[ADOPT] Bull/Bear mini-debate inside the Comparator & Company Analyst.** Instead of a single verdict, generate a short bull case + bear case, then a balanced conclusion. One extra LLM turn, big credibility gain. This is TradingAgents' core pattern, scaled down.
- **[ADOPT] Reflection memory (lightweight).** A `agent_reflections` table (or reuse LangFuse) storing past analyses + what changed, injected as context on repeat queries for the same symbol. Don't build the full trading-memory loop — just "last analysis summary for this ticker."
- **[IN-SPEC] LLM factory resilience.** Groq→Ollama fallback with 3x backoff (1/2/4s) is specified; also add: per-provider timeouts, and a deterministic non-LLM fallback for structured outputs (FinSight's "dual-mode inference") so tests/demos run even if both LLMs are down.
- **[ADOPT] Separate synthesizer/reporter concern.** Keep the Synthesizer purely about formatting + citations (LangAlpha's reporter split) so specialist prompts stay focused on analysis.
- **[ADOPT] Checkpointing.** Use LangGraph's checkpointer (Postgres/Redis saver) so long chat turns can resume and so LangFuse traces line up with graph state.

## 2. RAG pipeline (Phase 5) — agentic retrieval + real evidence tracing

- **[IN-SPEC++] Hybrid retrieval gateway with dedup.** We already plan pgvector cosine + PG full-text + RRF. Add explicit dedup/merge at a `HybridRetrievalGateway` layer (FinSight) and metadata filters (filename, page, and — once parsed — company/fiscal period).
- **[ADOPT] Agentic RAG loop for document Q&A.** Decompose the question into sub-queries → retrieve per sub-query → **grade chunk relevance** (drop low-relevance) → rerank (cross-encoder, already specced) → generate → **answer-vs-source check** to flag unsupported sentences. This is Financial_Agentic_RAG's pipeline and directly raises RAGAS faithfulness.
- **[ADOPT] Evidence-tracing table.** Add `rag_traces` binding every answer to the exact chunk IDs used (with page + snippet). Powers: citations in the UI, hallucination-risk metric, and RAGAS regression cases. This is FinSight's strongest idea and fits our citation requirement exactly.
- **[ADOPT] Snapshot-hash cache keys.** Cache generated analyses/answers keyed by a hash of the underlying data snapshot (not the prompt string), so cached conclusions auto-invalidate when source data changes. Store `data_snapshot_hash` on cached reports.

## 3. Data layer (Phase 3) — resilience + richer signals

- **[IN-SPEC] Reuse the curl_cffi impersonation session for ALL yfinance calls** (see `[[yfinance-data-source]]` memory). Add light caching in Redis (quote/ratios TTL) so we don't refetch on every request and to reduce throttling.
- **[ADOPT] Multi-source fallback for prices/statements.** yfinance primary; on failure fall back to `.BO` (BSE) suffix, then a secondary free source. The 11-agent app's auto-fallback chain is what makes data layers production-grade — and it's exactly what bit us with LTIM/TATAMOTORS.
- **[ADOPT] Risk-signal + earnings-quality engine.** Pre-compute risk flags (high debt/equity, margin compression, negative FCF, promoter-pledge if available) and an earnings-quality score (EPS surprise pattern, one-time items) into a `risk_signals` table. Use them both as prompt context AND as screener/ranking filters (FinSight + 11-agent).
- **[IN-SPEC] Ratios** (ROE/ROA/ROCE/D-E/current/margins/EPS & rev growth/FCF yield) — compute once, store in a `financial_metrics` table with a definitions endpoint, rather than recomputing per request.

## 4. Backend engineering (cross-cutting) — production hygiene

- **[ADOPT] Celery task idempotency.** Idempotency key + status/attempt/error columns on document-ingestion tasks; a recovery sweep for stuck `RUNNING` tasks (FinSight's workflow-task model, simplified — no need for fencing tokens at our scale).
- **[ADOPT] Versioned outputs.** Store model, source (groq/ollama), generated_at, and snapshot hash on every AI report for audit + cache invalidation.
- **[ADOPT] Observability beyond LangFuse.** Add `/metrics` (basic counters) and structured request logging; LangFuse covers LLM traces (tokens/latency/cost) as specced.

## 5. Frontend (Phase 6) — trust & transparency (ai-equity's gap = our edge)

- **[ADOPT] Reasoning transparency panel.** Show the agent path taken (Router → which specialists), the data snapshot used, and a link to the LangFuse trace. ai-equity's weakness is opaque agent logic — surfacing it is a differentiator.
- **[ADOPT] Evidence/citation UX.** Expandable source cards (filename + page + snippet), and highlight which answer sentences are grounded vs model-inferred (from the answer-vs-source check).
- **[IN-SPEC] Everything else** (8 pages, dark mode, skeletons, SSE streaming) stays as specified.

## 6. Evaluation & "definition of done" (Phase 7) — don't skip

- **[IN-SPEC] RAGAS** faithfulness / answer-relevancy / context-precision on 5–10 fixed QA cases.
- **[ADOPT] Evaluation-as-regression-gate.** Freeze a small golden set (RAG QA + a few agent queries) and assert metrics stay above thresholds; run before calling a phase "done" (FinSight's regression gates).
- **[ADOPT] Grounding metrics:** evidence coverage (% answer backed by chunks) + hallucination-risk flag, surfaced in the eval script.

## 7. Indian-market differentiators — **[OPTIONAL]**, post-MVP

Thematic clustering (IT/EV/green/defense), promoter-pledge & insider/block-deal tracker, macro bridge (IIP/PMI/GST vs sectors), DCF with Indian WACC/tax inputs, tax-loss harvesting under Indian capital-gains rules, DRHP/exchange-announcement ingestion. High value, but only after the 7 phases are complete and stable.

---

## Recommended sequencing (keeps us on the locked 7-phase path)
1. Finish **Phase 3** with: curl_cffi reuse everywhere, Redis cache, `financial_metrics` + `risk_signals` tables, `.BO` fallback (also backfills LTIM/TATAMOTORS).
2. **Phase 4**: Router-as-planner (multi-specialist fan-out), verified-data snapshots, bull/bear mini-debate, LangGraph checkpointer, LangFuse tracing.
3. **Phase 5**: agentic RAG loop + `rag_traces` evidence table + snapshot-hash cache.
4. **Phase 6**: add reasoning-transparency + evidence UX on top of the 8 specced pages.
5. **Phase 7**: RAGAS + regression gate + grounding metrics + README.

Adopted architecture decisions are recorded in the `architecture-decisions` project memory so future sessions build to this plan.

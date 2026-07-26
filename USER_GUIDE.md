# Equity Prism — User Guide

How to use Equity Prism as a user: what each part of the app does and the things you can do with it.

Equity Prism is a local AI equity-research assistant for Indian stocks (NSE/BSE). It combines live market data, financial statements, a multi-agent AI analyst (named **Prism**), and document Q&A over your own PDFs — all running on your own machine.

> This is a research and learning tool. It is **not** personalised investment advice.

---

## 1. Getting started

**Start the backend** (once, from the project folder):

```bash
docker compose up -d
```

**Start the app (frontend):**

```bash
cd frontend
npm run dev
```

Then open **http://localhost:3001** in your browser.

You navigate using the **left sidebar**. The **top bar** has a stock search box (type a name or symbol like `TCS` or `Reliance`) and a **light/dark theme toggle**.

---

## 2. What you can do — feature by feature

### Dashboard (home)
Your at-a-glance market snapshot.
- **Live index cards** — NIFTY 50, SENSEX, BANK NIFTY, and INDIA VIX with the day's change.
- **Watchlist** — the stocks you're tracking, with price and a colour-coded risk badge.
- **Portfolio summary** — total value, profit/loss, and a sector breakdown of your holdings.
- **Quick-ask box** — type a question and jump straight into a chat with Prism.

### Company page
Deep-dive on a single stock. Get here from search, the watchlist, or the screener.
- **Interactive price chart** — candlesticks + volume, with range buttons (1M / 3M / 6M / 1Y / 5Y).
- **Key metrics** — P/E, P/B, ROE, ROCE, Debt/Equity, Dividend Yield.
- **Financial statements** — Income, Balance Sheet, Cash Flow, switchable between annual and quarterly.
- **Risk signals** — rule-based flags (e.g. high leverage, weak margins) with an overall risk level.
- **Watch** button to add it to your watchlist, and **Ask AI** to analyse it in chat.

### Prism Chat (the AI analyst)
Ask questions in plain English. Behind the scenes a **team of specialist agents** collaborates:
- **Router** decides which specialists are needed.
- **Company Analyst** — bull/bear analysis of a single stock.
- **Comparator** — side-by-side comparison of two or more stocks.
- **Sentiment** — reads recent news sentiment.
- **Portfolio** — reasons about your actual holdings.
- **Document Research** — answers from your uploaded PDFs (see Documents below).
- **Synthesizer** — writes the final answer.

What you'll see: the answer **streams in live**, tagged with **badges** showing which agents contributed, and (where relevant) **citations** you can expand. Your chat **history** is saved in the sidebar so you can revisit past threads.

**Example questions to try:**
- "Analyze TCS as an investment."
- "Compare TCS and Infosys on valuation and profitability."
- "What's the latest news sentiment on HDFC Bank?"
- "How is my portfolio positioned across sectors?"
- "Which is cheaper right now, Reliance or ITC, and why?"

> Every number Prism uses comes from the verified data snapshot — it won't invent figures. If a metric is missing, it says "not available."

### Compare
Pick **2 to 5 stocks** and see them side by side.
- Metric **bar charts** (P/E, ROE, Debt/Equity, Net margin).
- A full **metrics table**.
- An **AI verdict** — click "Ask Prism to compare" for a streamed written comparison.

### Portfolio
Track your holdings and see live performance.
- **Add a holding** — symbol, quantity, and average buy price.
- **Live P&L table** — current price, market value, and profit/loss per holding.
- **Sector allocation** donut.
- **Analyze** — ask Prism to review the whole portfolio.

### Documents (ask questions about your own PDFs)
Upload financial documents and query them — this is the **RAG** feature.
1. **Drag & drop a PDF** (annual report, filing, research note) onto the upload area.
2. It's processed in the background — status goes **pending → processing → ready**.
3. Once ready, **ask questions about it**. Answers come back grounded in the document, with **citations showing the source filename and page number**.

**Example document questions:**
- "According to the uploaded report, what was total revenue and how did it grow?"
- "What risks does management highlight?"
- "What is the dividend and payout ratio in this filing?"

> The answer only uses what's actually in your document — if the PDF doesn't contain the answer, Prism will say so rather than guess.

### Screener
Filter the Nifty 50 by fundamentals.
- Filters: **sector, minimum market cap, P/E range, minimum ROE, minimum dividend yield**.
- **Sortable** results table — click a column header to sort.
- Click any row to open that company's page, or the **star** to add it to your watchlist.

### News
Market news with a sentiment read.
- A **sentiment gauge** and headlines tagged **bullish / neutral / bearish**.
- Useful for a quick pulse before a deeper dive in chat.

### Settings
Theme and app preferences.

---

## 3. Tips & good to know

- **Symbols:** use NSE tickers without a suffix in the UI (e.g. `TCS`, `RELIANCE`, `INFY`). The app handles the `.NS`/`.BO` mapping.
- **Two stocks with no data:** `LTIM` and `TATAMOTORS` currently have no numbers from Yahoo Finance (a demerger / symbol change) — their name and sector show, but metrics are blank by design (never faked).
- **Citations:** in chat, expand the citations under an answer to see exactly what a claim is based on — stored financials, news, or a document page.
- **Freshness:** market data is cached and refreshed periodically. To force-refresh all stocks, an admin can run the refresh job (see README).
- **Privacy:** everything runs locally. Your uploaded documents, portfolio, and chats stay on your machine. Only the LLM prompts go to the Groq API (or fully local Ollama as fallback).
- **Agent traces (optional):** if LangFuse is enabled, the sidebar "Agent Traces" link opens a dashboard showing each AI call with token counts, latency, and cost.

---

## 4. A typical workflow

1. **Search** a stock in the top bar → land on its **Company** page to review chart, metrics, and risk.
2. Hit **Ask AI** to get Prism's bull/bear view.
3. **Compare** it against a peer or two.
4. Add it to your **Watchlist** or record a position in **Portfolio**.
5. **Upload** the company's annual report on the **Documents** page and ask targeted questions about it.
6. Check **News** for sentiment before deciding.

---

## 5. Quick troubleshooting

| Symptom | Fix |
|---------|-----|
| Page won't load at :3001 | Frontend isn't running — `cd frontend && npm run dev` |
| Data/charts empty or errors | Backend may be down — `docker compose up -d`, then check http://localhost:8000/api/health |
| Uploaded PDF stuck on "processing" | The background worker needs to be running — `docker compose up -d worker` |
| Chat is slow or errors once, then works | The AI briefly hit a rate limit and retried/fell back to the local model — try again |

For full setup and architecture, see **[README.md](./README.md)**. For every URL and endpoint, see **[LINKS.md](./LINKS.md)**.

# FintelPulse

> AI-powered equity research desk — multi-agent analysis, honest self-scoring, free-forever stack.

**FintelPulse** lets you search any stock ticker and get a structured research verdict from five parallel AI analysts (news, fundamentals, technical, ownership, risk). Every prediction is logged and scored nightly against actual market outcomes — the system holds itself accountable.

---

## Live Demo

> Deployed on Streamlit Community Cloud — link here once live.

---

## Key Features

| Feature | Detail |
|---|---|
| 5 parallel AI agents | News · Fundamentals · Technical · Ownership · Risk — run simultaneously |
| Portfolio Manager | Synthesizes all agents into one verdict; always includes a downside driver |
| Concrete analysis | Agents required to cite actual figures (P/E, %, beta) — no vague adjectives |
| Smart caching | Results cached 4 hours — repeat queries are instant |
| Self-scoring pipeline | Nightly job resolves every prediction against real closing prices |
| Scoring logic | Bullish/Bearish correct if move > ±1%; Neutral correct if move stays within ±1% |
| All-time accuracy | Cumulative hit-rate shown on homepage, grows with every scored prediction |
| Dynamic Nifty 50 universe | Daily job fetches live index constituents from NSE's official CSV |
| Top Gainers / Losers | Green/red panels with fallback to best/worst performers on all-red days |
| Fully free stack | Gemini · Neon · Streamlit Cloud · GitHub Actions — no paid services |

---

## Architecture

![FintelPulse Architecture](docs/architecture.svg)

```
User query
    │
    ▼
Orchestrator ──► Cache hit? ──► Return instantly (⚡ cached)
    │
    │ Cache miss
    ▼
┌──────────────────────────────────────────┐
│  5 Specialist Agents (parallel)          │
│  News · Fundamentals · Technical         │
│  Ownership · Risk                        │
└──────────────────────────────────────────┘
    │
    ▼
Portfolio Manager (Gemini) ──► Structured JSON verdict
    │
    ▼
Neon Postgres ──► verdict_cache + predictions log
    │
    ▼
Nightly job (10 PM IST) ──► resolve outcomes ──► all-time accuracy
Daily job   (4 PM IST)  ──► Nifty 50 movers + most-viewed lists
```

---

## Tech Stack

| Layer | Tool | Notes |
|---|---|---|
| Language | Python 3.12 | |
| AI model | Gemini 3.1 Flash Lite | Free tier, higher rate limits |
| Market data | yfinance | Prices, fundamentals, ownership |
| News | Google News RSS | No API key needed |
| Index constituents | NSE official CSV | Live Nifty 50 list, no auth required |
| Database | Neon Postgres (free tier) | Serverless, scales to zero |
| Scheduler | GitHub Actions (cron) | Free on public repos |
| Frontend & hosting | Streamlit Community Cloud | Free |

---

## Scheduled Jobs

| Job | Schedule (IST) | What it does |
|---|---|---|
| Daily Discovery | 4:00 PM weekdays | Fetches live Nifty 50 constituents, builds movers + most-viewed |
| Nightly Accuracy | 10:00 PM weekdays | Scores predictions against closing prices, updates hit-rate |

> **Why these times:** Daily Discovery runs 30 min after NSE close (3:30 PM). Nightly Accuracy runs after both NSE (3:30 PM) and NYSE (9:30 PM) close so US stocks are also covered.

Add `GEMINI_API_KEY` and `DATABASE_URL` as **repository secrets** under `Settings → Secrets and variables → Actions`.

---

## Prediction Scoring Logic

| Prediction | Marked correct if |
|---|---|
| Bullish | Closing price moves **> +1%** vs open |
| Bearish | Closing price moves **< -1%** vs open |
| Neutral | Price stays **within ±1%** of open |

Predictions for a given day are scored the same night (10 PM IST), after market close.

---

## Database Schema

| Table | Purpose |
|---|---|
| `verdict_cache` | Latest verdict per ticker (4-hour TTL) |
| `predictions` | Every bullish / neutral / bearish call with outcome |
| `accuracy` | All-time hit-rate scorecard |
| `discovery_list` | Daily movers and most-viewed lists |
| `ticker_views` | Query count per ticker |

---

## Running Locally

### Prerequisites
- Python 3.12+
- [Neon](https://neon.tech) Postgres database (free tier)
- [Google Gemini](https://aistudio.google.com) API key (free tier)

### Steps

**1. Clone**
```bash
git clone https://github.com/aammiit2002/fintel-pulse.git
cd fintel-pulse
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Environment variables** — create `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

**4. Create tables**
```bash
python -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv()
conn = psycopg2.connect(os.environ['DATABASE_URL'])
conn.autocommit = True
conn.cursor().execute(open('sql/schema.sql').read())
print('Tables created.')
"
```

**5. Run**
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) — search any ticker e.g. `RELIANCE.NS`, `INFY.NS`.

---

## Deploying to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
3. **New app** → `aammiit2002/fintel-pulse` → `main` → `app.py`
4. **Advanced settings** → add secrets:
   ```toml
   GEMINI_API_KEY = "your_key"
   DATABASE_URL = "your_neon_url"
   ```
5. Click **Deploy**

---

## Project Structure

```
fintel-pulse/
├── app.py                  # Streamlit frontend
├── core/
│   ├── agent.py            # Gemini 3.1 Flash Lite wrapper
│   ├── team.py             # 5 specialists + Portfolio Manager
│   ├── orchestrator.py     # Cache logic + prediction logging
│   ├── tools.py            # yfinance + Google News RSS fetchers
│   └── db.py               # Neon Postgres helpers
├── jobs/
│   ├── daily_discovery.py  # Fetches Nifty 50 CSV, builds movers + most-viewed
│   └── nightly_accuracy.py # Scores predictions, updates all-time accuracy
├── sql/
│   └── schema.sql          # Full database schema
├── docs/
│   └── architecture.svg    # System architecture diagram
├── .github/workflows/
│   ├── daily_discovery.yml # Cron: 4 PM IST weekdays
│   └── nightly_accuracy.yml# Cron: 10 PM IST weekdays
├── requirements.txt
└── .env                    # Not committed — add keys here
```

---

## Disclaimer

Educational only — not financial advice. Data sourced from yfinance (unofficial Yahoo Finance feed) and Google News RSS. Next-day stock direction is close to a coin flip. Do not use this tool for real investment decisions.

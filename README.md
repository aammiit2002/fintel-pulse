# FintelPulse

> AI-powered equity research desk — multi-agent analysis, honest self-scoring, free-forever stack.

**FintelPulse** lets you search any stock ticker and instantly receive a structured research verdict synthesized from five parallel AI analysts covering news sentiment, fundamentals, technical momentum, institutional ownership, and downside risk. Every prediction is logged and scored nightly against real market outcomes — so the system holds itself accountable.

---

## Live Demo

> Deployed on Streamlit Community Cloud — link here once live.

---

## Key Features

| Feature | Description |
|---|---|
| Multi-agent analysis | 5 specialist AI agents run in parallel per query |
| Portfolio Manager | Synthesizes all agents into one verdict with a required downside |
| Smart caching | Results cached for 4 hours — repeat queries are instant |
| Self-scoring | Nightly job resolves predictions against actual price moves |
| 30-day accuracy tracker | Rolling scorecard shown on the homepage |
| Discovery panel | Daily movers and most-viewed tickers surfaced automatically |
| Fully free stack | Gemini free tier · Neon free tier · Streamlit Cloud · GitHub Actions |

---

## Architecture

![FintelPulse Architecture](docs/architecture.svg)

### How it works

```
User query
    │
    ▼
Orchestrator ──► Cache hit? ──► Return instantly
    │
    │ Cache miss
    ▼
┌─────────────────────────────────────────┐
│  5 Specialist Agents (parallel)         │
│  News · Fundamentals · Technical        │
│  Ownership · Risk                       │
└─────────────────────────────────────────┘
    │
    ▼
Portfolio Manager (Gemini) ──► Structured verdict
    │
    ▼
Neon Postgres ──► verdict_cache + predictions
    │
    ▼
Nightly job: resolve outcomes ──► accuracy scorecard
Daily job:   build movers + most-viewed lists
```

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.12 |
| AI | Google Gemini 3.1 Flash Lite (free tier) |
| Market data | yfinance |
| News | Google News RSS (no API key needed) |
| Database | Neon Postgres (free tier) |
| Scheduler | GitHub Actions (cron) |
| Frontend & hosting | Streamlit Community Cloud (free) |

---

## Database Schema

| Table | Purpose |
|---|---|
| `verdict_cache` | Stores latest verdict per ticker (4-hour TTL) |
| `predictions` | Logs every bullish / neutral / bearish call |
| `accuracy` | Rolling 30-day hit-rate scorecard |
| `discovery_list` | Daily movers and most-viewed lists |
| `ticker_views` | Tracks how often each ticker is queried |

---

## Running Locally

### Prerequisites
- Python 3.12+
- A [Neon](https://neon.tech) Postgres database (free tier)
- A [Google Gemini](https://aistudio.google.com) API key (free tier)

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/aammiit2002/fintel-pulse.git
cd fintel-pulse
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

**4. Create database tables**
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

**5. Run the app**
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) and search any ticker — e.g. `AAPL`, `RELIANCE.NS`, `TSLA`.

---

## Scheduled Jobs

Both jobs run automatically via GitHub Actions on weekdays. You can also trigger them manually from the **Actions** tab on GitHub.

| Job | Schedule (IST) | File |
|---|---|---|
| Daily Discovery | 9:00 AM weekdays | `jobs/daily_discovery.py` |
| Nightly Accuracy | 6:00 PM weekdays | `jobs/nightly_accuracy.py` |

Add `GEMINI_API_KEY` and `DATABASE_URL` as **repository secrets** under `Settings → Secrets and variables → Actions`.

---

## Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select `aammiit2002/fintel-pulse` → `main` → `app.py`
4. Under **Advanced settings**, add your secrets:
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
│   ├── agent.py            # Gemini agent wrapper
│   ├── team.py             # 5 specialist agents + Portfolio Manager
│   ├── orchestrator.py     # Cache logic and prediction logging
│   ├── tools.py            # yfinance + Google News data fetchers
│   └── db.py               # Neon Postgres helpers
├── jobs/
│   ├── daily_discovery.py  # Builds movers + most-viewed lists
│   └── nightly_accuracy.py # Resolves predictions and updates scorecard
├── sql/
│   └── schema.sql          # Full database schema
├── docs/
│   └── architecture.svg    # System architecture diagram
├── .github/workflows/      # GitHub Actions cron jobs
├── requirements.txt
└── .env                    # Not committed — add your keys here
```

---

## Disclaimer

Educational only — not financial advice. Data sourced from yfinance (unofficial Yahoo Finance feed) and Google News RSS. Next-day stock direction is close to a coin flip. Do not use this tool to make real investment decisions.

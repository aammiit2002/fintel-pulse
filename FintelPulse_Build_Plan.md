# FintelPulse — Full Build Plan

An AI equity-research web app with a light data-engineering layer. Free-forever stack. Built one working layer at a time so you always have something you can demo.

**Honest framing (keep this everywhere):** this is an *educational research-synthesis tool*, not a profit oracle. Next-day stock direction is close to a coin flip. The strong part of the project is the *honest self-evaluation loop* — a scheduled pipeline that scores every prediction against reality and reports a real hit-rate.

---

## The whole thing in one paragraph

A user searches a stock. The *orchestrator* checks a *cache* for a recent answer and serves it instantly if found. On a miss, five AI *specialists* (news, fundamentals, technical, ownership, risk) run in parallel, a *Portfolio Manager* merges them into a structured verdict, and that verdict is cached and logged as a prediction. Every night at 10 PM IST a scheduled job fetches closing prices, scores each prediction, and updates an all-time accuracy scorecard. Every day at 4 PM IST a second job fetches the live Nifty 50 constituents from NSE's official CSV and builds the homepage movers and most-viewed panels.

---

## Stack (all free)

| Piece | Tool | Notes |
|---|---|---|
| Language | Python 3.12 | |
| AI model | Gemini 3.1 Flash Lite | Higher rate limits than 2.5 Flash |
| Market data | yfinance | Prices, fundamentals, ownership |
| News | Google News RSS | No key needed |
| Index universe | NSE official CSV | Live Nifty 50 constituents, no auth |
| Database | Neon Postgres (free tier) | Serverless, scales to zero |
| Scheduler | GitHub Actions | Free on public repos |
| Frontend + host | Streamlit Community Cloud | Free |

---

## Build-order cheat sheet

| Phase | What you add | What you can demo |
|---|---|---|
| 0 | Accounts, keys, repo, folders | Keys load cleanly |
| 1 | One agent + minimal page | Type ticker → AI read on live data |
| 2 | Postgres: cache, predictions, views | Repeat queries instant; rows appear in DB |
| 3 | Full 5-agent team + Portfolio Manager | Structured multi-agent verdict |
| 4 | Nightly accuracy pipeline | Predictions scored; scorecard appears |
| 5 | Discovery panel + daily job | Homepage with movers + most-viewed |
| 6 | Deploy + polish | Public URL + interview story |

---

# Phase 0 — Setup

**Goal:** all accounts created, keys stored safely, repo and folder structure ready.

### Accounts and keys

| Service | Where | What you get |
|---|---|---|
| Gemini | aistudio.google.com | API key — free, ~1500 req/day |
| Neon | neon.tech | Postgres connection string — free 0.5 GB |
| GitHub | github.com | Repo — public = unlimited Actions minutes |
| Streamlit | share.streamlit.io | Sign in via GitHub — deploy later |

**Golden rule:** keys never go in code. Three homes — `.env` locally, Streamlit Secrets on Cloud, GitHub Actions Secrets for jobs.

### Folder structure

```
fintel-pulse/
├── app.py
├── core/
│   ├── __init__.py
│   ├── agent.py
│   ├── team.py
│   ├── tools.py
│   ├── orchestrator.py
│   └── db.py
├── jobs/
│   ├── nightly_accuracy.py
│   └── daily_discovery.py
├── sql/schema.sql
├── .github/workflows/
│   ├── nightly_accuracy.yml
│   └── daily_discovery.yml
├── docs/architecture.svg
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

### requirements.txt
```
streamlit
google-genai
yfinance
psycopg2-binary
feedparser
python-dotenv
pandas
```

---

# Phase 1 — Vertical slice (one agent, end to end)

**Goal:** one specialist that pulls live data, calls Gemini, returns a verdict on a minimal Streamlit page.

**Why first:** proves the riskiest part (AI + live data + web) on day one. Everything later is adding layers around this.

### core/agent.py
```python
import os
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

class Agent:
    def __init__(self, name, system_prompt, model="gemini-3.1-flash-lite"):
        self.name = name
        self.system_prompt = system_prompt
        self.model = model

    def run(self, user_content: str) -> str:
        resp = client.models.generate_content(
            model=self.model,
            contents=f"{self.system_prompt}\n\n{user_content}",
        )
        return resp.text
```

> **Model note:** use `gemini-3.1-flash-lite` — higher rate limits than 2.5 Flash, better for multi-agent workloads.

---

# Phase 2 — Data store (cache + predictions + views)

**Goal:** Postgres on Neon, cache for instant repeats, prediction log for later scoring.

### sql/schema.sql

```sql
CREATE TABLE IF NOT EXISTS verdict_cache (
    ticker   TEXT PRIMARY KEY,
    verdict  JSONB NOT NULL,
    made_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS predictions (
    id            SERIAL PRIMARY KEY,
    ticker        TEXT NOT NULL,
    predicted_on  DATE NOT NULL,
    prediction    TEXT NOT NULL,    -- bullish / neutral / bearish
    for_date      DATE NOT NULL,    -- day being predicted
    actual_move   NUMERIC,          -- filled by nightly job
    correct       BOOLEAN           -- filled by nightly job
);

CREATE TABLE IF NOT EXISTS accuracy (
    scope      TEXT NOT NULL,       -- 'overall'
    period     TEXT NOT NULL,       -- 'all_time'
    hit_rate   NUMERIC NOT NULL,
    total      INT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (scope, period)
);

CREATE TABLE IF NOT EXISTS discovery_list (
    kind     TEXT NOT NULL,         -- 'movers' or 'most_viewed'
    payload  JSONB NOT NULL,
    built_on DATE NOT NULL,
    PRIMARY KEY (kind, built_on)
);

CREATE TABLE IF NOT EXISTS ticker_views (
    ticker     TEXT PRIMARY KEY,
    views      INT NOT NULL DEFAULT 0,
    last_asked TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

# Phase 3 — Full agent team (5 specialists + Portfolio Manager)

**Goal:** five independent specialists in parallel, one manager that synthesises.

### Agent prompt design (learned from production)

Each specialist is prompted to **cite actual figures**, not adjectives:
- Fundamentals: "cite P/E, revenue growth %, D/E ratio"
- Technical: "cite specific price levels or % moves"
- Risk: "cite beta, short ratio, distance from 52-week high/low"

Portfolio Manager rules:
1. Include at least one specific number in drivers
2. **Final driver must name a concrete risk** — even if stance is bullish
3. Keep each driver under 15 words
4. Return only valid JSON, no markdown fences

### Parallel execution

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

with ThreadPoolExecutor(max_workers=5) as pool:
    futures = {pool.submit(_run_one, name, ticker): name for name in SPECIALISTS}
    for future in as_completed(futures):
        name, result = future.result()
        reports[name] = result
```

Five specialists run simultaneously; manager waits for all five. Same result as sequential, ~5× faster.

---

# Phase 4 — Nightly accuracy pipeline

**Goal:** scheduled job that scores every prediction against actual closing prices and updates the all-time accuracy scorecard.

### Scoring logic

| Prediction | Correct if |
|---|---|
| Bullish | Actual move **> +1%** (open → close) |
| Bearish | Actual move **< -1%** |
| Neutral | Actual move **within ±1%** |

> The ±1% threshold filters out noise — a 0.3% move on a "bullish" call shouldn't count as wrong.

### Key implementation notes

- Use `for_date <= current_date` (not `<`) so same-day predictions are scored the same night
- yfinance date range: `history(start=for_date, end=for_date + timedelta(days=1))` — end is exclusive, must be +1 day
- Convert yfinance values with `float()` before passing to psycopg2 — numpy scalars cause `schema "np" does not exist` errors
- Bare Indian tickers (e.g. `INDIGO`) need `.NS` suffix for yfinance — try bare first, fallback to `ticker + ".NS"`

### Schedule

```yaml
# .github/workflows/nightly_accuracy.yml
- cron: "30 16 * * 1-5"   # 10:00 PM IST — after both NSE (3:30 PM) and NYSE (9:30 PM) close
```

---

# Phase 5 — Discovery panel + daily job

**Goal:** homepage panels for biggest movers and most-viewed tickers. Zero AI in this phase.

### Dynamic Nifty 50 universe

Do **not** hardcode the 50 tickers — NSE publishes an official CSV that updates when composition changes:

```python
NIFTY50_CSV = "https://archives.nseindia.com/content/indices/ind_nifty50list.csv"

def get_universe() -> list[str]:
    df = pd.read_csv(NIFTY50_CSV)
    return [s + ".NS" for s in df["Symbol"].tolist()]
```

This fetches live constituents on every job run. No auth, no scraping, no fragile session cookies.

### Movers display

- Separate **Top Gainers** (green ▲) and **Top Losers** (red ▼)
- On all-red days: show "best performers today" in teal with `~` symbol — never show ▲ with a negative number
- Strip `.NS` / `.BO` suffix from display — show `TCS` not `TCS.NS`

### Schedule

```yaml
# .github/workflows/daily_discovery.yml
- cron: "30 10 * * 1-5"   # 4:00 PM IST — 30 min after NSE close (3:30 PM)
```

---

# Phase 6 — Deploy + polish

1. **Streamlit Cloud:** push to GitHub → [share.streamlit.io](https://share.streamlit.io) → New app → add secrets
2. **GitHub Actions secrets:** `DATABASE_URL` and `GEMINI_API_KEY` under Settings → Secrets → Actions
3. **Trigger jobs manually** first (Run workflow button) to verify before trusting the schedule
4. **Update README** with live URL once deployed

### The story for interviews

> "I built an AI research desk with a light data-engineering layer. The interesting part isn't the prediction — it's the honest evaluation loop: a nightly pipeline that scores every prediction against real closing prices and reports an all-time hit-rate. I used five parallel agents to cover different analysis dimensions, a Portfolio Manager to synthesise them, and a Postgres cache so repeat queries are instant. The whole stack is free — Gemini free tier, Neon serverless Postgres, Streamlit Cloud, and GitHub Actions for scheduling."

---

## Things to verify as you go

| Check | Why |
|---|---|
| Gemini model name in AI Studio | Google rotates model IDs |
| Neon free tier limits | 0.5 GB storage, 100 compute-hours/month |
| yfinance is unofficial | Wrap all data calls in try/except |
| Keep repo public | Public repos get free GitHub Actions minutes |
| `.env` in `.gitignore` | Never commit API keys |

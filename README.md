# FintelPulse

An AI equity-research web app with a light data-engineering layer. **Free-forever stack.**

> **Honest framing:** this is an *educational research-synthesis tool*, not a profit oracle.
> Next-day stock direction is close to a coin flip. The strong part of the project is that it
> *keeps an honest scorecard of itself* — that self-evaluation loop is the headline feature.

## Architecture

![Architecture](complete_architecture_grouped_tables.svg)

## How it works

A user asks about a stock. The *orchestrator* resolves the ticker, checks a *cache* for a
recent answer, and serves it instantly if found. On a miss, five AI *specialists* (news,
fundamentals, technical, ownership, risk) run **in parallel**, a *Portfolio Manager* merges
them into one structured verdict, and that verdict is saved to the cache and logged as a
*prediction*. Every night a scheduled job checks what those stocks actually did and updates
an *accuracy* scorecard. Every morning a second job builds the homepage's "biggest movers"
and "most viewed" lists.

## Stack (all free)

| Piece | Tool |
|---|---|
| Language | Python 3.12 |
| AI brain | Google Gemini (free tier) |
| Market data | yfinance |
| News | Google News RSS |
| Database | Postgres on Neon (free tier) |
| Scheduler | GitHub Actions |
| Frontend + host | Streamlit Community Cloud |

## Setup

1. Copy `.env.example` → `.env` and fill in your keys.
2. Run the SQL schema against your Neon database: `sql/schema.sql`.
3. Install dependencies: `pip install -r requirements.txt`
4. Run locally: `streamlit run app.py`

Add `GEMINI_API_KEY` and `DATABASE_URL` as GitHub repository secrets for the scheduled jobs.

## Disclaimer

Educational only — not financial advice. Data sourced from yfinance (unofficial feed) and
Google News RSS. Not suitable for real investment decisions.

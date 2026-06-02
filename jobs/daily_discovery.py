"""
Daily job — run each morning before the market opens.
Builds two discovery lists stored in the discovery_list table:
  'movers'      — biggest % gainers/losers from the reference universe
  'most_viewed' — tickers with the most user queries
"""
import json
import yfinance as yf
from core.db import conn

# Reference universe — extend this list for broader coverage
UNIVERSE = [
    "RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ITC.NS",
    "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
]


def build_movers() -> list[dict]:
    try:
        data = yf.download(UNIVERSE, period="2d", progress=False)["Close"]
        pct = ((data.iloc[-1] / data.iloc[-2]) - 1) * 100
        ranked = sorted(
            [(str(t), round(float(p), 2)) for t, p in pct.items() if not __import__("math").isnan(p)],
            key=lambda kv: abs(kv[1]),
            reverse=True,
        )
        return [{"ticker": t, "pct": p} for t, p in ranked[:10]]
    except Exception as e:
        print(f"build_movers error: {e}")
        return []


def build_most_viewed() -> list[dict]:
    with conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT ticker, views FROM ticker_views ORDER BY views DESC LIMIT 10"
        )
        return [{"ticker": t, "views": v} for t, v in cur.fetchall()]


def save(kind: str, payload: list):
    with conn() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO discovery_list (kind, payload, built_on)
            VALUES (%s, %s, current_date)
            ON CONFLICT (kind, built_on) DO UPDATE SET payload = EXCLUDED.payload
            """,
            (kind, json.dumps(payload)),
        )
    print(f"Saved {kind}: {len(payload)} items.")


if __name__ == "__main__":
    save("movers", build_movers())
    save("most_viewed", build_most_viewed())

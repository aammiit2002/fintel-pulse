"""
Nightly job — run after market close.
1. Resolves actual outcomes for any prediction whose for_date has passed.
2. Recomputes the rolling 30-day accuracy scorecard.
"""
import yfinance as yf
from core.db import conn


def pct_change_on(ticker: str, for_date) -> float | None:
    """Return the percentage price change on for_date, or None if unavailable."""
    try:
        hist = yf.Ticker(ticker).history(start=str(for_date), end=str(for_date))
        if hist.empty or len(hist) < 1:
            return None
        open_p = hist["Open"].iloc[0]
        close_p = hist["Close"].iloc[0]
        if open_p == 0:
            return None
        return round(((close_p - open_p) / open_p) * 100, 4)
    except Exception:
        return None


def resolve_outcomes():
    with conn() as c, c.cursor() as cur:
        cur.execute(
            """
            SELECT id, ticker, prediction, for_date
            FROM predictions
            WHERE correct IS NULL AND for_date < current_date
            """
        )
        rows = cur.fetchall()

    for pid, ticker, prediction, for_date in rows:
        move = pct_change_on(ticker, for_date)
        if move is None:
            continue
        correct = (move > 0 and prediction == "bullish") or (
            move < 0 and prediction == "bearish"
        )
        with conn() as c, c.cursor() as cur:
            cur.execute(
                "UPDATE predictions SET actual_move = %s, correct = %s WHERE id = %s",
                (move, correct, pid),
            )
    print(f"Resolved {len(rows)} pending predictions.")


def recompute_accuracy():
    with conn() as c, c.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*) FROM predictions
            WHERE correct IS NOT NULL
              AND for_date > current_date - INTERVAL '30 days'
            """
        )
        total = cur.fetchone()[0]
        if total == 0:
            print("No scored predictions yet, skipping accuracy update.")
            return
        cur.execute(
            """
            INSERT INTO accuracy (scope, period, hit_rate, total, updated_at)
            SELECT
                'overall',
                'last_30_days',
                ROUND(AVG(CASE WHEN correct THEN 1.0 ELSE 0.0 END) * 100, 1),
                COUNT(*),
                now()
            FROM predictions
            WHERE correct IS NOT NULL
              AND for_date > current_date - INTERVAL '30 days'
            ON CONFLICT (scope, period) DO UPDATE
            SET hit_rate   = EXCLUDED.hit_rate,
                total      = EXCLUDED.total,
                updated_at = now()
            """
        )
    print("Accuracy scorecard updated.")


if __name__ == "__main__":
    resolve_outcomes()
    recompute_accuracy()

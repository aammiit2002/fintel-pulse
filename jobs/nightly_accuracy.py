"""
Nightly job — run after market close.
1. Resolves actual outcomes for any prediction whose for_date has passed.
2. Recomputes the rolling 30-day accuracy scorecard.
"""
from datetime import timedelta
import yfinance as yf
from core.db import conn


def _fetch_hist(ticker: str, for_date):
    return yf.Ticker(ticker).history(
        start=str(for_date), end=str(for_date + timedelta(days=1))
    )


def pct_change_on(ticker: str, for_date) -> float | None:
    """Return the percentage price change on for_date, or None if unavailable.
    Tries bare ticker first, then appends .NS for Indian stocks."""
    for sym in [ticker, ticker + ".NS"] if "." not in ticker else [ticker]:
        try:
            hist = _fetch_hist(sym, for_date)
            if hist.empty:
                continue
            open_p  = float(hist["Open"].iloc[0])
            close_p = float(hist["Close"].iloc[0])
            if open_p == 0:
                continue
            return round((close_p - open_p) / open_p * 100, 4)
        except Exception:
            continue
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
        correct = (
            (move > 1.0  and prediction == "bullish") or
            (move < -1.0 and prediction == "bearish") or
            (abs(move) <= 1.0 and prediction == "neutral")
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
            "SELECT COUNT(*) FROM predictions WHERE correct IS NOT NULL"
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
                'all_time',
                ROUND(AVG(CASE WHEN correct THEN 1.0 ELSE 0.0 END) * 100, 1),
                COUNT(*),
                now()
            FROM predictions
            WHERE correct IS NOT NULL
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

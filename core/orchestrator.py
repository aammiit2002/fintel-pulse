from datetime import date, timedelta
from core import db


def tomorrow() -> date:
    return date.today() + timedelta(days=1)


def answer(ticker: str, run_agents) -> dict:
    """
    1. Bump view count on every ask.
    2. Return cached verdict if fresh.
    3. Otherwise run agents, save, and return.
    """
    ticker = ticker.upper().strip()
    db.bump_view(ticker)

    cached = db.get_cached(ticker)
    if cached:
        cached["_source"] = "cache"
        return cached

    verdict = run_agents(ticker)
    db.save_verdict_and_log(ticker, verdict, for_date=tomorrow())
    verdict["_source"] = "live"
    return verdict

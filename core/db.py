import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor


def conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def get_cached(ticker: str, ttl_hours: int = 4):
    with conn() as c, c.cursor() as cur:
        cur.execute(
            """
            SELECT verdict FROM verdict_cache
            WHERE ticker = %s AND made_at > now() - interval '1 hour' * %s
            """,
            (ticker, ttl_hours),
        )
        row = cur.fetchone()
        return row[0] if row else None


def save_verdict_and_log(ticker: str, verdict: dict, for_date):
    with conn() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO verdict_cache (ticker, verdict, made_at)
            VALUES (%s, %s, now())
            ON CONFLICT (ticker) DO UPDATE
            SET verdict = EXCLUDED.verdict, made_at = now()
            """,
            (ticker, json.dumps(verdict)),
        )
        cur.execute(
            """
            INSERT INTO predictions (ticker, predicted_on, prediction, for_date)
            VALUES (%s, current_date, %s, %s)
            """,
            (ticker, verdict.get("stance", "neutral"), for_date),
        )


def bump_view(ticker: str):
    with conn() as c, c.cursor() as cur:
        cur.execute(
            """
            INSERT INTO ticker_views (ticker, views, last_asked)
            VALUES (%s, 1, now())
            ON CONFLICT (ticker) DO UPDATE
            SET views = ticker_views.views + 1, last_asked = now()
            """,
            (ticker,),
        )


def get_accuracy():
    with conn() as c, c.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT hit_rate, total FROM accuracy WHERE scope = 'overall' AND period = 'all_time'"
        )
        return cur.fetchone()


def get_discovery(kind: str):
    with conn() as c, c.cursor() as cur:
        cur.execute(
            "SELECT payload FROM discovery_list WHERE kind = %s ORDER BY built_on DESC LIMIT 1",
            (kind,),
        )
        row = cur.fetchone()
        return row[0] if row else []

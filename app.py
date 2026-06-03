import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from core.orchestrator import answer
from core.team import run_team
from core import db

st.set_page_config(page_title="FintelPulse", page_icon="📈", layout="centered")

st.title("📈 FintelPulse")
st.caption("Educational AI research desk — not financial advice.")

# ── Homepage panels ──────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    try:
        acc = db.get_accuracy()
        if acc:
            st.metric("30-day accuracy", f"{acc['hit_rate']}%", f"{acc['total']} predictions")
        else:
            st.metric("30-day accuracy", "—", "No data yet")
    except Exception:
        st.metric("30-day accuracy", "—")

with col2:
    try:
        movers = db.get_discovery("movers")
        if movers:
            gainers = [m for m in movers if m["pct"] > 0]
            losers  = [m for m in movers if m["pct"] < 0]

            st.subheader("Top Gainers")
            if gainers:
                for item in gainers[:5]:
                    st.markdown(
                        f"<span style='color:#00c853'>▲ **{item['ticker']}** &nbsp; {item['pct']:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No gainers today.")

            st.subheader("Top Losers")
            if losers:
                for item in losers[:5]:
                    st.markdown(
                        f"<span style='color:#ff1744'>▼ **{item['ticker']}** &nbsp; {item['pct']:+.2f}%</span>",
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No losers today.")
        else:
            st.subheader("Movers")
            st.caption("Available after the daily job runs.")
    except Exception:
        st.subheader("Movers")
        st.caption("Connect database to see movers.")

with col3:
    try:
        viewed = db.get_discovery("most_viewed")
        if viewed:
            st.subheader("Most viewed")
            for item in viewed[:5]:
                st.write(f"**{item['ticker']}** — {item['views']} asks")
        else:
            st.subheader("Most viewed")
            st.caption("Available after the daily job runs.")
    except Exception:
        st.subheader("Most viewed")
        st.caption("Connect database to see views.")

st.divider()

# ── Search ────────────────────────────────────────────────────────────────────
ticker_input = st.text_input(
    "Stock ticker",
    placeholder="e.g. AAPL, RELIANCE.NS, TSLA",
    help="Enter any ticker supported by Yahoo Finance.",
)

if st.button("Analyze", type="primary") and ticker_input.strip():
    ticker = ticker_input.strip().upper()
    with st.spinner(f"Researching {ticker}…"):
        try:
            verdict = answer(ticker, run_team)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    source_tag = "⚡ cached" if verdict.get("_source") == "cache" else "🔍 live analysis"
    st.success(f"Done! ({source_tag})")

    stance = verdict.get("stance", "neutral").title()
    confidence = verdict.get("confidence", "—").title()
    drivers = verdict.get("drivers", [])

    st.subheader(f"{ticker} — {stance}")
    st.write(f"**Confidence:** {confidence}")

    if drivers:
        st.subheader("Key drivers")
        for d in drivers:
            st.markdown(f"- {d}")

    st.info("Educational only — not financial advice. Next-day stock direction is close to a coin flip.")

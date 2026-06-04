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

# ── Accuracy bar ─────────────────────────────────────────────────────────────
try:
    acc = db.get_accuracy()
    if acc:
        st.metric("Overall prediction accuracy", f"{acc['hit_rate']}%", f"based on {acc['total']} predictions")
    else:
        st.metric("30-day prediction accuracy", "—", "Populates after first full trading day")
except Exception:
    st.metric("30-day prediction accuracy", "—")

st.divider()


def fmt_ticker(ticker: str) -> str:
    return ticker.replace(".NS", "").replace(".BO", "")


def mover_row(color: str, symbol: str, pct: float, arrow: str) -> str:
    return (
        f"<div style='display:flex; justify-content:space-between; "
        f"padding:4px 0; border-bottom:1px solid #222;'>"
        f"<span style='color:{color}; font-weight:600'>{arrow} {fmt_ticker(symbol)}</span>"
        f"<span style='color:{color}'>{pct:+.2f}%</span></div>"
    )


# ── Movers + Most viewed ──────────────────────────────────────────────────────
col_g, col_l, col_v = st.columns(3)

with col_g:
    st.subheader("Top Gainers")
    try:
        movers = db.get_discovery("movers")
        if movers:
            sorted_desc = sorted(movers, key=lambda x: x["pct"], reverse=True)
            gainers = [m for m in sorted_desc if m["pct"] > 0][:5]
            if gainers:
                for item in gainers:
                    st.markdown(mover_row("#00c853", item["ticker"], item["pct"], "▲"), unsafe_allow_html=True)
            else:
                st.caption("All stocks down — best today:")
                for item in sorted_desc[:5]:
                    st.markdown(mover_row("#80cbc4", item["ticker"], item["pct"], "~"), unsafe_allow_html=True)
        else:
            st.caption("Available after daily job runs.")
    except Exception:
        st.caption("—")

with col_l:
    st.subheader("Top Losers")
    try:
        movers = db.get_discovery("movers")
        if movers:
            sorted_asc = sorted(movers, key=lambda x: x["pct"])
            losers = [m for m in sorted_asc if m["pct"] < 0][:5]
            if losers:
                for item in losers:
                    st.markdown(mover_row("#ff1744", item["ticker"], item["pct"], "▼"), unsafe_allow_html=True)
            else:
                st.caption("All stocks up — worst today:")
                for item in sorted_asc[:5]:
                    st.markdown(mover_row("#ef9a9a", item["ticker"], item["pct"], "~"), unsafe_allow_html=True)
        else:
            st.caption("Available after daily job runs.")
    except Exception:
        st.caption("—")

with col_v:
    st.subheader("Most Viewed")
    try:
        viewed = db.get_discovery("most_viewed")
        if viewed:
            for item in viewed[:5]:
                st.markdown(
                    f"<div style='display:flex; justify-content:space-between; "
                    f"padding:4px 0; border-bottom:1px solid #222;'>"
                    f"<span style='font-weight:600'>{fmt_ticker(item['ticker'])}</span>"
                    f"<span style='color:#888'>{item['views']} asks</span></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Available after daily job runs.")
    except Exception:
        st.caption("—")

st.divider()

# ── Search ────────────────────────────────────────────────────────────────────
exchange = st.radio(
    "Exchange",
    ["NSE (India)", "US (NYSE / NASDAQ)"],
    horizontal=True,
)

is_nse = exchange == "NSE (India)"
placeholder = "e.g. SBIN, RELIANCE, TCS, INFY" if is_nse else "e.g. AAPL, TSLA, MSFT, NVDA"

ticker_input = st.text_input(
    "Stock ticker",
    placeholder=placeholder,
    help="Type the ticker symbol and we'll handle the rest.",
)

if st.button("Analyze", type="primary") and ticker_input.strip():
    raw = ticker_input.strip().upper()
    ticker = (raw + ".NS") if is_nse and not raw.endswith(".NS") else raw
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

    st.subheader(f"{fmt_ticker(ticker)} — {stance}")
    st.write(f"**Confidence:** {confidence}")

    if drivers:
        st.subheader("Key drivers")
        for d in drivers:
            st.markdown(f"- {d}")

    agent_reports = verdict.get("agent_reports", {})
    if agent_reports:
        st.subheader("Agent reasoning")
        icons = {"news": "📰", "fundamentals": "📊", "technical": "📈", "ownership": "🏦", "risk": "⚠️"}
        for name, report in agent_reports.items():
            with st.expander(f"{icons.get(name, '🤖')} {name.title()} Analyst"):
                st.markdown(report)

    st.info("Educational only — not financial advice. Next-day stock direction is close to a coin flip.")

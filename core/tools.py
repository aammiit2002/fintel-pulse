import feedparser
import urllib.parse
import yfinance as yf


def get_fundamentals(ticker: str) -> dict:
    """Return raw fundamental numbers only. No analysis here."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "name": info.get("shortName"),
            "pe_ratio": info.get("trailingPE"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_price_history(ticker: str) -> dict:
    """Return recent price data for technical analysis."""
    try:
        hist = yf.Ticker(ticker).history(period="3mo")
        if hist.empty:
            return {"error": "No price data"}
        closes = hist["Close"].round(2).tolist()
        return {
            "closes_last_30": closes[-30:],
            "current": closes[-1],
            "high_52w": round(hist["Close"].max(), 2),
            "low_52w": round(hist["Close"].min(), 2),
        }
    except Exception as e:
        return {"error": str(e)}


def get_ownership(ticker: str) -> dict:
    """Return institutional and insider ownership data."""
    try:
        t = yf.Ticker(ticker)
        inst = t.institutional_holders
        if inst is not None and not inst.empty:
            top = inst.head(5).to_dict(orient="records")
        else:
            top = []
        info = t.info
        return {
            "institutional_top5": top,
            "held_percent_institutions": info.get("heldPercentInstitutions"),
            "held_percent_insiders": info.get("heldPercentInsiders"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_everything(ticker: str) -> dict:
    """Return a broad data snapshot for the risk agent."""
    try:
        info = yf.Ticker(ticker).info
        return {
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "short_ratio": info.get("shortRatio"),
            "sector": info.get("sector"),
            "country": info.get("country"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_headlines(ticker: str, limit: int = 10) -> list[str]:
    """Fetch headlines from yfinance AND Google News RSS in parallel, combine and deduplicate."""
    from concurrent.futures import ThreadPoolExecutor

    try:
        info = yf.Ticker(ticker).info
        company_name = info.get("shortName") or info.get("longName") or ticker
    except Exception:
        company_name = ticker

    def fetch_yfinance_news():
        try:
            articles = yf.Ticker(ticker).news or []
            return [a.get("content", {}).get("title", "") or a.get("title", "") for a in articles if a]
        except Exception:
            return []

    def fetch_google_rss():
        try:
            url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(company_name + " stock")
            feed = feedparser.parse(url)
            return [e.title for e in feed.entries]
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(fetch_yfinance_news)
        f2 = pool.submit(fetch_google_rss)
        yf_titles  = f1.result()
        rss_titles = f2.result()

    # Combine, deduplicate, return top N
    seen = set()
    combined = []
    for title in yf_titles + rss_titles:
        if title and title.lower() not in seen:
            seen.add(title.lower())
            combined.append(title)
        if len(combined) >= limit:
            break

    return combined if combined else [f"No headlines found for {company_name}"]

import feedparser
import urllib.parse
import yfinance as yf


def _is_indian(ticker: str) -> bool:
    return ticker.upper().endswith(".NS") or ticker.upper().endswith(".BO")


def get_fundamentals(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        data = {
            "name": info.get("shortName") or info.get("longName"),
            "sector": info.get("sector"),
            "pe_ratio": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "profit_margin": info.get("profitMargins"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "debt_to_equity": info.get("debtToEquity"),
            "return_on_equity": info.get("returnOnEquity"),
            "current_ratio": info.get("currentRatio"),
        }
        if _is_indian(ticker):
            data["india_pe_context"] = (
                "Indian market P/E benchmarks (trailing): "
                "Nifty 50 long-term average ~20-22x. "
                "Sector ranges — IT: 25-35x, Private Banks: 15-25x, "
                "PSU/Infra: 8-15x, FMCG: 40-60x, Pharma: 25-40x, Auto: 15-25x. "
                "Evaluate P/E against sector peers, not a single universal threshold."
            )
        return data
    except Exception as e:
        return {"error": str(e)}


def get_price_history(ticker: str) -> dict:
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
            "avg_volume_30d": round(hist["Volume"].tail(30).mean()),
        }
    except Exception as e:
        return {"error": str(e)}


def get_ownership(ticker: str) -> dict:
    try:
        t = yf.Ticker(ticker)
        inst = t.institutional_holders
        top = inst.head(5).to_dict(orient="records") if inst is not None and not inst.empty else []
        info = t.info
        data = {
            "held_percent_institutions": info.get("heldPercentInstitutions"),
            "held_percent_insiders": info.get("heldPercentInsiders"),
            "institutional_top5": top,
        }
        if _is_indian(ticker):
            data["india_ownership_context"] = (
                "IMPORTANT for Indian stocks: "
                "'held_percent_insiders' here represents PROMOTER + PROMOTER GROUP holding "
                "(not insider trading). This is normal Indian corporate structure. "
                "Promoter holding >50% means majority control — common and not a red flag. "
                "Promoter holding <40% may indicate dilution risk. "
                "Declining promoter holding across quarters is worth flagging. "
                "'held_percent_institutions' represents combined FII (Foreign) + DII (Domestic) "
                "institutional holding. The institutional_top5 list is often sparse for Indian stocks "
                "in this data source — treat absence of data as incomplete, not zero holding."
            )
        return data
    except Exception as e:
        return {"error": str(e)}


def get_everything(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        data = {
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "avg_volume": info.get("averageVolume"),
            "market_cap": info.get("marketCap"),
            "short_ratio": info.get("shortRatio"),
            "sector": info.get("sector"),
            "country": info.get("country"),
            "currency": info.get("currency"),
        }
        if _is_indian(ticker):
            data["india_risk_context"] = (
                "Indian market risk factors to consider: "
                "1) FII (foreign institutional) outflows are a primary driver of sharp NSE selloffs. "
                "2) RBI monetary policy and repo rate changes directly impact rate-sensitive sectors "
                "(banking, NBFCs, real estate). "
                "3) INR/USD depreciation raises import costs and pressures margins for import-heavy sectors. "
                "4) US Fed decisions and global risk-off sentiment cause correlated FII outflows. "
                "5) Domestic macro: GST collections, IIP data, CPI inflation influence market direction. "
                "Beta on NSE stocks is measured against Nifty 50 — beta >1 means higher volatility than index."
            )
        return data
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

    seen = set()
    combined = []
    for title in yf_titles + rss_titles:
        if title and title.lower() not in seen:
            seen.add(title.lower())
            combined.append(title)
        if len(combined) >= limit:
            break

    return combined if combined else [f"No headlines found for {company_name}"]

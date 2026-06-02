import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.agent import Agent
from core import tools

SPECIALISTS = {
    "news": (
        "You are a news sentiment analyst. Given a list of recent stock headlines, "
        "assess market sentiment. Give: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 key reasons. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_headlines(t),
    ),
    "fundamentals": (
        "You are a fundamentals analyst. Given raw financial numbers, "
        "give a short, balanced read: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 plain reasons. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_fundamentals(t),
    ),
    "technical": (
        "You are a technical analyst. Given recent price history, "
        "identify key trends and momentum: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 observations. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_price_history(t),
    ),
    "ownership": (
        "You are an ownership analyst. Given institutional and insider data, "
        "assess what smart money signals: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 reasons. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_ownership(t),
    ),
    "risk": (
        "You are a risk analyst. Given broad market and company risk indicators, "
        "assess the key downside risks: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 risk factors. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_everything(t),
    ),
}


def _run_one(name: str, ticker: str) -> tuple[str, str]:
    system_prompt, fetch = SPECIALISTS[name]
    agent = Agent(name=name, system_prompt=system_prompt)
    data = fetch(ticker)
    return name, agent.run(f"Ticker: {ticker}\nData: {data}")


def run_team(ticker: str) -> dict:
    """Run all 5 specialists in parallel, then synthesize with Portfolio Manager."""
    reports = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_run_one, name, ticker): name for name in SPECIALISTS}
        for future in as_completed(futures):
            name, result = future.result()
            reports[name] = result

    pm = Agent(
        name="PortfolioManager",
        system_prompt=(
            "You are a Portfolio Manager. Combine the five analyst reports into ONE verdict. "
            "Return ONLY valid JSON with no markdown fences: "
            '{"stance": "bullish|neutral|bearish", "confidence": "low|medium|high", '
            '"drivers": ["reason1", "reason2", "reason3"]}. No prose outside the JSON.'
        ),
    )
    raw = pm.run(json.dumps(reports))
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(cleaned)

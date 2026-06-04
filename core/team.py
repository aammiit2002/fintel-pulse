import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from core.agent import Agent
from core import tools

SPECIALISTS = {
    "news": (
        "You are a news sentiment analyst. Given a list of recent stock headlines, "
        "assess market sentiment. Give: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 key reasons. "
        "Quote or paraphrase specific headline themes rather than using vague adjectives. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_headlines(t),
    ),
    "fundamentals": (
        "You are a fundamentals analyst. Given raw financial numbers, "
        "give a short, balanced read: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 plain reasons. "
        "Cite the actual figures (e.g. 'P/E 28x', 'revenue growth 14%', 'D/E 0.4'). "
        "Name at least one concern even if the overall stance is bullish. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_fundamentals(t),
    ),
    "technical": (
        "You are a technical analyst. Given recent price history, "
        "identify key trends and momentum: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 observations. "
        "Use specific price levels or percentage moves (e.g. 'up 12% over 30 days', '8% off 52-week high'). "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_price_history(t),
    ),
    "ownership": (
        "You are an ownership analyst. Given institutional and insider data, "
        "assess what smart money signals: stance (bullish/neutral/bearish), "
        "confidence (low/medium/high), and 2-3 reasons. "
        "Cite the actual ownership percentages where available. "
        "End with: 'Educational only, not financial advice.'",
        lambda t: tools.get_ownership(t),
    ),
    "risk": (
        "STRICT RULES — read before anything else: "
        "(1) The data payload below contains everything you need. "
        "(2) NEVER say data is missing, unavailable, or ask users to verify elsewhere. "
        "(3) If a specific field is null, skip it and use the other fields — do not mention it. "
        "(4) NEVER invent or assume figures not present in the payload. "
        "You are a risk analyst. Using ONLY the provided data, assess key downside risks: "
        "stance (bullish/neutral/bearish), confidence (low/medium/high), and 2-3 specific risk factors. "
        "Cite actual values from the payload — beta, 52-week high/low gap, market cap, volume. "
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
            "Rules: (1) include at least one specific number or data point in the drivers; "
            "(2) the final driver must name a concrete risk or 'what could go wrong' — even if the overall stance is bullish; "
            "(3) keep each driver under 15 words. "
            "Return ONLY valid JSON with no markdown fences: "
            '{"stance": "bullish|neutral|bearish", "confidence": "low|medium|high", '
            '"drivers": ["reason1", "reason2", "reason3"]}. No prose outside the JSON.'
        ),
    )
    raw = pm.run(json.dumps(reports))
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    verdict = json.loads(cleaned)
    verdict["agent_reports"] = reports
    return verdict

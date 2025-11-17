"""Generate artificial news, signals, macro snapshots, and alerts."""
from __future__ import annotations

import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

COMPANIES = [
    ("AAPL", "Apple"),
    ("MSFT", "Microsoft"),
    ("AMZN", "Amazon"),
    ("NVDA", "NVIDIA"),
    ("TSLA", "Tesla"),
    ("JPM", "JPMorgan"),
    ("NFLX", "Netflix"),
    ("DIS", "Disney"),
    ("GOOGL", "Alphabet"),
    ("META", "Meta"),
]

CATEGORIES = ["Markets", "Stocks", "Crypto", "Banking", "Commodities", "Technology"]
IMPACTS = ["Earnings", "Macro", "Product", "Regulation", "M&A", "Supply Chain"]

REGION_MAP = {
    "S&P 500": "Americas",
    "NASDAQ": "Americas",
    "Dow Jones": "Americas",
    "Russell 2000": "Americas",
    "FTSE 100": "EMEA",
    "DAX": "EMEA",
    "CAC 40": "EMEA",
    "Nikkei 225": "APAC",
    "Hang Seng": "APAC",
    "Kospi": "APAC",
    "ASX 200": "APAC",
}


def fake_headlines(count: int = 100) -> List[Dict[str, str]]:
    articles: List[Dict[str, str]] = []
    for _ in range(count):
        ticker, company = random.choice(COMPANIES)
        action = random.choice(
            [
                "reports record earnings",
                "faces regulatory scrutiny",
                "launches AI division",
                "announces $5B buyback",
                "warns on guidance",
                "inks strategic partnership",
                "secures mega government contract",
                "faces activist investor pressure",
            ]
        )
        stance = random.choice(["buy", "hold", "sell"])
        timestamp = datetime.utcnow() - timedelta(seconds=random.randint(5, 1800))
        articles.append(
            {
                "ticker": ticker,
                "title": f"{company} {action}",
                "source": random.choice(["MarketWatch", "Reuters", "WSJ", "Bloomberg"]),
                "timestamp": timestamp.isoformat(),
                "stance": stance,
                "category": random.choice(CATEGORIES),
                "summary": f"Analysts react to {company}'s update with {stance} bias.",
                "impact": random.choice(IMPACTS),
            }
        )
    return articles


def fake_signals() -> Dict[str, List[Dict[str, str]]]:
    cards = []
    for ticker, company in COMPANIES:
        direction = random.choice(["BUY", "HOLD", "SELL"])
        cards.append(
            {
                "ticker": ticker,
                "company": company,
                "direction": direction,
                "confidence": random.randint(55, 90),
                "signals": random.randint(3, 10),
                "summary": f"{company} flow indicates {direction.lower()} bias over next 3d.",
                "horizon": random.choice(["1d", "3d", "1w"]),
                "risk": random.choice(["Low", "Medium", "High"]),
            }
        )
    return {
        "cards": cards,
        "bands": [
            {"label": "Positive", "percent": random.randint(30, 40)},
            {"label": "Negative", "percent": random.randint(20, 40)},
            {"label": "Neutral", "percent": random.randint(20, 30)},
        ],
    }


def _generate_index_series(latest: float, points: int = 18) -> List[Dict[str, float]]:
    current = latest
    series = []
    for step in reversed(range(points)):
        current = max(500, current + random.uniform(-100, 120))
        series.append({"step": step, "value": round(current, 2)})
    series.sort(key=lambda x: x["step"])
    series[-1]["value"] = round(latest, 2)
    return series


def fake_indices() -> List[Dict[str, str | float]]:
    snapshots = []
    for label, region in REGION_MAP.items():
        base = random.uniform(3000, 15000)
        change = random.uniform(-150, 200)
        current_value = base + change
        change_pct = (change / base) * 100
        trend = "Bullish" if change >= 0 else "Bearish"
        snapshots.append(
            {
                "name": label,
                "region": region,
                "value": round(current_value, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "trend": trend,
                "volatility": random.randint(80, 180),
                "series": _generate_index_series(current_value),
            }
        )
    return snapshots


def fake_watchlists() -> List[Dict[str, str]]:
    return [
        {"name": "US Megacap", "tickers": "AAPL, MSFT, AMZN", "signals": random.randint(5, 10)},
        {"name": "AI Momentum", "tickers": "NVDA, GOOGL, META", "signals": random.randint(5, 10)},
        {"name": "Macro Risk", "tickers": "JPM, TSLA, DIS", "signals": random.randint(5, 10)},
    ]


def sentiment_summary(articles: List[Dict[str, str]]) -> Dict[str, int | List[Tuple[str, int]]]:
    counts = {"buy": 0, "hold": 0, "sell": 0}
    ticker_counts: Dict[str, int] = {}
    for article in articles:
        counts[article["stance"]] += 1
        ticker_counts[article["ticker"]] = ticker_counts.get(article["ticker"], 0) + 1
    top = sorted(ticker_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]
    return {"counts": counts, "top": top}


def risk_alerts() -> List[Dict[str, str]]:
    levels = ["High", "Medium", "Low"]
    descriptions = [
        "Elevated volatility in AI basket following regulatory rumors.",
        "OPEC meeting signaling tighter supply—watch energy shorts.",
        "ECB minutes suggest hawkish tone; euro-sensitive assets at risk.",
        "Large dispersion between credit spreads and equities.",
        "Options market pricing unusual upside in semiconductors.",
    ]
    alerts = []
    for desc in descriptions:
        alerts.append(
            {
                "title": desc.split()[0] + " Alert",
                "description": desc,
                "severity": random.choice(levels),
                "timestamp": f"{random.randint(2, 45)}m ago",
            }
        )
    return alerts


def macro_snapshot() -> List[Dict[str, str]]:
    metrics = [
        ("US 10Y", random.uniform(3.5, 4.5)),
        ("Breakevens", random.uniform(2.0, 2.7)),
        ("DXY", random.uniform(95, 105)),
        ("WTI", random.uniform(70, 90)),
        ("Gold", random.uniform(1800, 2100)),
    ]
    return [
        {"asset": name, "value": f"{value:.2f}", "change": f"{random.uniform(-1, 1):+.2f}%"}
        for name, value in metrics
    ]


def trending_topics(articles: List[Dict[str, str]]) -> List[str]:
    tags = set()
    for article in articles:
        tags.add(article["impact"])
    return list(tags)


def fake_portfolio_series(days: int = 45) -> List[Dict[str, str]]:
    base = 100.0
    series: List[Dict[str, str]] = []
    for i in range(days):
        base += random.uniform(-1.5, 2.2)
        date = (datetime.utcnow() - timedelta(days=days - i)).strftime("%Y-%m-%d")
        series.append({"date": date, "value": round(base, 2)})
    return series


def sector_exposure() -> List[Dict[str, str]]:
    sectors = ["Technology", "Energy", "Healthcare", "Financials", "Consumer"]
    exposures = []
    for sector in sectors:
        weight = random.uniform(5, 35)
        pnl = random.uniform(-3, 4)
        exposures.append({"sector": sector, "weight": round(weight, 2), "pnl": round(pnl, 2)})
    return exposures


def generate_alert_feed(count: int = 10) -> List[Dict[str, str]]:
    templates = [
        ("Margin call risk", "Multiple long positions leveraged >5x in volatile sectors."),
        ("Liquidity stress", "Cross-asset spreads widening beyond 2 standard deviations."),
        ("Macro surprise", "Upcoming CPI release exceeding consensus by 0.5%."),
        ("Credit dispersion", "HY vs IG spread blowout signaled by CDS curves."),
        ("FX dislocation", "Dollar funding shortage in APAC markets."),
    ]
    alerts = []
    for _ in range(count):
        title, body = random.choice(templates)
        alerts.append(
            {
                "title": title,
                "body": body,
                "status": random.choice(["Unresolved", "Investigating", "Resolved"]) ,
                "assignee": random.choice(["Ops", "Risk", "PM Team"]),
            }
        )
    return alerts


def company_snapshot(ticker: str) -> Dict[str, float]:
    return {
        "price": round(random.uniform(40, 400), 2),
        "change": round(random.uniform(-5, 5), 2),
        "volume": round(random.uniform(5, 80), 2),
        "market_cap": round(random.uniform(50, 800), 2),
        "pe": round(random.uniform(10, 45), 1),
        "beta": round(random.uniform(0.7, 1.6), 2),
    }


def company_price_series(ticker: str, bias: str | None = None, interval_minutes: int = 5) -> List[Dict[str, float]]:
    """Generate intraday series with directional bias."""
    session_minutes = 6.5 * 60
    points = int(session_minutes // interval_minutes)
    start_time = datetime.utcnow().replace(hour=13, minute=30, second=0, microsecond=0)
    prev_close = random.uniform(40, 320)
    price = prev_close + random.uniform(-2, 2)

    sentiment = (bias or "neutral").lower()
    base_trend = {
        "buy": random.uniform(0.15, 0.35),
        "bullish": random.uniform(0.15, 0.35),
        "increase": random.uniform(0.15, 0.35),
        "sell": -random.uniform(0.15, 0.35),
        "bearish": -random.uniform(0.15, 0.35),
        "decrease": -random.uniform(0.15, 0.35),
    }.get(sentiment, random.uniform(-0.08, 0.08))

    morning_burst = random.uniform(0.8, 1.6) * (1 if base_trend >= 0 else -1)
    shock_center = random.uniform(0.35, 0.55)
    shock_magnitude = random.uniform(1.5, 3.2) * (1 if base_trend >= 0 else -1)
    series: List[Dict[str, float]] = []

    for i in range(points):
        progress = i / (points - 1)
        timestamp = start_time + timedelta(minutes=i * interval_minutes)

        morning_factor = morning_burst * math.exp(-progress * 6)
        trend_component = base_trend * (1 - 0.4 * progress)
        wave = math.sin(progress * math.pi * 1.5) * random.uniform(0.4, 1.2)
        shock = 0
        if abs(progress - shock_center) < 0.08:
            shock = shock_magnitude * (1 - abs(progress - shock_center) / 0.08)

        noise = random.uniform(-0.4, 0.4)
        increment = morning_factor + trend_component + wave + shock + noise
        price = max(1, price + increment)

        volume = random.randint(250_000, 2_500_000)
        if progress < 0.15 or progress > 0.85:
            volume = int(volume * 1.4)

        series.append(
            {
                "time": timestamp.isoformat(),
                "price": round(price, 2),
                "volume": volume,
                "prev_close": round(prev_close, 2),
            }
        )

    return series

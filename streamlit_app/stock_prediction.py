from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import random

from news_data import company_price_series, company_snapshot


@dataclass
class Prediction:
    direction: str
    confidence: int
    target_price: float
    timeframe: str
    factors: List[str]


@dataclass
class StockData:
    current_price: float
    change: float
    change_percent: float
    beta: float
    rsi: float
    volatility: float
    volume: int
    market_cap: float
    pe_ratio: float
    fifty_two_week_high: Optional[float]
    fifty_two_week_low: Optional[float]
    correlation: float
    average_volume: Optional[int]
    prediction: Optional[Prediction] = None


@dataclass
class Article:
    title: str
    summary: str
    source: str
    timestamp: datetime
    investment_recommendation: str


class StockPredictionModal:
    def __init__(self, ticker: str, articles: List[Article]):
        self.ticker = ticker
        self.articles = articles
        self.stock_data: Optional[StockData] = None
        self.loading = True

    def fetch_stock_data(self) -> StockData:
        snapshot = company_snapshot(self.ticker)
        data = StockData(
            current_price=snapshot["price"],
            change=snapshot["change"],
            change_percent=snapshot["change"] / snapshot["price"] * 100,
            beta=snapshot["beta"],
            rsi=random.uniform(20, 80),
            volatility=random.uniform(0.1, 0.3),
            volume=int(snapshot["volume"] * 1_000_000),
            market_cap=snapshot["market_cap"],
            pe_ratio=random.uniform(10, 40),
            fifty_two_week_high=snapshot["price"] * 1.1,
            fifty_two_week_low=snapshot["price"] * 0.9,
            correlation=random.uniform(0.3, 0.9),
            average_volume=random.randint(2_000_000, 5_000_000),
        )
        self.stock_data = data
        self.loading = False
        return data

    def generate_prediction_data(self, stock_data: StockData) -> StockData:
        prediction = Prediction(
            direction="bullish" if stock_data.change_percent > 0 else "bearish",
            confidence=random.randint(65, 90),
            target_price=stock_data.current_price * (1 + (stock_data.change_percent / 100) * 2),
            timeframe="3 months",
            factors=[
                "Technical analysis indicators",
                "Market sentiment analysis",
                "Earnings and financial metrics",
                "Industry sector performance",
                "Economic and market conditions",
            ],
        )
        stock_data.prediction = prediction
        return stock_data

    def get_related_articles(self, limit: int = 3) -> List[Article]:
        return self.articles[:limit]

    def get_modal_data(self) -> Dict[str, Any]:
        if self.loading or not self.stock_data:
            return {"loading": True, "message": "Loading stock data..."}

        data = self.generate_prediction_data(self.stock_data)
        related_articles = self.get_related_articles()

        return {
            "loading": False,
            "ticker": self.ticker,
            "stock_data": data,
            "prediction": data.prediction,
            "related_articles": related_articles,
            "price_series": company_price_series(self.ticker),
        }


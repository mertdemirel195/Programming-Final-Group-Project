from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List
import random


@dataclass
class ChartDataPoint:
    time: str
    price: float
    volume: int


@dataclass
class StockChartData:
    ticker: str
    current_price: float
    change: float
    change_percent: float
    chart_data: List[ChartDataPoint]
    is_positive: bool
    line_color: str
    days_range_low: float
    days_range_high: float
    volume: int
    avg_volume: int
    market_cap: float


class StockChart:
    def __init__(self, ticker: str, current_price: float, change: float, change_percent: float):
        self.ticker = ticker
        self.current_price = current_price
        self.change = change
        self.change_percent = change_percent

    def generate_chart_data(self) -> List[ChartDataPoint]:
        base_price = self.current_price - self.change
        data: List[ChartDataPoint] = []
        now = datetime.now()
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        for i in range(7):
            time = market_open + timedelta(hours=i)
            volatility = 0.01 + random.random() * 0.02
            trend = (self.change / base_price) * (i / 6)
            random_walk = (random.random() - 0.5) * volatility * base_price
            price = base_price + (trend * base_price) + random_walk
            if i == 6:
                price = self.current_price
            data.append(
                ChartDataPoint(
                    time=time.strftime("%I:%M %p"),
                    price=round(price, 2),
                    volume=random.randint(500_000, 2_500_000),
                )
            )
        return data

    def to_dict(self) -> Dict[str, Any]:
        chart_data = self.generate_chart_data()
        is_positive = self.change >= 0
        line_color = "#10b981" if is_positive else "#ef4444"
        return {
            "ticker": self.ticker,
            "current_price": self.current_price,
            "change": self.change,
            "change_percent": self.change_percent,
            "is_positive": is_positive,
            "line_color": line_color,
            "chart_data": [point.__dict__ for point in chart_data],
            "stats": {
                "days_range_low": round(self.current_price * 0.98, 2),
                "days_range_high": round(self.current_price * 1.02, 2),
                "volume": random.randint(1_000_000, 6_000_000),
                "avg_volume": random.randint(2_000_000, 5_000_000),
                "market_cap": round(self.current_price * 10_000_000_000 / 1_000_000_000, 1),
            },
            "metadata": {
                "close_time": datetime.now().strftime("%I:%M:%S %p"),
                "exchange": "NYSE - Nasdaq Real Time Price • USD",
            },
        }


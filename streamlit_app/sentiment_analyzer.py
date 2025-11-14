from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SentimentData:
    count: int
    percentage: int
    color: str
    label: str


@dataclass
class PredictionData:
    count: int
    label: str
    emoji: str
    color: str


@dataclass
class SentimentAnalysis:
    positive: SentimentData
    negative: SentimentData
    neutral: SentimentData
    total: int


@dataclass
class MarketPredictions:
    bullish: PredictionData
    bearish: PredictionData
    neutral: PredictionData


@dataclass
class MarketOverview:
    total_articles: int
    sources: int
    last_updated: str


class SentimentAnalyzer:
    def __init__(self, articles: List[Dict[str, Any]]):
        self.articles = articles
        self.total = len(articles)

    def calculate_sentiment_counts(self) -> Dict[str, int]:
        counts = Counter()
        for article in self.articles:
            counts[article.get("sentiment", "neutral")] += 1
        return counts

    def calculate_prediction_counts(self) -> Dict[str, int]:
        counts = Counter()
        for article in self.articles:
            counts[article.get("stockPrediction", "neutral")] += 1
        return counts

    def get_percentage(self, count: int) -> int:
        return 0 if self.total == 0 else round(count / self.total * 100)

    def get_sentiment_analysis(self) -> SentimentAnalysis:
        counts = self.calculate_sentiment_counts()
        positive = counts.get("positive", 0)
        negative = counts.get("negative", 0)
        neutral = counts.get("neutral", 0)
        return SentimentAnalysis(
            positive=SentimentData(positive, self.get_percentage(positive), "green", "Positive"),
            negative=SentimentData(negative, self.get_percentage(negative), "red", "Negative"),
            neutral=SentimentData(neutral, self.get_percentage(neutral), "yellow", "Neutral"),
            total=self.total,
        )

    def get_market_predictions(self) -> MarketPredictions:
        counts = self.calculate_prediction_counts()
        return MarketPredictions(
            bullish=PredictionData(counts.get("increase", 0), "Bullish", "↗️", "green"),
            bearish=PredictionData(counts.get("decrease", 0), "Bearish", "↘️", "red"),
            neutral=PredictionData(counts.get("neutral", 0), "Neutral", "➡️", "gray"),
        )

    def get_market_overview(self) -> MarketOverview:
        return MarketOverview(
            total_articles=self.total,
            sources=32,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

    def to_dict(self) -> Dict[str, Any]:
        sentiment = self.get_sentiment_analysis()
        predictions = self.get_market_predictions()
        overview = self.get_market_overview()
        return {
            "sentiment_analysis": {
                "positive": sentiment.positive.__dict__,
                "negative": sentiment.negative.__dict__,
                "neutral": sentiment.neutral.__dict__,
                "total": sentiment.total,
            },
            "market_predictions": {
                "bullish": predictions.bullish.__dict__,
                "bearish": predictions.bearish.__dict__,
                "neutral": predictions.neutral.__dict__,
            },
            "market_overview": overview.__dict__,
        }


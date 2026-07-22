"""
Sentiment Analysis module.
Analyzes news articles for market sentiment using VADER + IBM Granite.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER_AVAILABLE = True
except ImportError:
    _VADER_AVAILABLE = False
    logger.warning("vaderSentiment not installed — using keyword fallback")

_POSITIVE_KEYWORDS = [
    "beat", "exceed", "record", "growth", "surge", "rally", "profit",
    "strong", "upgrade", "outperform", "bullish", "buy", "raise", "expand",
    "innovative", "breakthrough", "acquisition", "partnership",
]
_NEGATIVE_KEYWORDS = [
    "miss", "decline", "loss", "drop", "downgrade", "underperform", "bearish",
    "sell", "cut", "layoff", "lawsuit", "investigation", "debt", "bankrupt",
    "recall", "scandal", "warning", "disappoint",
]


class SentimentAnalyzer:
    """Performs sentiment analysis on financial news articles."""

    def __init__(self):
        self._vader = SentimentIntensityAnalyzer() if _VADER_AVAILABLE else None

    def analyze(self, news_articles: list[dict], ticker: str) -> dict[str, Any]:
        if not news_articles:
            return self._empty_result(ticker)

        logger.info("Analyzing sentiment for %d articles [%s]", len(news_articles), ticker)

        article_scores = []
        for article in news_articles:
            text = f"{article.get('title', '')} {article.get('description', '')}".strip()
            score = self._score_text(text)
            article_scores.append({
                "title": article.get("title", ""),
                "source": article.get("source", ""),
                "published_at": article.get("published_at", ""),
                "compound_score": score["compound"],
                "positive": score["pos"],
                "negative": score["neg"],
                "neutral": score["neu"],
                "label": self._label(score["compound"]),
            })

        # Aggregate
        compounds = [a["compound_score"] for a in article_scores]
        avg_compound = sum(compounds) / len(compounds) if compounds else 0.0

        positive_count = sum(1 for a in article_scores if a["label"] == "positive")
        negative_count = sum(1 for a in article_scores if a["label"] == "negative")
        neutral_count = sum(1 for a in article_scores if a["label"] == "neutral")

        # Overall sentiment label
        if avg_compound >= 0.10:
            overall_label = "bullish"
        elif avg_compound >= 0.03:
            overall_label = "slightly_bullish"
        elif avg_compound <= -0.10:
            overall_label = "bearish"
        elif avg_compound <= -0.03:
            overall_label = "slightly_bearish"
        else:
            overall_label = "neutral"

        # Normalised sentiment score 0-100
        sentiment_score = round((avg_compound + 1) / 2 * 100, 1)

        top_positive = sorted(
            [a for a in article_scores if a["label"] == "positive"],
            key=lambda x: x["compound_score"],
            reverse=True,
        )[:3]
        top_negative = sorted(
            [a for a in article_scores if a["label"] == "negative"],
            key=lambda x: x["compound_score"],
        )[:3]

        return {
            "ticker": ticker,
            "article_count": len(article_scores),
            "avg_compound_score": round(avg_compound, 4),
            "sentiment_score": sentiment_score,
            "overall_label": overall_label,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "top_positive_articles": top_positive,
            "top_negative_articles": top_negative,
            "all_scores": article_scores,
            "method": "vader" if _VADER_AVAILABLE else "keyword",
        }

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    def _score_text(self, text: str) -> dict:
        if self._vader:
            return self._vader.polarity_scores(text)
        return self._keyword_score(text)

    @staticmethod
    def _keyword_score(text: str) -> dict:
        text_lower = text.lower()
        pos_count = sum(1 for kw in _POSITIVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in _NEGATIVE_KEYWORDS if kw in text_lower)
        total = pos_count + neg_count or 1
        compound = (pos_count - neg_count) / total
        pos = pos_count / total
        neg = neg_count / total
        return {"compound": compound, "pos": pos, "neg": neg, "neu": 1 - pos - neg}

    @staticmethod
    def _label(compound: float) -> str:
        if compound >= 0.05:
            return "positive"
        if compound <= -0.05:
            return "negative"
        return "neutral"

    @staticmethod
    def _empty_result(ticker: str) -> dict:
        return {
            "ticker": ticker,
            "article_count": 0,
            "avg_compound_score": 0.0,
            "sentiment_score": 50.0,
            "overall_label": "neutral",
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "top_positive_articles": [],
            "top_negative_articles": [],
            "all_scores": [],
            "method": "none",
        }

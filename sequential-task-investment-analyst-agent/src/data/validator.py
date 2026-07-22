"""
Data validation and cleaning module.
Ensures collected financial data meets quality thresholds before analysis.
"""

import logging
import math
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

REQUIRED_INFO_FIELDS = [
    "shortName",
    "sector",
    "industry",
    "marketCap",
    "currentPrice",
]


class DataValidator:
    """Validates and cleans raw collected financial data."""

    def __init__(self):
        self.validation_report: dict[str, Any] = {}

    def validate_and_clean(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Main entry point. Returns a cleaned data dict plus a
        ``_validation`` key describing quality findings.
        """
        ticker = raw_data.get("ticker", "UNKNOWN")
        logger.info("Validating data for %s", ticker)

        cleaned = dict(raw_data)
        issues: list[str] = []
        warnings: list[str] = []

        # ── yfinance ────────────────────────────────────────────
        yf = cleaned.get("yfinance", {})
        info = yf.get("info", {})

        for field in REQUIRED_INFO_FIELDS:
            if not info.get(field):
                issues.append(f"yfinance.info missing: {field}")

        # Sanitise numeric fields in info
        cleaned_info = {}
        for k, v in info.items():
            cleaned_info[k] = self._sanitise_number(v)
        yf["info"] = cleaned_info

        # Validate price history
        history = yf.get("history", {})
        close_prices = history.get("close", [])
        if len(close_prices) < 20:
            warnings.append(f"Price history has only {len(close_prices)} data points (< 20)")

        close_prices = [p for p in close_prices if self._is_valid_price(p)]
        history["close"] = close_prices

        # ── Alpha Vantage overview ───────────────────────────────
        av = cleaned.get("alpha_vantage", {})
        av_overview = av.get("overview", {})
        if not av_overview:
            warnings.append("Alpha Vantage overview missing — will rely on yfinance only")

        # Remove AV Note fields (rate limit messages)
        if "Note" in av_overview:
            warnings.append("Alpha Vantage returned rate-limit Note — overview data may be incomplete")
            av["overview"] = {}

        # ── News ────────────────────────────────────────────────
        news = cleaned.get("news", [])
        cleaned_news = []
        for article in news:
            if article.get("title") and article.get("description"):
                cleaned_news.append(article)
        if len(cleaned_news) < len(news):
            warnings.append(f"Removed {len(news) - len(cleaned_news)} news articles with missing fields")
        cleaned["news"] = cleaned_news

        # ── Completeness score ───────────────────────────────────
        total_checks = 10
        passed = total_checks - len(issues)
        completeness = round(max(0.0, passed / total_checks) * 100, 1)

        cleaned["_validation"] = {
            "ticker": ticker,
            "validated_at": datetime.utcnow().isoformat(),
            "issues": issues,
            "warnings": warnings,
            "completeness_score": completeness,
            "is_usable": len(issues) == 0,
        }

        if issues:
            logger.warning("Validation issues for %s: %s", ticker, issues)
        logger.info("Validation complete for %s — completeness %.1f%%", ticker, completeness)
        return cleaned

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    @staticmethod
    def _sanitise_number(value: Any) -> Any:
        """Replace NaN/Inf floats with None to avoid downstream JSON errors."""
        if isinstance(value, float):
            if math.isnan(value) or math.isinf(value):
                return None
        return value

    @staticmethod
    def _is_valid_price(price: Any) -> bool:
        if not isinstance(price, (int, float)):
            return False
        if math.isnan(price) or math.isinf(price):
            return False
        return price > 0

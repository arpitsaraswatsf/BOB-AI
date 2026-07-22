"""
Risk Detection module.
Identifies financial and market risk factors, computes a composite risk score.
"""

import logging
from typing import Any

from config.settings import RISK_THRESHOLDS

logger = logging.getLogger(__name__)


class RiskDetector:
    """Detects and scores risk factors from KPIs, ratios, and sentiment data."""

    def detect(
        self,
        kpis: dict[str, Any],
        ratios: dict[str, Any],
        sentiment: dict[str, Any],
    ) -> dict[str, Any]:
        ticker = kpis.get("ticker", "UNKNOWN")
        logger.info("Risk detection for %s", ticker)

        risk_factors: list[dict] = []

        # ── Financial Risks ─────────────────────────────────────
        self._check(risk_factors, "HIGH_DEBT",
                    kpis.get("debt_to_equity"),
                    lambda v: v / 100 > RISK_THRESHOLDS["debt_to_equity_high"] if v > 20 else v > RISK_THRESHOLDS["debt_to_equity_high"],
                    "Debt-to-Equity is above {v:.2f} threshold",
                    severity="high")

        self._check(risk_factors, "LOW_LIQUIDITY",
                    kpis.get("current_ratio"),
                    lambda v: v < RISK_THRESHOLDS["current_ratio_low"],
                    "Current Ratio {v:.2f} below 1.0 — short-term liquidity risk",
                    severity="high")

        self._check(risk_factors, "LOW_PROFITABILITY",
                    kpis.get("profit_margin"),
                    lambda v: v < RISK_THRESHOLDS["profit_margin_low"],
                    "Net Profit Margin {v:.2%} is very thin",
                    severity="medium")

        self._check(risk_factors, "NEGATIVE_NET_INCOME",
                    kpis.get("net_income"),
                    lambda v: v < 0,
                    "Net income is negative (${v:,.0f})",
                    severity="high")

        self._check(risk_factors, "NEGATIVE_FCF",
                    kpis.get("free_cash_flow"),
                    lambda v: v < 0,
                    "Free Cash Flow is negative — cash burn risk",
                    severity="medium")

        self._check(risk_factors, "HIGH_VALUATION",
                    kpis.get("pe_ratio"),
                    lambda v: v > RISK_THRESHOLDS["pe_ratio_high"],
                    "P/E Ratio {v:.1f} is elevated — valuation risk if growth slows",
                    severity="medium")

        self._check(risk_factors, "LOW_ROE",
                    kpis.get("roe"),
                    lambda v: 0 < v < RISK_THRESHOLDS["roe_low"],
                    "ROE {v:.2%} is below 5% — weak capital efficiency",
                    severity="low")

        self._check(risk_factors, "NEGATIVE_ROE",
                    kpis.get("roe"),
                    lambda v: v < 0,
                    "ROE {v:.2%} is negative",
                    severity="high")

        self._check(risk_factors, "REVENUE_DECLINE",
                    kpis.get("revenue_growth"),
                    lambda v: v < -0.05,
                    "Revenue declining YoY ({v:.1%})",
                    severity="high")

        self._check(risk_factors, "HIGH_SHORT_INTEREST",
                    kpis.get("short_percent_of_float"),
                    lambda v: v > 0.15,
                    "Short interest {v:.1%} of float — elevated bearish positioning",
                    severity="medium")

        self._check(risk_factors, "HIGH_BETA",
                    kpis.get("beta"),
                    lambda v: v > 2.0,
                    "Beta {v:.2f} — high volatility vs market",
                    severity="medium")

        # ── Sentiment Risk ───────────────────────────────────────
        sentiment_score = sentiment.get("sentiment_score", 50)
        if sentiment_score < 30:
            risk_factors.append({
                "code": "NEGATIVE_SENTIMENT",
                "message": f"News sentiment score {sentiment_score:.0f}/100 is significantly negative",
                "severity": "high",
            })
        elif sentiment_score < 40:
            risk_factors.append({
                "code": "MILD_NEGATIVE_SENTIMENT",
                "message": f"News sentiment score {sentiment_score:.0f}/100 is mildly negative",
                "severity": "low",
            })

        # ── Risk Score (0-100, higher = riskier) ────────────────
        severity_weights = {"high": 20, "medium": 10, "low": 5}
        raw_risk = sum(severity_weights.get(f["severity"], 5) for f in risk_factors)
        risk_score = min(100, raw_risk)

        if risk_score >= 70:
            risk_level = "very_high"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "moderate"
        elif risk_score >= 15:
            risk_level = "low"
        else:
            risk_level = "very_low"

        return {
            "ticker": ticker,
            "risk_factors": risk_factors,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "high_severity_count": sum(1 for f in risk_factors if f["severity"] == "high"),
            "medium_severity_count": sum(1 for f in risk_factors if f["severity"] == "medium"),
            "low_severity_count": sum(1 for f in risk_factors if f["severity"] == "low"),
        }

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    @staticmethod
    def _check(
        factors: list,
        code: str,
        value: Any,
        condition,
        message_template: str,
        severity: str,
    ):
        if value is None:
            return
        try:
            if condition(value):
                factors.append({
                    "code": code,
                    "message": message_template.format(v=value),
                    "severity": severity,
                    "value": value,
                })
        except Exception as exc:
            logger.debug("Risk check %s error: %s", code, exc)

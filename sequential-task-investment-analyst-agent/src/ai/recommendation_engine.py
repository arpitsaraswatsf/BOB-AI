"""
Recommendation Engine.
Synthesizes all analysis outputs into a final investment recommendation.
"""

import logging
from typing import Any

from config.settings import RECOMMENDATION_THRESHOLDS

logger = logging.getLogger(__name__)

RECOMMENDATION_LEVELS = ["Strong Sell", "Sell", "Hold", "Buy", "Strong Buy"]

RECOMMENDATION_COLORS = {
    "Strong Buy": "#16a34a",
    "Buy": "#65a30d",
    "Hold": "#d97706",
    "Sell": "#ea580c",
    "Strong Sell": "#dc2626",
}


class RecommendationEngine:
    """Synthesizes all analysis components into a final investment verdict."""

    def generate(
        self,
        kpis: dict[str, Any],
        ratios: dict[str, Any],
        sentiment: dict[str, Any],
        risk: dict[str, Any],
        competitor: dict[str, Any],
        ai_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        ticker = kpis.get("ticker", "UNKNOWN")
        logger.info("Generating final recommendation for %s", ticker)

        # Component scores (0-100)
        financial_score = ratios.get("overall_financial_score", 50.0)
        sentiment_score = sentiment.get("sentiment_score", 50.0)
        risk_score = risk.get("risk_score", 50.0)

        # Safety score inverts risk (high risk → low safety)
        safety_component = max(0, 100 - risk_score)

        # Competitor ranking bonus/penalty
        competitor_bonus = self._competitor_bonus(ticker, competitor)

        # Analyst consensus weight
        analyst_score = self._analyst_score(kpis)

        # Upside potential
        upside_score = self._upside_score(kpis)

        # Weighted composite recommendation score
        composite = (
            financial_score * 0.35
            + sentiment_score * 0.15
            + safety_component * 0.20
            + analyst_score * 0.15
            + upside_score * 0.10
            + competitor_bonus * 0.05
        )
        composite = round(max(0.0, min(100.0, composite)), 1)

        # Map to recommendation
        ai_recommendation = ai_analysis.get("recommendation", "Hold")
        quantitative_recommendation = self._map_to_recommendation(composite)

        # Final recommendation: blend AI + quant (AI gets slight override authority)
        final_recommendation = self._blend_recommendations(
            ai_recommendation, quantitative_recommendation, composite
        )

        # Build reasoning bullets
        reasoning = self._build_reasoning(
            kpis, ratios, sentiment, risk, composite, final_recommendation
        )

        return {
            "ticker": ticker,
            "company_name": kpis.get("company_name", ""),
            "current_price": kpis.get("current_price"),
            "analyst_target_price": kpis.get("analyst_target_price"),
            "final_recommendation": final_recommendation,
            "recommendation_color": RECOMMENDATION_COLORS.get(final_recommendation, "#6b7280"),
            "composite_score": composite,
            "component_scores": {
                "financial": round(financial_score, 1),
                "sentiment": round(sentiment_score, 1),
                "safety": round(safety_component, 1),
                "analyst": round(analyst_score, 1),
                "upside": round(upside_score, 1),
                "competitor_bonus": round(competitor_bonus, 1),
            },
            "quantitative_recommendation": quantitative_recommendation,
            "ai_recommendation": ai_recommendation,
            "reasoning": reasoning,
            "full_analysis": ai_analysis.get("analysis_text", ""),
            "growth_predictions": "",
            "risk_level": risk.get("risk_level", "unknown"),
            "risk_score": risk.get("risk_score", 0),
            "sentiment_label": sentiment.get("overall_label", "neutral"),
        }

    # ──────────────────────────────────────────────
    # SCORING COMPONENTS
    # ──────────────────────────────────────────────

    @staticmethod
    def _analyst_score(kpis: dict) -> float:
        """Convert analyst recommendation key to 0-100 score."""
        mapping = {
            "strongbuy": 90,
            "buy": 72,
            "hold": 50,
            "underperform": 30,
            "sell": 15,
        }
        rec_key = kpis.get("analyst_recommendation", "").lower().replace(" ", "").replace("_", "")
        return float(mapping.get(rec_key, 50))

    @staticmethod
    def _upside_score(kpis: dict) -> float:
        """Calculate upside potential from current price to analyst target."""
        current = kpis.get("current_price")
        target = kpis.get("analyst_target_price")
        if not current or not target or current <= 0:
            return 50.0
        upside = (target - current) / current
        if upside > 0.30: return 90.0
        if upside > 0.20: return 78.0
        if upside > 0.10: return 65.0
        if upside > 0.05: return 58.0
        if upside >= 0: return 50.0
        if upside > -0.10: return 38.0
        if upside > -0.20: return 25.0
        return 15.0

    @staticmethod
    def _competitor_bonus(ticker: str, competitor: dict) -> float:
        """Compute score based on where target ranks among peers."""
        rankings = competitor.get("rankings", {})
        if not rankings:
            return 50.0

        favorable_metrics = ["roe", "roa", "profit_margin", "revenue_growth", "free_cash_flow"]
        rank_scores = []

        for metric in favorable_metrics:
            ranked = rankings.get(metric, [])
            if ticker in ranked:
                position = ranked.index(ticker)
                total = len(ranked)
                if total > 1:
                    percentile = (total - 1 - position) / (total - 1) * 100
                    rank_scores.append(percentile)

        return round(sum(rank_scores) / len(rank_scores), 1) if rank_scores else 50.0

    # ──────────────────────────────────────────────
    # RECOMMENDATION MAPPING
    # ──────────────────────────────────────────────

    @staticmethod
    def _map_to_recommendation(score: float) -> str:
        if score >= RECOMMENDATION_THRESHOLDS["strong_buy"]:
            return "Strong Buy"
        if score >= RECOMMENDATION_THRESHOLDS["buy"]:
            return "Buy"
        if score >= RECOMMENDATION_THRESHOLDS["hold"]:
            return "Hold"
        if score >= RECOMMENDATION_THRESHOLDS["sell"]:
            return "Sell"
        return "Strong Sell"

    @staticmethod
    def _blend_recommendations(ai_rec: str, quant_rec: str, score: float) -> str:
        """When AI and quant disagree, use score to arbitrate."""
        if ai_rec == quant_rec:
            return ai_rec
        # If they differ by one step, defer to quant which is more objective
        order = {r: i for i, r in enumerate(RECOMMENDATION_LEVELS)}
        ai_idx = order.get(ai_rec, 2)
        quant_idx = order.get(quant_rec, 2)
        if abs(ai_idx - quant_idx) <= 1:
            return quant_rec
        # Large disagreement: take the more conservative (middle-ward) option
        mid = 2
        final_idx = ai_idx if abs(ai_idx - mid) < abs(quant_idx - mid) else quant_idx
        return RECOMMENDATION_LEVELS[final_idx]

    # ──────────────────────────────────────────────
    # REASONING BULLETS
    # ──────────────────────────────────────────────

    def _build_reasoning(
        self,
        kpis: dict,
        ratios: dict,
        sentiment: dict,
        risk: dict,
        composite: float,
        recommendation: str,
    ) -> list[str]:
        reasons: list[str] = []

        # Financial quality
        qs = ratios.get("quality_score", 50)
        if qs >= 70:
            reasons.append(f"Strong financial quality score ({qs:.0f}/100) driven by high ROE/ROA and healthy margins.")
        elif qs <= 35:
            reasons.append(f"Weak financial quality score ({qs:.0f}/100) — margins and returns need improvement.")

        # Growth
        gs = ratios.get("growth_score", 50)
        rev_growth = kpis.get("revenue_growth")
        if gs >= 70 and rev_growth:
            reasons.append(f"Revenue growing at {rev_growth*100:.1f}% YoY supports a positive growth outlook.")
        elif gs <= 35:
            reasons.append("Growth momentum is limited — watch for acceleration before increasing exposure.")

        # Valuation
        pe = kpis.get("pe_ratio")
        vs = ratios.get("value_score", 50)
        if pe and pe < 20:
            reasons.append(f"Attractive valuation with P/E of {pe:.1f}x relative to sector peers.")
        elif pe and pe > 35:
            reasons.append(f"Elevated P/E of {pe:.1f}x prices in significant growth — downside risk if targets are missed.")

        # Risk
        rl = risk.get("risk_level", "moderate")
        rs = risk.get("risk_score", 0)
        if rs <= 20:
            reasons.append("Low risk profile with healthy liquidity and modest leverage.")
        elif rs >= 60:
            high_risks = [f["code"] for f in risk.get("risk_factors", []) if f["severity"] == "high"]
            reasons.append(f"Elevated risk ({rl}) — key concerns: {', '.join(high_risks[:3]) or 'see risk report'}.")

        # Sentiment
        sl = sentiment.get("overall_label", "neutral")
        ss = sentiment.get("sentiment_score", 50)
        if sl in ("bullish", "slightly_bullish"):
            reasons.append(f"News sentiment is {sl.replace('_', ' ')} ({ss:.0f}/100) — market narrative is supportive.")
        elif sl in ("bearish", "slightly_bearish"):
            reasons.append(f"News sentiment is {sl.replace('_', ' ')} ({ss:.0f}/100) — near-term headwinds in media coverage.")

        # Upside
        current = kpis.get("current_price")
        target = kpis.get("analyst_target_price")
        if current and target:
            upside = (target - current) / current * 100
            if upside > 10:
                reasons.append(f"Analyst consensus target ${target:.2f} implies {upside:.1f}% upside from current levels.")
            elif upside < -5:
                reasons.append(f"Analyst consensus target ${target:.2f} implies {abs(upside):.1f}% downside risk.")

        if not reasons:
            reasons.append(f"Composite score of {composite:.0f}/100 supports a {recommendation} rating.")

        return reasons

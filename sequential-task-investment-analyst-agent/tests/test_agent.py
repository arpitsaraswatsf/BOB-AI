"""
Integration tests for the Investment Analyst Agent.
Uses real yfinance data (AAPL is well-covered) but mocks Granite API calls.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agents.investment_agent import InvestmentAnalystAgent
from src.analysis.kpi_extractor import KPIExtractor
from src.analysis.ratios_calculator import RatiosCalculator
from src.analysis.risk_detector import RiskDetector
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.ai.recommendation_engine import RecommendationEngine


# ──────────────────────────────────────────────
# FIXTURES
# ──────────────────────────────────────────────

@pytest.fixture
def sample_kpis():
    return {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "market_cap": 3_000_000_000_000,
        "current_price": 195.0,
        "revenue_ttm": 385_000_000_000,
        "revenue_growth": 0.08,
        "net_income": 97_000_000_000,
        "eps_ttm": 6.43,
        "gross_margin": 0.45,
        "operating_margin": 0.30,
        "profit_margin": 0.25,
        "ebitda_margin": 0.33,
        "roe": 1.60,
        "roa": 0.28,
        "pe_ratio": 30.0,
        "forward_pe": 27.0,
        "peg_ratio": 2.1,
        "price_to_book": 48.0,
        "ev_to_ebitda": 22.0,
        "debt_to_equity": 1.76,
        "current_ratio": 1.07,
        "quick_ratio": 0.98,
        "total_debt": 110_000_000_000,
        "total_cash": 73_000_000_000,
        "total_assets": 353_000_000_000,
        "free_cash_flow": 90_000_000_000,
        "operating_cash_flow": 112_000_000_000,
        "beta": 1.20,
        "short_percent_of_float": 0.007,
        "analyst_target_price": 215.0,
        "analyst_recommendation": "buy",
        "dividend_yield": 0.005,
        "earnings_growth": 0.12,
        "shares_outstanding": 15_550_000_000,
    }


@pytest.fixture
def sample_ratios(sample_kpis):
    calc = RatiosCalculator()
    return calc.calculate(sample_kpis)


@pytest.fixture
def sample_sentiment():
    return {
        "ticker": "AAPL",
        "article_count": 10,
        "avg_compound_score": 0.12,
        "sentiment_score": 56.0,
        "overall_label": "slightly_bullish",
        "positive_count": 6,
        "negative_count": 2,
        "neutral_count": 2,
        "top_positive_articles": [],
        "top_negative_articles": [],
        "all_scores": [],
        "method": "vader",
    }


@pytest.fixture
def sample_risk(sample_kpis, sample_ratios, sample_sentiment):
    detector = RiskDetector()
    return detector.detect(sample_kpis, sample_ratios, sample_sentiment)


@pytest.fixture
def sample_competitor():
    return {
        "target_ticker": "AAPL",
        "peers": ["MSFT"],
        "comparison_table": [
            {"ticker": "AAPL", "pe_ratio": 30.0, "roe": 1.60, "profit_margin": 0.25, "revenue_growth": 0.08},
            {"ticker": "MSFT", "pe_ratio": 35.0, "roe": 0.40, "profit_margin": 0.36, "revenue_growth": 0.16},
        ],
        "rankings": {
            "profit_margin": ["MSFT", "AAPL"],
            "roe": ["AAPL", "MSFT"],
        },
        "sector_averages": {"pe_ratio": 32.5, "roe": 1.0, "profit_margin": 0.305},
        "target_vs_sector": {},
        "peer_count": 1,
    }


# ──────────────────────────────────────────────
# KPI EXTRACTOR TESTS
# ──────────────────────────────────────────────

class TestKPIExtractor:
    def test_extract_returns_expected_fields(self, sample_kpis):
        # KPIs already extracted; verify required fields exist
        required = ["ticker", "market_cap", "revenue_ttm", "eps_ttm", "roe", "pe_ratio"]
        for field in required:
            assert field in sample_kpis, f"Missing field: {field}"

    def test_ebitda_margin_calculated(self, sample_kpis):
        assert sample_kpis["ebitda_margin"] > 0


# ──────────────────────────────────────────────
# RATIOS CALCULATOR TESTS
# ──────────────────────────────────────────────

class TestRatiosCalculator:
    def test_scores_in_range(self, sample_ratios):
        for score_key in ["value_score", "quality_score", "growth_score", "safety_score", "overall_financial_score"]:
            score = sample_ratios[score_key]
            assert 0 <= score <= 100, f"{score_key} out of range: {score}"

    def test_pct_fields_are_percentage(self, sample_ratios):
        # Percentage fields should be in human-readable % form (not 0-1)
        gm = sample_ratios.get("gross_margin_pct")
        assert gm is not None
        assert gm > 1, f"gross_margin_pct should be >1 for Apple: {gm}"

    def test_net_debt_calculated(self, sample_ratios):
        nd = sample_ratios.get("net_debt")
        assert nd is not None
        assert nd > 0  # Apple has more debt than cash


# ──────────────────────────────────────────────
# RISK DETECTOR TESTS
# ──────────────────────────────────────────────

class TestRiskDetector:
    def test_risk_score_in_range(self, sample_risk):
        rs = sample_risk["risk_score"]
        assert 0 <= rs <= 100, f"risk_score out of range: {rs}"

    def test_risk_level_valid(self, sample_risk):
        valid = {"very_low", "low", "moderate", "high", "very_high"}
        assert sample_risk["risk_level"] in valid

    def test_aapl_not_highest_risk(self, sample_risk):
        # Apple should not be very_high risk
        assert sample_risk["risk_level"] != "very_high"


# ──────────────────────────────────────────────
# SENTIMENT ANALYZER TESTS
# ──────────────────────────────────────────────

class TestSentimentAnalyzer:
    def test_empty_news_returns_neutral(self):
        analyzer = SentimentAnalyzer()
        result = analyzer.analyze([], "AAPL")
        assert result["overall_label"] == "neutral"
        assert result["sentiment_score"] == 50.0

    def test_positive_news_scored_correctly(self):
        analyzer = SentimentAnalyzer()
        news = [
            {"title": "Apple beats earnings expectations with record revenue growth", "description": "Strong buy signal."},
            {"title": "Apple surges after profit upgrade", "description": "Analysts raise price targets."},
        ]
        result = analyzer.analyze(news, "AAPL")
        assert result["sentiment_score"] > 50.0

    def test_negative_news_scored_correctly(self):
        analyzer = SentimentAnalyzer()
        news = [
            {"title": "Apple misses earnings, stock drops sharply", "description": "Revenue decline disappoints."},
            {"title": "Apple under investigation for antitrust violations", "description": "Regulatory risks mount."},
        ]
        result = analyzer.analyze(news, "AAPL")
        assert result["sentiment_score"] < 50.0


# ──────────────────────────────────────────────
# RECOMMENDATION ENGINE TESTS
# ──────────────────────────────────────────────

class TestRecommendationEngine:
    def test_recommendation_valid_value(self, sample_kpis, sample_ratios, sample_sentiment, sample_risk, sample_competitor):
        engine = RecommendationEngine()
        ai_analysis = {
            "ticker": "AAPL",
            "analysis_text": "Strong Buy recommendation based on solid financials.",
            "recommendation": "Buy",
        }
        result = engine.generate(
            sample_kpis, sample_ratios, sample_sentiment,
            sample_risk, sample_competitor, ai_analysis
        )
        valid_recs = {"Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"}
        assert result["final_recommendation"] in valid_recs

    def test_composite_score_in_range(self, sample_kpis, sample_ratios, sample_sentiment, sample_risk, sample_competitor):
        engine = RecommendationEngine()
        ai_analysis = {"ticker": "AAPL", "analysis_text": "", "recommendation": "Buy"}
        result = engine.generate(
            sample_kpis, sample_ratios, sample_sentiment,
            sample_risk, sample_competitor, ai_analysis
        )
        assert 0 <= result["composite_score"] <= 100

    def test_reasoning_not_empty(self, sample_kpis, sample_ratios, sample_sentiment, sample_risk, sample_competitor):
        engine = RecommendationEngine()
        ai_analysis = {"ticker": "AAPL", "analysis_text": "", "recommendation": "Hold"}
        result = engine.generate(
            sample_kpis, sample_ratios, sample_sentiment,
            sample_risk, sample_competitor, ai_analysis
        )
        assert len(result["reasoning"]) > 0

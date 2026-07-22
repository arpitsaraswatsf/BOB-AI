"""
Main Investment Analyst Agent — orchestrates the full sequential workflow.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from src.data.collector import DataCollector
from src.data.validator import DataValidator
from src.analysis.kpi_extractor import KPIExtractor
from src.analysis.ratios_calculator import RatiosCalculator
from src.analysis.competitor_analyzer import CompetitorAnalyzer
from src.analysis.sentiment_analyzer import SentimentAnalyzer
from src.analysis.risk_detector import RiskDetector
from src.ai.granite_client import GraniteAI
from src.ai.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    name: str
    status: str = "pending"      # pending | running | completed | failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: Optional[float] = None
    error: Optional[str] = None


@dataclass
class AnalysisResult:
    ticker: str
    steps: list[WorkflowStep] = field(default_factory=list)
    raw_data: dict = field(default_factory=dict)
    validated_data: dict = field(default_factory=dict)
    kpis: dict = field(default_factory=dict)
    ratios: dict = field(default_factory=dict)
    competitor_analysis: dict = field(default_factory=dict)
    sentiment: dict = field(default_factory=dict)
    risk: dict = field(default_factory=dict)
    ai_analysis: dict = field(default_factory=dict)
    growth_predictions: dict = field(default_factory=dict)
    recommendation: dict = field(default_factory=dict)
    workflow_started_at: Optional[str] = None
    workflow_completed_at: Optional[str] = None
    total_duration_seconds: Optional[float] = None
    success: bool = False
    errors: list[str] = field(default_factory=list)


WORKFLOW_STEPS = [
    "data_collection",
    "data_validation",
    "kpi_extraction",
    "ratio_calculation",
    "competitor_analysis",
    "sentiment_analysis",
    "risk_detection",
    "ai_analysis",
    "growth_predictions",
    "recommendation_generation",
]


class InvestmentAnalystAgent:
    """
    Sequential workflow agent that takes a ticker symbol and produces
    a comprehensive investment analysis report.
    """

    def __init__(self):
        self._collector = DataCollector()
        self._validator = DataValidator()
        self._kpi_extractor = KPIExtractor()
        self._ratios_calculator = RatiosCalculator()
        self._competitor_analyzer = CompetitorAnalyzer()
        self._sentiment_analyzer = SentimentAnalyzer()
        self._risk_detector = RiskDetector()
        self._granite_ai = GraniteAI()
        self._recommendation_engine = RecommendationEngine()

    # ──────────────────────────────────────────────
    # MAIN ENTRY POINT
    # ──────────────────────────────────────────────

    def analyze(self, ticker: str) -> AnalysisResult:
        ticker = ticker.upper().strip()
        logger.info("=" * 60)
        logger.info("Starting Investment Analysis Workflow for: %s", ticker)
        logger.info("=" * 60)

        result = AnalysisResult(
            ticker=ticker,
            steps=[WorkflowStep(name=s) for s in WORKFLOW_STEPS],
            workflow_started_at=datetime.utcnow().isoformat(),
        )
        t0 = time.time()

        # ── Step 1: Data Collection ──────────────────────────────
        raw_data = self._run_step(result, "data_collection", self._collector.collect_all, ticker)
        if raw_data:
            result.raw_data = raw_data

        # ── Step 2: Data Validation ──────────────────────────────
        validated = self._run_step(result, "data_validation", self._validator.validate_and_clean, raw_data or {})
        if validated:
            result.validated_data = validated

        # ── Step 3: KPI Extraction ───────────────────────────────
        kpis = self._run_step(result, "kpi_extraction", self._kpi_extractor.extract, validated or {})
        if kpis:
            result.kpis = kpis

        # ── Step 4: Ratio Calculation ────────────────────────────
        ratios = self._run_step(result, "ratio_calculation", self._ratios_calculator.calculate, kpis or {})
        if ratios:
            result.ratios = ratios

        # ── Step 5: Competitor Analysis ──────────────────────────
        competitor = self._run_step(
            result, "competitor_analysis",
            self._competitor_analyzer.analyze, ticker, kpis or {}
        )
        if competitor:
            result.competitor_analysis = competitor

        # ── Step 6: Sentiment Analysis ───────────────────────────
        news = (validated or {}).get("news", [])
        sentiment = self._run_step(result, "sentiment_analysis", self._sentiment_analyzer.analyze, news, ticker)
        if sentiment:
            result.sentiment = sentiment

        # ── Step 7: Risk Detection ───────────────────────────────
        risk = self._run_step(
            result, "risk_detection",
            self._risk_detector.detect, kpis or {}, ratios or {}, sentiment or {}
        )
        if risk:
            result.risk = risk

        # ── Step 8: AI Analysis (Granite) ────────────────────────
        ai_analysis = self._run_step(
            result, "ai_analysis",
            self._granite_ai.generate_analysis,
            kpis or {}, ratios or {}, sentiment or {}, risk or {}, competitor or {}
        )
        if ai_analysis:
            result.ai_analysis = ai_analysis

        # ── Step 9: Growth Predictions (Granite) ─────────────────
        growth = self._run_step(result, "growth_predictions", self._granite_ai.generate_growth_predictions, kpis or {})
        if growth:
            result.growth_predictions = growth
            # Attach growth text to ai_analysis for the recommendation engine
            if result.ai_analysis:
                result.ai_analysis["growth_predictions_text"] = growth.get("growth_predictions_text", "")

        # ── Step 10: Final Recommendation ────────────────────────
        recommendation = self._run_step(
            result, "recommendation_generation",
            self._recommendation_engine.generate,
            kpis or {}, ratios or {}, sentiment or {}, risk or {},
            competitor or {}, ai_analysis or {}
        )
        if recommendation:
            result.recommendation = recommendation

        # ── Finalise ─────────────────────────────────────────────
        result.workflow_completed_at = datetime.utcnow().isoformat()
        result.total_duration_seconds = round(time.time() - t0, 2)
        result.success = len(result.errors) == 0

        logger.info(
            "Workflow complete for %s in %.1fs — %s",
            ticker,
            result.total_duration_seconds,
            result.recommendation.get("final_recommendation", "N/A"),
        )
        return result

    def to_dict(self, result: AnalysisResult) -> dict[str, Any]:
        """Serialize AnalysisResult to a plain dict for API/JSON output."""
        return {
            "ticker": result.ticker,
            "workflow_started_at": result.workflow_started_at,
            "workflow_completed_at": result.workflow_completed_at,
            "total_duration_seconds": result.total_duration_seconds,
            "success": result.success,
            "errors": result.errors,
            "steps": [
                {
                    "name": s.name,
                    "status": s.status,
                    "duration_seconds": s.duration_seconds,
                    "error": s.error,
                }
                for s in result.steps
            ],
            "kpis": result.kpis,
            "ratios": result.ratios,
            "competitor_analysis": result.competitor_analysis,
            "sentiment": result.sentiment,
            "risk": result.risk,
            "ai_analysis": result.ai_analysis,
            "growth_predictions": result.growth_predictions,
            "recommendation": result.recommendation,
        }

    # ──────────────────────────────────────────────
    # STEP RUNNER
    # ──────────────────────────────────────────────

    def _run_step(self, result: AnalysisResult, step_name: str, fn, *args) -> Any:
        step = next((s for s in result.steps if s.name == step_name), None)
        if step is None:
            logger.warning("Unknown step: %s", step_name)
            return None

        step.status = "running"
        step.started_at = datetime.utcnow().isoformat()
        t0 = time.time()
        logger.info("[%s] Starting...", step_name)

        try:
            output = fn(*args)
            step.status = "completed"
            step.duration_seconds = round(time.time() - t0, 2)
            step.completed_at = datetime.utcnow().isoformat()
            logger.info("[%s] Completed in %.2fs", step_name, step.duration_seconds)
            return output
        except Exception as exc:
            step.status = "failed"
            step.error = str(exc)
            step.duration_seconds = round(time.time() - t0, 2)
            step.completed_at = datetime.utcnow().isoformat()
            result.errors.append(f"{step_name}: {exc}")
            logger.error("[%s] Failed: %s", step_name, exc, exc_info=True)
            return None

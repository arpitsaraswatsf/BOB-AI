"""
Competitor Analysis module.
Fetches and compares KPIs across the target company and its top peers.
"""

import logging
from typing import Any

from config.settings import COMPETITOR_MAP
from src.data.collector import DataCollector
from src.data.validator import DataValidator
from src.analysis.kpi_extractor import KPIExtractor

logger = logging.getLogger(__name__)

_COMPARISON_METRICS = [
    "pe_ratio",
    "forward_pe",
    "peg_ratio",
    "price_to_book",
    "ev_to_ebitda",
    "roe",
    "roa",
    "profit_margin",
    "gross_margin",
    "revenue_growth",
    "earnings_growth",
    "current_ratio",
    "debt_to_equity",
    "free_cash_flow",
    "market_cap",
    "beta",
    "dividend_yield",
]


class CompetitorAnalyzer:
    """Compares the target company against peers on key financial metrics."""

    def __init__(self):
        self._collector = DataCollector()
        self._validator = DataValidator()
        self._kpi_extractor = KPIExtractor()

    def analyze(self, target_ticker: str, target_kpis: dict[str, Any]) -> dict[str, Any]:
        ticker = target_ticker.upper()
        peers = COMPETITOR_MAP.get(ticker, [])

        if not peers:
            logger.info("No predefined peers for %s — using analyst peers if available", ticker)

        logger.info("Competitor analysis for %s vs peers: %s", ticker, peers)

        peer_kpis: list[dict] = []
        for peer in peers[:4]:  # limit to 4 peers to control latency
            try:
                raw = self._collector.collect_all(peer)
                clean = self._validator.validate_and_clean(raw)
                kpis = self._kpi_extractor.extract(clean)
                peer_kpis.append(kpis)
                logger.info("Collected peer data: %s", peer)
            except Exception as exc:
                logger.warning("Failed to collect peer %s: %s", peer, exc)

        all_kpis = [target_kpis] + peer_kpis
        comparison_table = self._build_comparison_table(all_kpis)
        rankings = self._rank_companies(all_kpis)
        sector_averages = self._compute_sector_averages(all_kpis)
        target_vs_sector = self._vs_sector(target_kpis, sector_averages)

        return {
            "target_ticker": ticker,
            "peers": [k.get("ticker") for k in peer_kpis],
            "comparison_table": comparison_table,
            "rankings": rankings,
            "sector_averages": sector_averages,
            "target_vs_sector": target_vs_sector,
            "peer_count": len(peer_kpis),
        }

    # ──────────────────────────────────────────────
    # TABLE BUILDER
    # ──────────────────────────────────────────────

    def _build_comparison_table(self, all_kpis: list[dict]) -> list[dict]:
        rows = []
        for kpis in all_kpis:
            row: dict[str, Any] = {"ticker": kpis.get("ticker"), "company": kpis.get("company_name", "")}
            for metric in _COMPARISON_METRICS:
                row[metric] = kpis.get(metric)
            rows.append(row)
        return rows

    def _rank_companies(self, all_kpis: list[dict]) -> dict[str, list[str]]:
        """Returns dict of metric → list of tickers sorted best→worst."""
        rankings: dict[str, list[str]] = {}

        higher_is_better = {
            "roe", "roa", "profit_margin", "gross_margin",
            "revenue_growth", "earnings_growth", "current_ratio",
            "free_cash_flow", "market_cap", "dividend_yield",
        }
        lower_is_better = {
            "pe_ratio", "forward_pe", "peg_ratio", "price_to_book",
            "ev_to_ebitda", "debt_to_equity", "beta",
        }

        for metric in _COMPARISON_METRICS:
            entries = [(k.get("ticker"), k.get(metric)) for k in all_kpis]
            entries = [(t, v) for t, v in entries if v is not None]

            if metric in higher_is_better:
                entries.sort(key=lambda x: x[1], reverse=True)
            elif metric in lower_is_better:
                entries.sort(key=lambda x: abs(x[1]))
            else:
                entries.sort(key=lambda x: x[1], reverse=True)

            rankings[metric] = [t for t, _ in entries]

        return rankings

    def _compute_sector_averages(self, all_kpis: list[dict]) -> dict[str, float | None]:
        averages: dict[str, float | None] = {}
        for metric in _COMPARISON_METRICS:
            values = [k.get(metric) for k in all_kpis if k.get(metric) is not None]
            averages[metric] = round(sum(values) / len(values), 4) if values else None
        return averages

    def _vs_sector(self, target: dict, averages: dict) -> dict[str, dict]:
        result = {}
        for metric, avg in averages.items():
            target_val = target.get(metric)
            if avg is not None and target_val is not None:
                diff = target_val - avg
                result[metric] = {
                    "target": target_val,
                    "sector_avg": avg,
                    "diff": round(diff, 4),
                    "above_avg": diff > 0,
                }
        return result

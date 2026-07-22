"""
Financial Ratios Calculator.
Computes derived ratios and scores from extracted KPIs.
"""

import logging
import math
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    return a / b


class RatiosCalculator:
    """Calculates comprehensive financial ratios and composite scores."""

    def calculate(self, kpis: dict[str, Any]) -> dict[str, Any]:
        ticker = kpis.get("ticker", "UNKNOWN")
        logger.info("Calculating financial ratios for %s", ticker)

        ratios: dict[str, Any] = {"ticker": ticker}

        # ── Profitability ────────────────────────────────────────
        ratios["gross_margin_pct"] = self._pct(kpis.get("gross_margin"))
        ratios["operating_margin_pct"] = self._pct(kpis.get("operating_margin"))
        ratios["net_profit_margin_pct"] = self._pct(kpis.get("profit_margin"))
        ratios["ebitda_margin_pct"] = self._pct(kpis.get("ebitda_margin"))
        ratios["roe_pct"] = self._pct(kpis.get("roe"))
        ratios["roa_pct"] = self._pct(kpis.get("roa"))

        # ── Valuation ────────────────────────────────────────────
        ratios["pe_ratio"] = kpis.get("pe_ratio")
        ratios["forward_pe"] = kpis.get("forward_pe")
        ratios["peg_ratio"] = kpis.get("peg_ratio")
        ratios["price_to_book"] = kpis.get("price_to_book")
        ratios["price_to_sales"] = kpis.get("price_to_sales")
        ratios["ev_to_ebitda"] = kpis.get("ev_to_ebitda")
        ratios["ev_to_revenue"] = kpis.get("ev_to_revenue")

        # ── Earnings yield (inverse P/E) ──────────────────────────
        ratios["earnings_yield_pct"] = self._pct(_div(1.0, kpis.get("pe_ratio"))) if kpis.get("pe_ratio") else None

        # ── Liquidity ────────────────────────────────────────────
        ratios["current_ratio"] = kpis.get("current_ratio")
        ratios["quick_ratio"] = kpis.get("quick_ratio")
        ratios["cash_ratio"] = _div(kpis.get("total_cash"), self._current_liabilities(kpis))

        # ── Leverage ─────────────────────────────────────────────
        ratios["debt_to_equity"] = kpis.get("debt_to_equity")
        ratios["debt_to_assets"] = _div(kpis.get("total_debt"), kpis.get("total_assets"))
        ratios["net_debt"] = self._net_debt(kpis)
        ratios["interest_coverage"] = self._interest_coverage(kpis)

        # ── Efficiency ───────────────────────────────────────────
        ratios["asset_turnover"] = _div(kpis.get("revenue_ttm"), kpis.get("total_assets"))
        ratios["revenue_per_employee"] = _div(kpis.get("revenue_ttm"), kpis.get("employees"))

        # ── Cash flow quality ────────────────────────────────────
        ratios["fcf_yield_pct"] = self._fcf_yield(kpis)
        ratios["fcf_to_net_income"] = _div(kpis.get("free_cash_flow"), kpis.get("net_income"))
        ratios["capex_to_revenue"] = self._capex_ratio(kpis)

        # ── Growth proxies ───────────────────────────────────────
        ratios["revenue_growth_pct"] = self._pct(kpis.get("revenue_growth"))
        ratios["earnings_growth_pct"] = self._pct(kpis.get("earnings_growth"))

        # ── Short interest ───────────────────────────────────────
        ratios["short_interest_pct"] = self._pct(kpis.get("short_percent_of_float"))

        # ── Composite scores ─────────────────────────────────────
        ratios["value_score"] = self._value_score(kpis)
        ratios["quality_score"] = self._quality_score(kpis)
        ratios["growth_score"] = self._growth_score(kpis)
        ratios["safety_score"] = self._safety_score(kpis)
        ratios["overall_financial_score"] = self._overall_score(ratios)

        logger.info("Ratio calculation complete for %s", ticker)
        return ratios

    # ──────────────────────────────────────────────
    # COMPOSITE SCORING (0-100)
    # ──────────────────────────────────────────────

    def _value_score(self, k: dict) -> float:
        score = 50.0
        pe = k.get("pe_ratio")
        pb = k.get("price_to_book")
        ps = k.get("price_to_sales")
        peg = k.get("peg_ratio")
        ev_ebitda = k.get("ev_to_ebitda")

        if pe is not None:
            if pe < 15: score += 15
            elif pe < 25: score += 8
            elif pe > 40: score -= 15
            elif pe > 30: score -= 8

        if pb is not None:
            if pb < 1.5: score += 10
            elif pb < 3: score += 5
            elif pb > 8: score -= 10

        if peg is not None:
            if peg < 1: score += 10
            elif peg < 2: score += 5
            elif peg > 3: score -= 10

        if ev_ebitda is not None:
            if ev_ebitda < 10: score += 10
            elif ev_ebitda < 20: score += 5
            elif ev_ebitda > 30: score -= 10

        return max(0.0, min(100.0, score))

    def _quality_score(self, k: dict) -> float:
        score = 50.0
        roe = k.get("roe")
        roa = k.get("roa")
        margin = k.get("profit_margin")
        gm = k.get("gross_margin")

        if roe is not None:
            if roe > 0.25: score += 15
            elif roe > 0.15: score += 8
            elif roe < 0.05: score -= 10
            elif roe < 0: score -= 20

        if roa is not None:
            if roa > 0.10: score += 10
            elif roa > 0.05: score += 5
            elif roa < 0.01: score -= 8

        if margin is not None:
            if margin > 0.20: score += 10
            elif margin > 0.10: score += 5
            elif margin < 0.03: score -= 10
            elif margin < 0: score -= 20

        if gm is not None:
            if gm > 0.50: score += 10
            elif gm > 0.30: score += 5
            elif gm < 0.15: score -= 8

        return max(0.0, min(100.0, score))

    def _growth_score(self, k: dict) -> float:
        score = 50.0
        rev_growth = k.get("revenue_growth")
        earn_growth = k.get("earnings_growth")
        fcf = k.get("free_cash_flow")

        if rev_growth is not None:
            if rev_growth > 0.25: score += 20
            elif rev_growth > 0.10: score += 12
            elif rev_growth > 0.05: score += 6
            elif rev_growth < -0.05: score -= 15
            elif rev_growth < 0: score -= 8

        if earn_growth is not None:
            if earn_growth > 0.25: score += 15
            elif earn_growth > 0.10: score += 8
            elif earn_growth < -0.10: score -= 15
            elif earn_growth < 0: score -= 8

        if fcf is not None and fcf > 0:
            score += 5

        return max(0.0, min(100.0, score))

    def _safety_score(self, k: dict) -> float:
        score = 50.0
        cr = k.get("current_ratio")
        de = k.get("debt_to_equity")
        beta = k.get("beta")
        short_pct = k.get("short_percent_of_float")

        if cr is not None:
            if cr > 2.0: score += 15
            elif cr > 1.5: score += 8
            elif cr < 1.0: score -= 15
            elif cr < 0.8: score -= 25

        if de is not None:
            # Yahoo Finance reports D/E as decimal (e.g. 1.5) or sometimes as %
            de_norm = de / 100 if de > 20 else de
            if de_norm < 0.5: score += 15
            elif de_norm < 1.0: score += 8
            elif de_norm > 2.0: score -= 15
            elif de_norm > 3.0: score -= 25

        if beta is not None:
            if beta < 0.8: score += 10
            elif beta < 1.2: score += 5
            elif beta > 2.0: score -= 15
            elif beta > 1.5: score -= 8

        if short_pct is not None:
            if short_pct > 0.20: score -= 15
            elif short_pct > 0.10: score -= 8

        return max(0.0, min(100.0, score))

    def _overall_score(self, ratios: dict) -> float:
        scores = [
            ratios.get("value_score"),
            ratios.get("quality_score"),
            ratios.get("growth_score"),
            ratios.get("safety_score"),
        ]
        valid = [s for s in scores if s is not None]
        if not valid:
            return 50.0
        weights = [0.25, 0.30, 0.25, 0.20]
        total = sum(s * w for s, w in zip(valid, weights[:len(valid)]))
        total_weight = sum(weights[:len(valid)])
        return round(total / total_weight, 1)

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    @staticmethod
    def _pct(v: Optional[float]) -> Optional[float]:
        if v is None:
            return None
        return round(v * 100, 2) if abs(v) < 100 else round(v, 2)

    @staticmethod
    def _net_debt(k: dict) -> Optional[float]:
        debt = k.get("total_debt")
        cash = k.get("total_cash")
        if debt is not None and cash is not None:
            return debt - cash
        return None

    @staticmethod
    def _current_liabilities(k: dict) -> Optional[float]:
        assets = k.get("total_assets")
        cr = k.get("current_ratio")
        total_cash = k.get("total_cash")
        # Approximate: we don't have current liabilities directly from yfinance info
        # Use cash / quick_ratio as a proxy when available
        qr = k.get("quick_ratio")
        if total_cash and qr and qr != 0:
            return total_cash / qr
        return None

    @staticmethod
    def _interest_coverage(k: dict) -> Optional[float]:
        ebitda = k.get("ebitda")
        debt = k.get("total_debt")
        if ebitda and debt and debt > 0:
            # Rough approximation: assume 5% avg interest rate on debt
            interest_est = debt * 0.05
            return ebitda / interest_est
        return None

    @staticmethod
    def _fcf_yield(k: dict) -> Optional[float]:
        fcf = k.get("free_cash_flow")
        mc = k.get("market_cap")
        if fcf and mc and mc != 0:
            return round((fcf / mc) * 100, 2)
        return None

    @staticmethod
    def _capex_ratio(k: dict) -> Optional[float]:
        fcf = k.get("free_cash_flow")
        ocf = k.get("operating_cash_flow")
        rev = k.get("revenue_ttm")
        if ocf and fcf and rev and rev != 0:
            capex = ocf - fcf
            return round(capex / rev, 4)
        return None

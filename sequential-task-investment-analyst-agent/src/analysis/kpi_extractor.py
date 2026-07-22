"""
KPI Extraction module.
Extracts standardized financial KPIs from cleaned multi-source data.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _safe_float(value: Any, scale: float = 1.0) -> Optional[float]:
    try:
        return float(value) * scale if value is not None else None
    except (TypeError, ValueError):
        return None


class KPIExtractor:
    """Extracts key performance indicators from validated financial data."""

    def extract(self, data: dict[str, Any]) -> dict[str, Any]:
        ticker = data.get("ticker", "UNKNOWN")
        logger.info("Extracting KPIs for %s", ticker)

        info = data.get("yfinance", {}).get("info", {})
        av_overview = data.get("alpha_vantage", {}).get("overview", {})
        finnhub_metrics = data.get("finnhub", {}).get("metrics", {}).get("metric", {})

        kpis = {
            "ticker": ticker,

            # ── Valuation ───────────────────────────────────────
            "market_cap": _safe_float(info.get("marketCap")),
            "enterprise_value": _safe_float(info.get("enterpriseValue")),
            "current_price": _safe_float(info.get("currentPrice") or info.get("regularMarketPrice")),
            "52w_high": _safe_float(info.get("fiftyTwoWeekHigh")),
            "52w_low": _safe_float(info.get("fiftyTwoWeekLow")),
            "beta": _safe_float(info.get("beta")),

            # ── Income ──────────────────────────────────────────
            "revenue_ttm": _safe_float(info.get("totalRevenue")),
            "revenue_growth": _safe_float(info.get("revenueGrowth")),
            "gross_profit": _safe_float(info.get("grossProfits")),
            "ebitda": _safe_float(info.get("ebitda")),
            "net_income": _safe_float(info.get("netIncomeToCommon")),
            "eps_ttm": _safe_float(info.get("trailingEps")),
            "eps_forward": _safe_float(info.get("forwardEps")),
            "earnings_growth": _safe_float(info.get("earningsGrowth")),

            # ── Margins ─────────────────────────────────────────
            "gross_margin": _safe_float(info.get("grossMargins")),
            "operating_margin": _safe_float(info.get("operatingMargins")),
            "profit_margin": _safe_float(info.get("profitMargins")),
            "ebitda_margin": self._calc_ebitda_margin(info),

            # ── Profitability ratios ─────────────────────────────
            "roe": _safe_float(info.get("returnOnEquity")),
            "roa": _safe_float(info.get("returnOnAssets")),

            # ── Valuation multiples ──────────────────────────────
            "pe_ratio": _safe_float(info.get("trailingPE")),
            "forward_pe": _safe_float(info.get("forwardPE")),
            "peg_ratio": _safe_float(info.get("pegRatio")),
            "price_to_book": _safe_float(info.get("priceToBook")),
            "price_to_sales": _safe_float(info.get("priceToSalesTrailing12Months")),
            "ev_to_ebitda": _safe_float(info.get("enterpriseToEbitda")),
            "ev_to_revenue": _safe_float(info.get("enterpriseToRevenue")),

            # ── Balance sheet ────────────────────────────────────
            "total_assets": _safe_float(info.get("totalAssets")),
            "total_debt": _safe_float(info.get("totalDebt")),
            "total_cash": _safe_float(info.get("totalCash")),
            "book_value_per_share": _safe_float(info.get("bookValue")),
            "cash_per_share": _safe_float(info.get("totalCashPerShare")),

            # ── Cash flow ────────────────────────────────────────
            "operating_cash_flow": _safe_float(info.get("operatingCashflow")),
            "free_cash_flow": _safe_float(info.get("freeCashflow")),
            "fcf_per_share": self._calc_fcf_per_share(info),

            # ── Liquidity ────────────────────────────────────────
            "current_ratio": _safe_float(info.get("currentRatio")),
            "quick_ratio": _safe_float(info.get("quickRatio")),

            # ── Leverage ─────────────────────────────────────────
            "debt_to_equity": _safe_float(info.get("debtToEquity")),

            # ── Dividends ────────────────────────────────────────
            "dividend_yield": _safe_float(info.get("dividendYield")),
            "dividend_rate": _safe_float(info.get("dividendRate")),
            "payout_ratio": _safe_float(info.get("payoutRatio")),

            # ── Analyst coverage ─────────────────────────────────
            "analyst_target_price": _safe_float(info.get("targetMeanPrice")),
            "analyst_high_price": _safe_float(info.get("targetHighPrice")),
            "analyst_low_price": _safe_float(info.get("targetLowPrice")),
            "analyst_recommendation": info.get("recommendationKey", ""),
            "number_of_analyst_opinions": info.get("numberOfAnalystOpinions"),

            # ── Shares ───────────────────────────────────────────
            "shares_outstanding": _safe_float(info.get("sharesOutstanding")),
            "float_shares": _safe_float(info.get("floatShares")),
            "shares_short": _safe_float(info.get("sharesShort")),
            "short_ratio": _safe_float(info.get("shortRatio")),
            "short_percent_of_float": _safe_float(info.get("shortPercentOfFloat")),

            # ── Company meta ─────────────────────────────────────
            "company_name": info.get("shortName") or info.get("longName", ""),
            "sector": info.get("sector", ""),
            "industry": info.get("industry", ""),
            "country": info.get("country", ""),
            "employees": info.get("fullTimeEmployees"),
            "description": info.get("longBusinessSummary", ""),
        }

        # Supplement with Alpha Vantage if yfinance fields are missing
        kpis = self._supplement_from_av(kpis, av_overview)

        # Supplement with Finnhub metrics
        kpis = self._supplement_from_finnhub(kpis, finnhub_metrics)

        # Derive any still-missing calculated fields
        kpis = self._derive_calculated_fields(kpis)

        logger.info("KPI extraction complete for %s — %d fields", ticker, sum(1 for v in kpis.values() if v is not None))
        return kpis

    # ──────────────────────────────────────────────
    # SUPPLEMENTS
    # ──────────────────────────────────────────────

    def _supplement_from_av(self, kpis: dict, av: dict) -> dict:
        mapping = {
            "market_cap": "MarketCapitalization",
            "pe_ratio": "PERatio",
            "peg_ratio": "PEGRatio",
            "book_value_per_share": "BookValue",
            "dividend_yield": "DividendYield",
            "eps_ttm": "EPS",
            "roe": "ReturnOnEquityTTM",
            "roa": "ReturnOnAssetsTTM",
            "profit_margin": "ProfitMargin",
            "operating_margin": "OperatingMarginTTM",
            "revenue_ttm": "RevenueTTM",
            "gross_profit": "GrossProfitTTM",
            "ebitda": "EBITDA",
            "analyst_target_price": "AnalystTargetPrice",
            "beta": "Beta",
            "52w_high": "52WeekHigh",
            "52w_low": "52WeekLow",
        }
        for kpi_key, av_key in mapping.items():
            if kpis.get(kpi_key) is None and av.get(av_key) not in (None, "None", "-"):
                kpis[kpi_key] = _safe_float(av.get(av_key))
        return kpis

    def _supplement_from_finnhub(self, kpis: dict, fh: dict) -> dict:
        mapping = {
            "pe_ratio": "peNormalizedAnnual",
            "roa": "roaRfy",
            "roe": "roeRfy",
            "debt_to_equity": "totalDebt/totalEquityAnnual",
            "current_ratio": "currentRatioAnnual",
            "quick_ratio": "quickRatioAnnual",
            "profit_margin": "netProfitMarginAnnual",
            "gross_margin": "grossMarginAnnual",
        }
        for kpi_key, fh_key in mapping.items():
            if kpis.get(kpi_key) is None and fh.get(fh_key) is not None:
                kpis[kpi_key] = _safe_float(fh.get(fh_key))
        return kpis

    def _derive_calculated_fields(self, kpis: dict) -> dict:
        # EBITDA margin
        if kpis.get("ebitda_margin") is None and kpis.get("ebitda") and kpis.get("revenue_ttm"):
            rev = kpis["revenue_ttm"]
            if rev and rev != 0:
                kpis["ebitda_margin"] = kpis["ebitda"] / rev

        # FCF per share
        if kpis.get("fcf_per_share") is None and kpis.get("free_cash_flow") and kpis.get("shares_outstanding"):
            shares = kpis["shares_outstanding"]
            if shares and shares != 0:
                kpis["fcf_per_share"] = kpis["free_cash_flow"] / shares

        return kpis

    # ──────────────────────────────────────────────
    # CALCULATED HELPERS
    # ──────────────────────────────────────────────

    @staticmethod
    def _calc_ebitda_margin(info: dict) -> Optional[float]:
        ebitda = _safe_float(info.get("ebitda"))
        revenue = _safe_float(info.get("totalRevenue"))
        if ebitda and revenue and revenue != 0:
            return ebitda / revenue
        return None

    @staticmethod
    def _calc_fcf_per_share(info: dict) -> Optional[float]:
        fcf = _safe_float(info.get("freeCashflow"))
        shares = _safe_float(info.get("sharesOutstanding"))
        if fcf and shares and shares != 0:
            return fcf / shares
        return None

"""
Data collection module — fetches financial data from multiple trusted sources.
Sources: Yahoo Finance (yfinance), Alpha Vantage, SEC EDGAR, Finnhub, NewsAPI.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Optional

import requests
import yfinance as yf

from config.settings import datasource_cfg, app_cfg

logger = logging.getLogger(__name__)


class DataCollector:
    """Orchestrates data retrieval from all external data sources."""

    def __init__(self):
        self.av_key = datasource_cfg.alpha_vantage_key
        self.newsapi_key = datasource_cfg.newsapi_key
        self.finnhub_key = datasource_cfg.finnhub_key
        self.sec_agent = datasource_cfg.sec_user_agent
        self.timeout = app_cfg.request_timeout
        self.max_retries = app_cfg.max_retries
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": self.sec_agent})

    # ──────────────────────────────────────────────
    # PUBLIC ENTRY POINT
    # ──────────────────────────────────────────────

    def collect_all(self, ticker: str) -> dict[str, Any]:
        """Collect all available data for a given ticker symbol."""
        ticker = ticker.upper().strip()
        logger.info("Starting data collection for %s", ticker)

        result: dict[str, Any] = {
            "ticker": ticker,
            "collected_at": datetime.utcnow().isoformat(),
            "yfinance": {},
            "alpha_vantage": {},
            "sec_filings": {},
            "news": [],
            "finnhub": {},
            "errors": [],
        }

        self._safe_collect(result, "yfinance", self._collect_yfinance, ticker)
        self._safe_collect(result, "alpha_vantage", self._collect_alpha_vantage, ticker)
        self._safe_collect(result, "sec_filings", self._collect_sec_filings, ticker)
        self._safe_collect(result, "news", self._collect_news, ticker)
        self._safe_collect(result, "finnhub", self._collect_finnhub, ticker)

        logger.info("Data collection complete for %s — errors: %d", ticker, len(result["errors"]))
        return result

    # ──────────────────────────────────────────────
    # YFINANCE (primary — broad coverage, free)
    # ──────────────────────────────────────────────

    def _collect_yfinance(self, ticker: str) -> dict[str, Any]:
        stock = yf.Ticker(ticker)
        info = stock.info or {}

        financials = {}
        try:
            financials["income_stmt"] = stock.financials.to_dict() if stock.financials is not None else {}
            financials["balance_sheet"] = stock.balance_sheet.to_dict() if stock.balance_sheet is not None else {}
            financials["cash_flow"] = stock.cashflow.to_dict() if stock.cashflow is not None else {}
            financials["quarterly_financials"] = stock.quarterly_financials.to_dict() if stock.quarterly_financials is not None else {}
        except Exception as exc:
            logger.warning("yfinance financials partial error for %s: %s", ticker, exc)

        history = {}
        try:
            hist = stock.history(period="1y")
            history = {
                "close": hist["Close"].tolist() if not hist.empty else [],
                "volume": hist["Volume"].tolist() if not hist.empty else [],
                "dates": [d.isoformat() for d in hist.index],
            }
        except Exception as exc:
            logger.warning("yfinance history partial error for %s: %s", ticker, exc)

        recommendations = []
        try:
            rec = stock.recommendations
            if rec is not None and not rec.empty:
                recommendations = rec.tail(10).to_dict(orient="records")
        except Exception as exc:
            logger.warning("yfinance recommendations partial error for %s: %s", ticker, exc)

        return {
            "info": info,
            "financials": financials,
            "history": history,
            "analyst_recommendations": recommendations,
        }

    # ──────────────────────────────────────────────
    # ALPHA VANTAGE (fundamental + technical)
    # ──────────────────────────────────────────────

    def _collect_alpha_vantage(self, ticker: str) -> dict[str, Any]:
        base = "https://www.alphavantage.co/query"
        result: dict[str, Any] = {}

        endpoints = {
            "overview": {"function": "OVERVIEW", "symbol": ticker},
            "income_statement": {"function": "INCOME_STATEMENT", "symbol": ticker},
            "balance_sheet": {"function": "BALANCE_SHEET", "symbol": ticker},
            "cash_flow": {"function": "CASH_FLOW", "symbol": ticker},
            "earnings": {"function": "EARNINGS", "symbol": ticker},
        }

        for key, params in endpoints.items():
            params["apikey"] = self.av_key
            data = self._get_json(base, params)
            if data:
                result[key] = data

        return result

    # ──────────────────────────────────────────────
    # SEC EDGAR (regulatory filings)
    # ──────────────────────────────────────────────

    def _collect_sec_filings(self, ticker: str) -> dict[str, Any]:
        # Resolve CIK from ticker
        cik = self._resolve_sec_cik(ticker)
        if not cik:
            return {"error": f"CIK not found for {ticker}"}

        filings_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        filings_data = self._get_json(filings_url)
        if not filings_data:
            return {"error": "Could not fetch SEC filings"}

        recent = filings_data.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        dates = recent.get("filingDate", [])
        accessions = recent.get("accessionNumber", [])

        # Return last 5 10-K and 10-Q
        important = []
        for form, date, acc in zip(forms, dates, accessions):
            if form in ("10-K", "10-Q") and len(important) < 10:
                important.append({"form": form, "date": date, "accession": acc})

        return {
            "cik": cik,
            "company_name": filings_data.get("name", ""),
            "sic": filings_data.get("sic", ""),
            "recent_filings": important,
        }

    def _resolve_sec_cik(self, ticker: str) -> Optional[int]:
        url = "https://efts.sec.gov/LATEST/search-index?q=%22{}%22&dateRange=custom&startdt=2020-01-01&forms=10-K".format(ticker)
        # Use the company_tickers JSON as a reliable lookup
        try:
            resp = self._session.get(
                "https://www.sec.gov/files/company_tickers.json",
                timeout=self.timeout,
            )
            if resp.status_code == 200:
                data = resp.json()
                for entry in data.values():
                    if entry.get("ticker", "").upper() == ticker.upper():
                        return entry["cik_str"]
        except Exception as exc:
            logger.warning("SEC CIK lookup failed: %s", exc)
        return None

    # ──────────────────────────────────────────────
    # NEWS API (market news & sentiment)
    # ──────────────────────────────────────────────

    def _collect_news(self, ticker: str) -> list[dict]:
        if not self.newsapi_key:
            logger.info("NewsAPI key not set — skipping news collection")
            return []

        from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "q": ticker,
            "from": from_date,
            "sortBy": "relevancy",
            "pageSize": 20,
            "language": "en",
            "apiKey": self.newsapi_key,
        }
        data = self._get_json("https://newsapi.org/v2/everything", params)
        articles = data.get("articles", []) if data else []
        return [
            {
                "title": a.get("title", ""),
                "source": a.get("source", {}).get("name", ""),
                "published_at": a.get("publishedAt", ""),
                "description": a.get("description", ""),
                "url": a.get("url", ""),
            }
            for a in articles
        ]

    # ──────────────────────────────────────────────
    # FINNHUB (analyst metrics + earnings)
    # ──────────────────────────────────────────────

    def _collect_finnhub(self, ticker: str) -> dict[str, Any]:
        if not self.finnhub_key:
            logger.info("Finnhub key not set — skipping")
            return {}

        base = "https://finnhub.io/api/v1"
        headers = {"X-Finnhub-Token": self.finnhub_key}
        result: dict[str, Any] = {}

        endpoints = {
            "profile": f"{base}/stock/profile2?symbol={ticker}",
            "metrics": f"{base}/stock/metric?symbol={ticker}&metric=all",
            "peers": f"{base}/stock/peers?symbol={ticker}",
            "sentiment": f"{base}/news-sentiment?symbol={ticker}",
            "earnings_calendar": f"{base}/calendar/earnings?symbol={ticker}",
        }

        for key, url in endpoints.items():
            try:
                resp = self._session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code == 200:
                    result[key] = resp.json()
            except Exception as exc:
                logger.warning("Finnhub %s error: %s", key, exc)

        return result

    # ──────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────

    def _safe_collect(self, result: dict, key: str, fn, *args):
        try:
            result[key] = fn(*args)
        except Exception as exc:
            logger.error("Collection error [%s]: %s", key, exc, exc_info=True)
            result["errors"].append({"source": key, "error": str(exc)})

    def _get_json(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self._session.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning("Rate limited on %s — waiting %ds", url, wait)
                    time.sleep(wait)
                else:
                    logger.warning("HTTP error for %s: %s", url, exc)
                    break
            except Exception as exc:
                logger.warning("Request error [attempt %d] %s: %s", attempt, url, exc)
                time.sleep(1)
        return None

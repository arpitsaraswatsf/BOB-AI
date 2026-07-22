"""
IBM Granite AI Integration module.
Calls IBM watsonx.ai Granite models for predictions, insights, and recommendations.
"""

import json
import logging
from typing import Any, Optional

import requests

from config.settings import watsonx_cfg, app_cfg

logger = logging.getLogger(__name__)

_IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"

# Prompt templates
_ANALYSIS_PROMPT_TEMPLATE = """You are a senior investment analyst at a top-tier investment bank.

## Company Overview
Ticker: {ticker}
Company: {company_name}
Sector: {sector}
Industry: {industry}

## Key Financial KPIs
- Revenue (TTM): ${revenue_ttm}
- Revenue Growth: {revenue_growth}%
- Net Income: ${net_income}
- EPS (TTM): ${eps_ttm}
- Gross Margin: {gross_margin}%
- Net Profit Margin: {profit_margin}%
- ROE: {roe}%
- ROA: {roa}%
- P/E Ratio: {pe_ratio}
- Forward P/E: {forward_pe}
- EV/EBITDA: {ev_to_ebitda}
- Debt-to-Equity: {debt_to_equity}
- Current Ratio: {current_ratio}
- Free Cash Flow: ${free_cash_flow}

## Financial Scores (0-100)
- Value Score: {value_score}/100
- Quality Score: {quality_score}/100
- Growth Score: {growth_score}/100
- Safety Score: {safety_score}/100
- Overall Financial Score: {overall_score}/100

## Market Sentiment
- Sentiment Score: {sentiment_score}/100
- Overall Sentiment: {sentiment_label}

## Risk Assessment
- Risk Score: {risk_score}/100
- Risk Level: {risk_level}
- Key Risk Factors: {risk_factors}

## Competitor Comparison
{competitor_summary}

Based on the above data, provide:
1. **Business Quality Assessment** (2-3 sentences on competitive moat and business model strength)
2. **Financial Health Summary** (2-3 sentences on balance sheet, margins, and cash flow)
3. **Growth Outlook** (2-3 sentences on growth drivers and sustainability)
4. **Key Risks** (bullet list of top 3 material risks)
5. **Valuation Assessment** (1-2 sentences on whether the stock is cheap, fair, or expensive)
6. **12-Month Price Target Rationale** (1-2 sentences)
7. **Investment Recommendation**: One of [Strong Buy | Buy | Hold | Sell | Strong Sell]
8. **Recommendation Rationale** (3-4 concise sentences explaining the recommendation)

Format your response in clean markdown. Be data-driven, specific, and concise."""


_GROWTH_PREDICTION_PROMPT = """You are an expert financial forecasting analyst with deep expertise in equity research.

## Company: {ticker} — {company_name}
## Sector: {sector}

## Historical Financials
- Revenue Growth (YoY): {revenue_growth}%
- Earnings Growth (YoY): {earnings_growth}%
- FCF Growth: {fcf_growth}
- Gross Margin Trend: {gross_margin}%
- Operating Leverage: {operating_margin}%

## Market Context
- Industry: {industry}
- Beta: {beta}
- Analyst Consensus: {analyst_rec}
- Analyst Target Price: ${analyst_target}
- Current Price: ${current_price}

Based on the financial trajectory and market context, provide:
1. **3-Year Revenue Growth Forecast** (low / base / high scenarios with percentages)
2. **Earnings Growth Forecast** (next 12 months and 3-year CAGR)
3. **Key Growth Catalysts** (top 3 catalysts driving future growth)
4. **Growth Headwinds** (top 2 factors that could limit growth)
5. **Confidence Level**: [High | Medium | Low] with a brief justification

Be quantitative where possible. Format in clean markdown."""


class GraniteAI:
    """IBM Granite model integration for investment analysis."""

    def __init__(self):
        self._iam_token: Optional[str] = None
        self._timeout = app_cfg.request_timeout
        self._session = requests.Session()

    # ──────────────────────────────────────────────
    # PUBLIC METHODS
    # ──────────────────────────────────────────────

    def generate_analysis(
        self,
        kpis: dict[str, Any],
        ratios: dict[str, Any],
        sentiment: dict[str, Any],
        risk: dict[str, Any],
        competitor: dict[str, Any],
    ) -> dict[str, Any]:
        logger.info("Generating Granite analysis for %s", kpis.get("ticker"))

        prompt = self._build_analysis_prompt(kpis, ratios, sentiment, risk, competitor)
        raw_output = self._call_granite(prompt, max_tokens=1200)

        # Parse recommendation from output
        recommendation = self._extract_recommendation(raw_output)

        return {
            "ticker": kpis.get("ticker"),
            "analysis_text": raw_output,
            "recommendation": recommendation,
            "model_id": watsonx_cfg.granite_model_id,
        }

    def generate_growth_predictions(self, kpis: dict[str, Any]) -> dict[str, Any]:
        logger.info("Generating growth predictions for %s", kpis.get("ticker"))

        prompt = self._build_growth_prompt(kpis)
        raw_output = self._call_granite(prompt, max_tokens=800)

        return {
            "ticker": kpis.get("ticker"),
            "growth_predictions_text": raw_output,
            "model_id": watsonx_cfg.granite_model_id,
        }

    # ──────────────────────────────────────────────
    # PROMPT BUILDERS
    # ──────────────────────────────────────────────

    def _build_analysis_prompt(
        self,
        kpis: dict,
        ratios: dict,
        sentiment: dict,
        risk: dict,
        competitor: dict,
    ) -> str:
        def fmt_num(v, suffix="", scale=1.0, decimals=2):
            if v is None:
                return "N/A"
            return f"{v * scale:,.{decimals}f}{suffix}"

        def fmt_usd(v, scale=1e-9):
            if v is None:
                return "N/A"
            b = v * scale
            return f"{b:.2f}B"

        risk_factors_text = "; ".join(
            f"{f['code']} ({f['severity']})" for f in risk.get("risk_factors", [])[:5]
        ) or "None detected"

        # Build competitor summary
        comp_rows = competitor.get("comparison_table", [])[:5]
        competitor_summary_lines = []
        if comp_rows:
            competitor_summary_lines.append("| Ticker | P/E | ROE | Net Margin | Rev Growth |")
            competitor_summary_lines.append("|--------|-----|-----|------------|------------|")
            for row in comp_rows:
                pe = fmt_num(row.get("pe_ratio"), decimals=1)
                roe = fmt_num(row.get("roe"), suffix="%", scale=100)
                nm = fmt_num(row.get("profit_margin"), suffix="%", scale=100)
                rg = fmt_num(row.get("revenue_growth"), suffix="%", scale=100)
                competitor_summary_lines.append(
                    f"| {row.get('ticker', 'N/A')} | {pe} | {roe} | {nm} | {rg} |"
                )
        competitor_summary = "\n".join(competitor_summary_lines) if competitor_summary_lines else "No peer data available"

        return _ANALYSIS_PROMPT_TEMPLATE.format(
            ticker=kpis.get("ticker", "N/A"),
            company_name=kpis.get("company_name", "N/A"),
            sector=kpis.get("sector", "N/A"),
            industry=kpis.get("industry", "N/A"),
            revenue_ttm=fmt_usd(kpis.get("revenue_ttm")),
            revenue_growth=fmt_num(kpis.get("revenue_growth"), scale=100),
            net_income=fmt_usd(kpis.get("net_income")),
            eps_ttm=fmt_num(kpis.get("eps_ttm")),
            gross_margin=fmt_num(kpis.get("gross_margin"), scale=100),
            profit_margin=fmt_num(kpis.get("profit_margin"), scale=100),
            roe=fmt_num(kpis.get("roe"), scale=100),
            roa=fmt_num(kpis.get("roa"), scale=100),
            pe_ratio=fmt_num(kpis.get("pe_ratio"), decimals=1),
            forward_pe=fmt_num(kpis.get("forward_pe"), decimals=1),
            ev_to_ebitda=fmt_num(kpis.get("ev_to_ebitda"), decimals=1),
            debt_to_equity=fmt_num(kpis.get("debt_to_equity"), decimals=2),
            current_ratio=fmt_num(kpis.get("current_ratio"), decimals=2),
            free_cash_flow=fmt_usd(kpis.get("free_cash_flow")),
            value_score=fmt_num(ratios.get("value_score"), decimals=1),
            quality_score=fmt_num(ratios.get("quality_score"), decimals=1),
            growth_score=fmt_num(ratios.get("growth_score"), decimals=1),
            safety_score=fmt_num(ratios.get("safety_score"), decimals=1),
            overall_score=fmt_num(ratios.get("overall_financial_score"), decimals=1),
            sentiment_score=fmt_num(sentiment.get("sentiment_score"), decimals=1),
            sentiment_label=sentiment.get("overall_label", "neutral"),
            risk_score=risk.get("risk_score", 0),
            risk_level=risk.get("risk_level", "unknown"),
            risk_factors=risk_factors_text,
            competitor_summary=competitor_summary,
        )

    def _build_growth_prompt(self, kpis: dict) -> str:
        def fmt(v, scale=100, suffix="%", decimals=2):
            if v is None:
                return "N/A"
            return f"{v * scale:.{decimals}f}{suffix}"

        return _GROWTH_PREDICTION_PROMPT.format(
            ticker=kpis.get("ticker", "N/A"),
            company_name=kpis.get("company_name", "N/A"),
            sector=kpis.get("sector", "N/A"),
            industry=kpis.get("industry", "N/A"),
            revenue_growth=fmt(kpis.get("revenue_growth")),
            earnings_growth=fmt(kpis.get("earnings_growth")),
            fcf_growth="N/A",
            gross_margin=fmt(kpis.get("gross_margin")),
            operating_margin=fmt(kpis.get("operating_margin")),
            beta=kpis.get("beta", "N/A"),
            analyst_rec=kpis.get("analyst_recommendation", "N/A"),
            analyst_target=kpis.get("analyst_target_price", "N/A"),
            current_price=kpis.get("current_price", "N/A"),
        )

    # ──────────────────────────────────────────────
    # IBM WATSONX API CALL
    # ──────────────────────────────────────────────

    def _call_granite(self, prompt: str, max_tokens: int = 1000) -> str:
        if not watsonx_cfg.api_key or not watsonx_cfg.project_id:
            logger.warning("watsonx credentials not configured — returning mock response")
            return self._mock_response(prompt)

        token = self._get_iam_token()
        if not token:
            logger.error("Failed to obtain IAM token")
            return self._mock_response(prompt)

        url = f"{watsonx_cfg.url}/ml/v1/text/generation?version=2023-05-29"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        payload = {
            "model_id": watsonx_cfg.granite_model_id,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_tokens,
                "min_new_tokens": 100,
                "stop_sequences": [],
                "repetition_penalty": 1.1,
            },
            "project_id": watsonx_cfg.project_id,
        }

        try:
            resp = self._session.post(url, headers=headers, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data["results"][0]["generated_text"].strip()
        except Exception as exc:
            logger.error("Granite API error: %s", exc)
            return self._mock_response(prompt)

    def _get_iam_token(self) -> Optional[str]:
        if self._iam_token:
            return self._iam_token
        try:
            resp = requests.post(
                _IAM_TOKEN_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey": watsonx_cfg.api_key,
                },
                timeout=self._timeout,
            )
            resp.raise_for_status()
            self._iam_token = resp.json()["access_token"]
            return self._iam_token
        except Exception as exc:
            logger.error("IAM token error: %s", exc)
            return None

    # ──────────────────────────────────────────────
    # RECOMMENDATION EXTRACTOR
    # ──────────────────────────────────────────────

    @staticmethod
    def _extract_recommendation(text: str) -> str:
        text_upper = text.upper()
        for rec in ["STRONG BUY", "STRONG SELL", "BUY", "SELL", "HOLD"]:
            if rec in text_upper:
                return rec.title()
        return "Hold"  # safe default

    # ──────────────────────────────────────────────
    # MOCK (when no credentials configured)
    # ──────────────────────────────────────────────

    @staticmethod
    def _mock_response(prompt: str) -> str:
        return (
            "**[MOCK — Configure WATSONX_API_KEY and WATSONX_PROJECT_ID for live responses]**\n\n"
            "## Business Quality Assessment\n"
            "This company operates in a competitive industry with a solid market position. "
            "Its diversified revenue streams provide resilience through market cycles.\n\n"
            "## Financial Health Summary\n"
            "The balance sheet is well-structured with manageable debt levels. "
            "Cash flow generation remains consistent, supporting capital allocation flexibility.\n\n"
            "## Growth Outlook\n"
            "Revenue growth is driven by product innovation and market expansion. "
            "Margin expansion opportunities exist through operating leverage.\n\n"
            "## Key Risks\n"
            "- Macroeconomic headwinds could dampen demand\n"
            "- Competitive pressure on pricing and margins\n"
            "- Regulatory uncertainty in key markets\n\n"
            "## Valuation Assessment\n"
            "Current valuation multiples appear reasonable relative to growth prospects.\n\n"
            "## 12-Month Price Target Rationale\n"
            "A blended DCF and comparable analysis supports modest upside from current levels.\n\n"
            "## Investment Recommendation\n"
            "**Hold** — The risk/reward appears balanced at current prices. "
            "Monitor upcoming earnings for catalysts before adding to positions."
        )

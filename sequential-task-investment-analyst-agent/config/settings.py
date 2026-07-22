"""
Central configuration for the Sequential Task Investment Analyst Agent.
All secrets are loaded from environment variables — never hardcoded.
"""

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WatsonxConfig:
    api_key: str = field(default_factory=lambda: os.getenv("WATSONX_API_KEY", ""))
    project_id: str = field(default_factory=lambda: os.getenv("WATSONX_PROJECT_ID", ""))
    url: str = field(default_factory=lambda: os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"))
    granite_model_id: str = field(default_factory=lambda: os.getenv("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"))
    granite_finance_model_id: str = field(default_factory=lambda: os.getenv("GRANITE_FINANCE_MODEL_ID", "ibm/granite-20b-multilingual"))


@dataclass
class LangflowConfig:
    host: str = field(default_factory=lambda: os.getenv("LANGFLOW_HOST", "http://localhost:7860"))
    api_key: str = field(default_factory=lambda: os.getenv("LANGFLOW_API_KEY", ""))
    flow_id: str = field(default_factory=lambda: os.getenv("LANGFLOW_FLOW_ID", ""))


@dataclass
class OrchestrateConfig:
    tenant_id: str = field(default_factory=lambda: os.getenv("ORCHESTRATE_TENANT_ID", ""))
    api_key: str = field(default_factory=lambda: os.getenv("ORCHESTRATE_API_KEY", ""))
    base_url: str = field(default_factory=lambda: os.getenv("ORCHESTRATE_BASE_URL", "https://api.ibm-orchestrate.com/v1"))


@dataclass
class DataSourceConfig:
    alpha_vantage_key: str = field(default_factory=lambda: os.getenv("ALPHA_VANTAGE_API_KEY", "demo"))
    newsapi_key: str = field(default_factory=lambda: os.getenv("NEWSAPI_KEY", ""))
    finnhub_key: str = field(default_factory=lambda: os.getenv("FINNHUB_API_KEY", ""))
    polygon_key: str = field(default_factory=lambda: os.getenv("POLYGON_API_KEY", ""))
    sec_user_agent: str = field(default_factory=lambda: os.getenv("SEC_USER_AGENT", "InvestmentAnalystAgent/1.0 contact@example.com"))


@dataclass
class AppConfig:
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    cache_ttl_seconds: int = field(default_factory=lambda: int(os.getenv("CACHE_TTL_SECONDS", "3600")))
    max_retries: int = field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "30")))
    dashboard_port: int = field(default_factory=lambda: int(os.getenv("DASHBOARD_PORT", "8050")))


# Singleton instances
watsonx_cfg = WatsonxConfig()
langflow_cfg = LangflowConfig()
orchestrate_cfg = OrchestrateConfig()
datasource_cfg = DataSourceConfig()
app_cfg = AppConfig()

# Financial thresholds used in scoring
RISK_THRESHOLDS = {
    "debt_to_equity_high": 2.0,
    "current_ratio_low": 1.0,
    "pe_ratio_high": 40.0,
    "roe_low": 0.05,
    "profit_margin_low": 0.03,
}

RECOMMENDATION_THRESHOLDS = {
    "strong_buy": 80,
    "buy": 65,
    "hold": 45,
    "sell": 30,
    # Below 30 → Strong Sell
}

COMPETITOR_MAP = {
    "AAPL": ["MSFT", "GOOGL", "SAMSF", "META"],
    "TSLA": ["F", "GM", "RIVN", "NIO", "LCID"],
    "MSFT": ["AAPL", "GOOGL", "AMZN", "META"],
    "GOOGL": ["MSFT", "META", "SNAP", "AMZN"],
    "AMZN": ["MSFT", "GOOGL", "WMT", "TGT"],
    "META": ["SNAP", "GOOGL", "TWTR", "PINS"],
    "NVDA": ["AMD", "INTC", "QCOM", "AVGO"],
    "JPM": ["BAC", "WFC", "C", "GS"],
    "JNJ": ["PFE", "MRK", "ABBV", "LLY"],
}

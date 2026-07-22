"""
FastAPI REST server for the Investment Analyst Agent.
Exposes endpoints for analysis, health, and streaming status.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from config.settings import app_cfg
from src.agents.investment_agent import InvestmentAnalystAgent

logger = logging.getLogger(__name__)

# Global agent instance (thread-safe reads are fine; one instance per process)
_agent: Optional[InvestmentAnalystAgent] = None
# In-memory result cache {ticker: result_dict}
_cache: dict[str, dict] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    logger.info("Initializing Investment Analyst Agent...")
    _agent = InvestmentAnalystAgent()
    logger.info("Agent ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Sequential Task Investment Analyst Agent",
    description="AI-powered investment analysis using IBM Granite, Langflow, and Orchestrate.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. AAPL, TSLA")
    force_refresh: bool = Field(False, description="Bypass cache and re-run full analysis")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        v = v.strip().upper()
        if not v.isalpha() or len(v) > 10:
            raise ValueError("Ticker must be 1-10 alphabetic characters")
        return v


class HealthResponse(BaseModel):
    status: str
    version: str
    agent_ready: bool


# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "agent_ready": _agent is not None,
    }


@app.post("/analyze", tags=["Analysis"])
async def analyze(request: AnalysisRequest):
    """
    Run the full 10-step sequential investment analysis workflow for a ticker.
    Returns comprehensive KPIs, ratios, competitor comparison, sentiment,
    risk assessment, and AI-generated recommendation.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    ticker = request.ticker

    # Serve from cache if available and not forced
    if not request.force_refresh and ticker in _cache:
        logger.info("Cache hit for %s", ticker)
        return JSONResponse(content={**_cache[ticker], "cached": True})

    try:
        # Run in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _agent.analyze, ticker)
        result_dict = _agent.to_dict(result)
        _cache[ticker] = result_dict
        return JSONResponse(content={**result_dict, "cached": False})
    except Exception as exc:
        logger.error("Analysis error for %s: %s", ticker, exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/analyze/{ticker}", tags=["Analysis"])
async def analyze_get(
    ticker: str,
    force_refresh: bool = Query(False, description="Bypass cache"),
):
    """GET convenience endpoint for quick ticker lookups."""
    return await analyze(AnalysisRequest(ticker=ticker, force_refresh=force_refresh))


@app.get("/recommendation/{ticker}", tags=["Analysis"])
async def get_recommendation(ticker: str):
    """Return only the recommendation summary for a previously analyzed ticker."""
    ticker = ticker.upper()
    if ticker not in _cache:
        raise HTTPException(
            status_code=404,
            detail=f"No analysis found for {ticker}. Call /analyze/{ticker} first.",
        )
    rec = _cache[ticker].get("recommendation", {})
    return JSONResponse(content=rec)


@app.get("/kpis/{ticker}", tags=["Analysis"])
async def get_kpis(ticker: str):
    """Return extracted KPIs for a previously analyzed ticker."""
    ticker = ticker.upper()
    if ticker not in _cache:
        raise HTTPException(status_code=404, detail=f"No analysis for {ticker}")
    return JSONResponse(content=_cache[ticker].get("kpis", {}))


@app.get("/risk/{ticker}", tags=["Analysis"])
async def get_risk(ticker: str):
    """Return risk assessment for a previously analyzed ticker."""
    ticker = ticker.upper()
    if ticker not in _cache:
        raise HTTPException(status_code=404, detail=f"No analysis for {ticker}")
    return JSONResponse(content=_cache[ticker].get("risk", {}))


@app.get("/sentiment/{ticker}", tags=["Analysis"])
async def get_sentiment(ticker: str):
    """Return sentiment analysis for a previously analyzed ticker."""
    ticker = ticker.upper()
    if ticker not in _cache:
        raise HTTPException(status_code=404, detail=f"No analysis for {ticker}")
    return JSONResponse(content=_cache[ticker].get("sentiment", {}))


@app.get("/competitors/{ticker}", tags=["Analysis"])
async def get_competitors(ticker: str):
    """Return competitor comparison for a previously analyzed ticker."""
    ticker = ticker.upper()
    if ticker not in _cache:
        raise HTTPException(status_code=404, detail=f"No analysis for {ticker}")
    return JSONResponse(content=_cache[ticker].get("competitor_analysis", {}))


@app.delete("/cache/{ticker}", tags=["System"])
async def clear_cache(ticker: str):
    """Clear cached results for a ticker."""
    ticker = ticker.upper()
    removed = _cache.pop(ticker, None)
    return {"removed": removed is not None, "ticker": ticker}


@app.delete("/cache", tags=["System"])
async def clear_all_cache():
    """Clear all cached results."""
    count = len(_cache)
    _cache.clear()
    return {"cleared": count}

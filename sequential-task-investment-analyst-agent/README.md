# Sequential Task Investment Analyst Agent

> An enterprise-grade, AI-powered investment analysis system built with **IBM watsonx**, **IBM Langflow**, **IBM Orchestrate**, and **IBM Granite Models**. Automates the complete 10-step investment analysis workflow — from raw data collection to actionable buy/sell recommendations.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Workflow — 10 Sequential Steps](#workflow)
4. [Folder Structure](#folder-structure)
5. [Technology Stack](#technology-stack)
6. [API Integrations](#api-integrations)
7. [IBM Granite Model Integration](#ibm-granite-model-integration)
8. [IBM Langflow Workflow](#ibm-langflow-workflow)
9. [IBM Orchestrate Automation](#ibm-orchestrate-automation)
10. [Dashboard](#dashboard)
11. [Quick Start](#quick-start)
12. [Configuration](#configuration)
13. [API Reference](#api-reference)
14. [Deployment](#deployment)
15. [Testing](#testing)

---

## Overview

The **Sequential Task Investment Analyst Agent** automates institutional-quality investment research by chaining 10 analytical tasks in sequence. Given any stock ticker (e.g. `AAPL`, `TSLA`, `NVDA`), the system:

- **Collects** multi-source financial data (5 sources in parallel)
- **Validates** and cleans data with a completeness score
- **Extracts** 50+ standardized KPIs
- **Calculates** composite financial scores (Value / Quality / Growth / Safety)
- **Compares** against up to 4 peer competitors
- **Analyzes** market news with VADER sentiment scoring
- **Detects** 12 categories of financial and market risk
- **Generates** deep analysis and growth predictions via **IBM Granite LLMs**
- **Produces** a final recommendation: `Strong Buy | Buy | Hold | Sell | Strong Sell`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SEQUENTIAL TASK INVESTMENT ANALYST AGENT                 │
│                                                                             │
│  ┌──────────────┐   REST API    ┌─────────────────────────────────────────┐│
│  │   Dashboard  │◄─────────────►│           FastAPI Server                ││
│  │  (HTML/JS)   │               │         /analyze  /health               ││
│  └──────────────┘               └──────────────┬──────────────────────────┘│
│                                                 │                           │
│  ┌──────────────────────────────────────────────▼──────────────────────────┐│
│  │                    InvestmentAnalystAgent (Orchestrator)                 ││
│  │                                                                          ││
│  │  Step 1   Step 2   Step 3   Step 4   Step 5   Step 6   Step 7  Steps 8-10││
│  │  Collect  Validate Extract  Ratios  Competitors Sentiment Risk   AI+Rec  ││
│  │     │        │        │       │         │          │       │        │    ││
│  └─────┼────────┼────────┼───────┼─────────┼──────────┼───────┼────────┼───┘│
│        │        │        │       │         │          │       │        │    │
│  ┌─────▼──┐ ┌───▼──┐ ┌───▼──┐ ┌─▼──┐ ┌───▼──┐ ┌─────▼──┐ ┌──▼──┐ ┌──▼──┐│
│  │Yahoo   │ │Data  │ │ KPI  │ │Rat │ │Compet│ │Sentim  │ │Risk │ │IBM  ││
│  │Finance │ │Valid │ │Extrc │ │Calc│ │Analz │ │Analyzer│ │Detec│ │Gran ││
│  │Alpha V │ │ator  │ │ tor  │ │ulat│ │er    │ │(VADER) │ │tor  │ │ite  ││
│  │SEC EDGR│ └──────┘ └──────┘ │ or │ └──────┘ └────────┘ └─────┘ │ LLM ││
│  │Finnhub │                   └────┘                              └─────┘│
│  │NewsAPI │                                                               │
│  └────────┘                                                               │
│                                                                           │
│  ┌──────────────────────────┐   ┌──────────────────────────────────────┐  │
│  │    IBM Langflow           │   │        IBM Orchestrate                │  │
│  │  (Visual Workflow Editor) │   │  (10-Skill Automation Manifest)      │  │
│  │  investment_analyst_flow  │   │   orchestrate_manifest.yaml          │  │
│  └──────────────────────────┘   └──────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow

The agent executes exactly **10 sequential steps**, each with its own module:

| # | Step | Module | Output |
|---|------|--------|--------|
| 1 | **Data Collection** | `src/data/collector.py` | Raw financial data from 5 sources |
| 2 | **Data Validation** | `src/data/validator.py` | Cleaned data + completeness score |
| 3 | **KPI Extraction** | `src/analysis/kpi_extractor.py` | 50+ standardized KPIs |
| 4 | **Ratio Calculation** | `src/analysis/ratios_calculator.py` | Composite scores (0-100 each) |
| 5 | **Competitor Analysis** | `src/analysis/competitor_analyzer.py` | Peer comparison table + rankings |
| 6 | **Sentiment Analysis** | `src/analysis/sentiment_analyzer.py` | Sentiment score 0-100 + label |
| 7 | **Risk Detection** | `src/analysis/risk_detector.py` | Risk score + 12-dimension breakdown |
| 8 | **AI Analysis** | `src/ai/granite_client.py` | Written analysis via IBM Granite |
| 9 | **Growth Predictions** | `src/ai/granite_client.py` | 3-year forecast (3 scenarios) |
| 10 | **Recommendation** | `src/ai/recommendation_engine.py` | Strong Buy/Buy/Hold/Sell/Strong Sell |

### Recommendation Composite Score Weights

| Component | Weight | Source |
|-----------|--------|--------|
| Financial Quality | 35% | `overall_financial_score` from ratios |
| Safety / Risk Inverse | 20% | `100 - risk_score` |
| Analyst Consensus | 15% | yfinance `recommendationKey` |
| Sentiment | 15% | VADER compound score |
| Upside Potential | 10% | Current vs analyst target price |
| Competitor Ranking | 5% | Peer percentile rank |

---

## Folder Structure

```
sequential-task-investment-analyst-agent/
│
├── main.py                         # App entry point (FastAPI + uvicorn)
├── requirements.txt                # Python dependencies
├── pyproject.toml                  # Pytest + linting config
├── Dockerfile                      # Container image
├── docker-compose.yml              # Multi-service stack (API + Langflow + Redis)
├── .env.example                    # Environment variable template
│
├── config/
│   ├── __init__.py
│   └── settings.py                 # All config (watsonx, Langflow, Orchestrate, APIs)
│
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── investment_agent.py     # 🧠 Main workflow orchestrator
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── collector.py            # Step 1: Multi-source data collection
│   │   └── validator.py            # Step 2: Data validation & cleaning
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── kpi_extractor.py        # Step 3: KPI extraction (50+ fields)
│   │   ├── ratios_calculator.py    # Step 4: Ratio + composite score calculation
│   │   ├── competitor_analyzer.py  # Step 5: Peer comparison & ranking
│   │   ├── sentiment_analyzer.py   # Step 6: News sentiment (VADER)
│   │   └── risk_detector.py        # Step 7: Multi-dimension risk scoring
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── granite_client.py       # Steps 8-9: IBM Granite LLM calls
│   │   └── recommendation_engine.py # Step 10: Final recommendation synthesis
│   │
│   └── api/
│       ├── __init__.py
│       └── server.py               # FastAPI REST server
│
├── langflow/
│   └── investment_analyst_flow.json  # IBM Langflow flow definition
│
├── orchestrate/
│   └── orchestrate_manifest.yaml    # IBM Orchestrate skill + workflow manifest
│
├── tests/
│   ├── __init__.py
│   └── test_agent.py                # Unit + integration tests
│
├── scripts/
│   └── run_analysis.py              # CLI runner
│
└── docs/
    └── architecture.md              # Extended architecture notes
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **AI / LLM** | IBM Granite 13B Instruct v2 | Analysis, summarization, predictions |
| **Workflow** | IBM Langflow | Visual 10-node pipeline builder |
| **Automation** | IBM Orchestrate | Skill registration and task automation |
| **Platform** | IBM watsonx.ai | Model hosting and inference |
| **API** | FastAPI + uvicorn | High-performance REST server |
| **Data** | yfinance, Alpha Vantage, SEC EDGAR, Finnhub, NewsAPI | Financial data |
| **Sentiment** | VADER Sentiment | News NLP scoring |
| **Container** | Docker + Docker Compose | Deployment |

---

## API Integrations

### Yahoo Finance (`yfinance`)
- **What it provides:** Company info, real-time price, income statement, balance sheet, cash flow, 1-year price history, analyst recommendations
- **Auth:** None required (public)
- **Module:** `src/data/collector.py:_collect_yfinance()`

### Alpha Vantage
- **What it provides:** Fundamentals overview, quarterly income/balance/cash flow, EPS history
- **Auth:** Free API key at [alphavantage.co](https://www.alphavantage.co/support/#api-key)
- **Env var:** `ALPHA_VANTAGE_API_KEY`
- **Rate limit:** 25 requests/day (free), 75/min (premium)

### SEC EDGAR
- **What it provides:** 10-K, 10-Q filing metadata and CIK lookup
- **Auth:** None (requires descriptive User-Agent header)
- **Env var:** `SEC_USER_AGENT` (e.g. `YourName/1.0 email@example.com`)

### Finnhub
- **What it provides:** Company profile, financial metrics, peer list, earnings sentiment
- **Auth:** Free API key at [finnhub.io](https://finnhub.io/register)
- **Env var:** `FINNHUB_API_KEY`

### NewsAPI
- **What it provides:** Last 30 days of news articles for a ticker
- **Auth:** Free key at [newsapi.org](https://newsapi.org/register)
- **Env var:** `NEWSAPI_KEY`

---

## IBM Granite Model Integration

The agent uses IBM Granite via the **watsonx.ai REST API** (no SDK dependency).

### Authentication
```python
# IBM IAM token exchange
POST https://iam.cloud.ibm.com/identity/token
grant_type=urn:ibm:params:oauth:grant-type:apikey&apikey=YOUR_KEY
```

### Inference
```python
POST https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29
{
  "model_id": "ibm/granite-13b-instruct-v2",
  "input": "<analysis prompt>",
  "parameters": {
    "decoding_method": "greedy",
    "max_new_tokens": 1200,
    "repetition_penalty": 1.1
  },
  "project_id": "YOUR_PROJECT_ID"
}
```

### Two Granite Calls Per Analysis
1. **Financial Analysis Prompt** — business quality, financial health, key risks, valuation, recommendation reasoning (~1,200 tokens)
2. **Growth Prediction Prompt** — 3-year low/base/high revenue/earnings forecast with catalysts and headwinds (~800 tokens)

---

## IBM Langflow Workflow

The flow file at `langflow/investment_analyst_flow.json` defines an 11-node directed graph:

```
[Ticker Input]
      │
      ▼
[Step 1: Data Collection] ──► [Step 2: Validation] ──► [Step 3: KPI Extraction]
                                       │                         │
                                  [News] ◄───────────────────────┤
                                       │                         │
                                       ▼                         ▼
                               [Step 6: Sentiment]      [Step 4: Ratios]
                                       │                         │
                                       └────────────┬────────────┘
                                                    │
                                  [Step 5: Competitors] ◄── [Ticker]
                                                    │
                                                    ▼
                                           [Step 7: Risk]
                                                    │
                                                    ▼
                              [Step 8: IBM Granite Analysis] ──► [Step 9: Growth Predictions]
                                                    │
                                                    ▼
                                    [Step 10: Final Recommendation]
                                                    │
                                                    ▼
                                           [Analysis Output]
```

### Import into Langflow
```bash
# Start Langflow
langflow run
# Open http://localhost:7860
# Click Import → Select langflow/investment_analyst_flow.json
# Configure your IBM watsonx credentials in the Granite nodes
```

---

## IBM Orchestrate Automation

The manifest at `orchestrate/orchestrate_manifest.yaml` registers **10 skills** and a **full workflow**:

### Skills Registered
| Skill Name | Endpoint | Description |
|-----------|----------|-------------|
| `collect_financial_data` | `POST /collect` | Multi-source data fetch |
| `validate_data` | `POST /validate` | Quality validation |
| `extract_kpis` | `POST /kpis/extract` | KPI standardization |
| `calculate_ratios` | `POST /ratios/calculate` | Composite scoring |
| `analyze_competitors` | `POST /competitors/analyze` | Peer benchmarking |
| `analyze_sentiment` | `POST /sentiment/analyze` | VADER + news NLP |
| `detect_risks` | `POST /risk/detect` | Multi-dimension risk scoring |
| `generate_ai_analysis` | `POST /ai/analyze` | IBM Granite analysis |
| `generate_growth_predictions` | `POST /ai/predict-growth` | 3-year forecast |
| `generate_recommendation` | `POST /recommendation/generate` | Final verdict |

### Deploy to Orchestrate
```bash
# Authenticate
ibm-ai-orchestrate auth login --apikey $ORCHESTRATE_API_KEY

# Import manifest
ibm-ai-orchestrate automations import -f orchestrate/orchestrate_manifest.yaml

# Trigger via CLI
ibm-ai-orchestrate automations run full_investment_analysis \
  --input '{"ticker": "AAPL"}'
```

---

## Dashboard

Open `src/dashboard/index.html` directly in a browser, or serve it with the API.

**Features:**
- Company header with price, recommendation badge, and composite score gauge
- 6 KPI tiles (Revenue, EPS, Gross Margin, ROE, P/E, Free Cash Flow)
- 4 Score tiles (Value / Quality / Growth / Safety — color-coded bars)
- Competitor comparison bar chart
- Risk factors table with severity color coding
- Sentiment breakdown (bullish / neutral / bearish article counts)
- AI Analysis full text panel
- Workflow step status tracker
- Responsive single-column layout

---

## Quick Start

### 1. Clone and install
```bash
git clone <repo-url>
cd sequential-task-investment-analyst-agent

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — add WATSONX_API_KEY, WATSONX_PROJECT_ID, etc.
```

### 3. Run CLI analysis
```bash
python scripts/run_analysis.py AAPL
python scripts/run_analysis.py TSLA --json
python scripts/run_analysis.py NVDA --output results/nvda.json
```

### 4. Start the API server
```bash
python main.py
# API running at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### 5. Run via Docker
```bash
docker compose up --build
# API: http://localhost:8000
# Langflow: http://localhost:7860
```

---

## Configuration

All settings are in `config/settings.py` and loaded from environment variables. See `.env.example` for the full list.

| Variable | Required | Description |
|----------|----------|-------------|
| `WATSONX_API_KEY` | Yes* | IBM Cloud API key for watsonx.ai |
| `WATSONX_PROJECT_ID` | Yes* | watsonx.ai project ID |
| `GRANITE_MODEL_ID` | No | Default: `ibm/granite-13b-instruct-v2` |
| `ALPHA_VANTAGE_API_KEY` | Recommended | Free at alphavantage.co |
| `NEWSAPI_KEY` | Recommended | Free at newsapi.org |
| `FINNHUB_API_KEY` | Optional | Supplemental financial data |
| `SEC_USER_AGENT` | Recommended | Required for SEC EDGAR |
| `LOG_LEVEL` | No | Default: `INFO` |

> *Without watsonx credentials the agent runs in **mock mode** — all steps work except Granite generates a placeholder response.

---

## API Reference

### `POST /analyze`
Run the full 10-step workflow.
```json
{ "ticker": "AAPL", "force_refresh": false }
```

### `GET /analyze/{ticker}`
Convenience GET endpoint.

### `GET /recommendation/{ticker}`
Return only the recommendation for a cached analysis.

### `GET /kpis/{ticker}`
Return extracted KPIs.

### `GET /risk/{ticker}`
Return risk assessment.

### `GET /sentiment/{ticker}`
Return sentiment scores.

### `GET /competitors/{ticker}`
Return competitor comparison.

### `DELETE /cache/{ticker}`
Clear cache for a specific ticker.

---

## Deployment

### Docker Compose (recommended)
```bash
docker compose up --build -d
```

### Kubernetes
```yaml
# Example deployment manifest
apiVersion: apps/v1
kind: Deployment
metadata:
  name: investment-analyst-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: investment-analyst
  template:
    spec:
      containers:
        - name: api
          image: investment-analyst:1.0.0
          ports:
            - containerPort: 8000
          envFrom:
            - secretRef:
                name: investment-analyst-secrets
```

### IBM Code Engine
```bash
ibmcloud ce application create \
  --name investment-analyst-api \
  --image us.icr.io/mynamespace/investment-analyst:1.0.0 \
  --port 8000 \
  --env-from-secret investment-analyst-secrets
```

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test class
pytest tests/test_agent.py::TestRatiosCalculator -v
```

Tests cover:
- KPI extraction field validation
- Ratio score range enforcement (0-100)
- Risk score boundary conditions
- Sentiment scoring with positive/negative/empty news
- Recommendation engine validity and reasoning generation

---

## License

MIT License — see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Add tests for new functionality
4. Submit a pull request

---

*Built with ❤️ using IBM watsonx, IBM Langflow, IBM Orchestrate, and IBM Granite Models.*

#!/usr/bin/env python3
"""
Quick CLI to run an investment analysis from the command line.
Usage: python scripts/run_analysis.py AAPL
       python scripts/run_analysis.py TSLA --json
       python scripts/run_analysis.py MSFT --no-competitors
"""

import argparse
import json
import logging
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from src.agents.investment_agent import InvestmentAnalystAgent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)


def print_summary(result_dict: dict):
    rec = result_dict.get("recommendation", {})
    kpis = result_dict.get("kpis", {})
    risk = result_dict.get("risk", {})
    sentiment = result_dict.get("sentiment", {})

    print("\n" + "═" * 70)
    print(f"  📊  INVESTMENT ANALYSIS: {rec.get('ticker', 'N/A')} — {rec.get('company_name', '')}")
    print("═" * 70)

    print(f"\n{'─'*70}")
    print("  FINAL RECOMMENDATION")
    print(f"{'─'*70}")
    final = rec.get("final_recommendation", "N/A")
    score = rec.get("composite_score", 0)
    colors = {
        "Strong Buy": "🟢🟢", "Buy": "🟢", "Hold": "🟡",
        "Sell": "🔴", "Strong Sell": "🔴🔴"
    }
    print(f"  {colors.get(final, '⚪')}  {final}  (Composite Score: {score:.1f}/100)")

    print(f"\n  Reasoning:")
    for reason in rec.get("reasoning", []):
        print(f"    • {reason}")

    print(f"\n{'─'*70}")
    print("  KEY FINANCIALS")
    print(f"{'─'*70}")
    price = kpis.get("current_price")
    target = kpis.get("analyst_target_price")
    upside = ((target - price) / price * 100) if price and target else None

    print(f"  Current Price:      ${price:,.2f}" if price else "  Current Price:      N/A")
    print(f"  Analyst Target:     ${target:,.2f}" if target else "  Analyst Target:     N/A")
    if upside is not None:
        print(f"  Upside Potential:   {upside:+.1f}%")
    print(f"  Market Cap:         ${kpis.get('market_cap', 0)/1e9:.1f}B" if kpis.get('market_cap') else "  Market Cap:         N/A")
    print(f"  P/E Ratio:          {kpis.get('pe_ratio', 'N/A')}")
    print(f"  Revenue (TTM):      ${kpis.get('revenue_ttm', 0)/1e9:.1f}B" if kpis.get('revenue_ttm') else "  Revenue (TTM):      N/A")
    print(f"  Revenue Growth:     {kpis.get('revenue_growth', 0)*100:.1f}%" if kpis.get('revenue_growth') else "  Revenue Growth:     N/A")
    print(f"  Net Margin:         {kpis.get('profit_margin', 0)*100:.1f}%" if kpis.get('profit_margin') else "  Net Margin:         N/A")
    print(f"  ROE:                {kpis.get('roe', 0)*100:.1f}%" if kpis.get('roe') else "  ROE:                N/A")
    print(f"  Free Cash Flow:     ${kpis.get('free_cash_flow', 0)/1e9:.1f}B" if kpis.get('free_cash_flow') else "  Free Cash Flow:     N/A")

    print(f"\n{'─'*70}")
    print("  RISK & SENTIMENT")
    print(f"{'─'*70}")
    print(f"  Risk Score:         {risk.get('risk_score', 0)}/100 ({risk.get('risk_level', 'N/A').replace('_', ' ').title()})")
    print(f"  Sentiment Score:    {sentiment.get('sentiment_score', 50):.0f}/100 ({sentiment.get('overall_label', 'N/A').replace('_', ' ')})")

    risk_factors = risk.get("risk_factors", [])
    if risk_factors:
        print(f"\n  Top Risk Factors:")
        for rf in risk_factors[:4]:
            icon = "⚠️ " if rf["severity"] == "high" else "ℹ️ "
            print(f"    {icon} [{rf['severity'].upper()}] {rf['message']}")

    print(f"\n{'─'*70}")
    print("  AI ANALYSIS EXCERPT (IBM Granite)")
    print(f"{'─'*70}")
    analysis = result_dict.get("ai_analysis", {}).get("analysis_text", "")
    if analysis:
        # Print first 800 chars
        excerpt = analysis[:800] + "..." if len(analysis) > 800 else analysis
        for line in excerpt.split("\n")[:20]:
            print(f"  {line}")

    print(f"\n{'─'*70}")
    workflow = result_dict.get("steps", [])
    completed = sum(1 for s in workflow if s["status"] == "completed")
    failed = sum(1 for s in workflow if s["status"] == "failed")
    duration = result_dict.get("total_duration_seconds", 0)
    print(f"  Workflow: {completed}/10 steps completed, {failed} failed | Total: {duration:.1f}s")
    print("═" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Investment Analyst CLI")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL)")
    parser.add_argument("--json", action="store_true", help="Output full JSON result")
    parser.add_argument("--output", help="Save JSON result to file")
    args = parser.parse_args()

    agent = InvestmentAnalystAgent()
    print(f"\n🔍 Running investment analysis for {args.ticker.upper()}...")
    result = agent.analyze(args.ticker)
    result_dict = agent.to_dict(result)

    if args.json:
        print(json.dumps(result_dict, indent=2, default=str))
    else:
        print_summary(result_dict)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(result_dict, f, indent=2, default=str)
        print(f"✅ Full results saved to: {args.output}")


if __name__ == "__main__":
    main()

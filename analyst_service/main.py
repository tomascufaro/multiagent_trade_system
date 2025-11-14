"""Analyst Service - Main entry point for analysis-only report."""
import sys
import os

# Add project root and shared directory to path for direct script execution
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, "shared"))

from analyst_service.analysis.analyst_service import AnalystService
from shared.formatting import setup_logger

logger = setup_logger("analyst_service")


def main():
    """Run a portfolio-level analysis and print a concise report."""
    analyst = AnalystService()

    logger.info("Starting portfolio analysis")

    try:
        analysis = analyst.analyze_portfolio()

        portfolio = analysis.get("portfolio") or {}
        debate = analysis.get("debate") or {}

        print("\n=== Portfolio Analyst Report ===")
        print(f"Timestamp: {analysis['timestamp']}")
        print(f"Equity: {portfolio.get('equity', 'N/A')}")
        print(f"Cash: {portfolio.get('cash', 'N/A')}")
        positions = portfolio.get("positions") or []
        print(f"Open Positions: {len(positions)}")

        if debate:
            print("\nDebate Results:")
            print(f"  Market Bias: {debate.get('market_bias', 'N/A')}")
            print(f"  Summary: {debate.get('summary', 'N/A')}")

        logger.info("Portfolio analysis completed")

    except Exception as exc:
        logger.error(f"Error in analysis: {str(exc)}")
        raise


if __name__ == "__main__":
    main()

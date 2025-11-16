"""AnalystService - Simple, analysis-only orchestrator.

Supports both symbol-level and portfolio-level analysis flows.
"""
from datetime import datetime
from typing import Any, Dict, List
import logging

from data_module.data_manager import DataManager

from .ta_signals import TechnicalAnalysis
from .report_writer import ReportWriter
from ..agents.debate_manager import DebateManager
from ..data_context import build_analysis_context, format_portfolio_context_for_prompt


class AnalystService:
    def __init__(self, config_path: str = "analyst_service/config/settings.yaml"):
        self.data_manager = DataManager(config_path)
        self.ta_signals = TechnicalAnalysis(config_path)
        self.debate_manager = DebateManager(config_path)
        self.report_writer = ReportWriter()

    def analyze(self, symbol: str) -> Dict[str, Any]:
        """Run analysis for a single symbol using DB context, TA, and agent debate."""
        market_data = self.data_manager.get_market_data(symbol)

        historical = market_data.get("historical_data") or []
        prices: List[float] = [bar["close"] for bar in historical if "close" in bar]

        context = build_analysis_context(symbol)

        ta_data: Dict[str, Any] = {}
        if prices:
            ta_data = self.ta_signals.get_signals(prices)

        # No external sentiment in this minimal pipeline; agents use context/news
        sentiment_data: Dict[str, Any] = {}

        debate = self.debate_manager.conduct_debate(symbol, prices, sentiment_data)

        return {
            "symbol": symbol,
            "context": context,
            "ta_signals": ta_data,
            "debate": debate,
            "summary": debate.get("summary", ""),
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_portfolio(self) -> Dict[str, Any]:
        """Run a portfolio-level analysis and debate."""
        portfolio = self.data_manager.get_portfolio_summary() or {}
        positions = portfolio.get("positions") or []
        tracking_symbols = sorted(self.data_manager.get_all_tracking_symbols() or [])

        # Collect recent news for symbols we hold or track
        news_by_symbol: Dict[str, List[Dict[str, Any]]] = {}
        all_symbols = {pos.get("symbol") for pos in positions if pos.get("symbol")} | set(
            tracking_symbols
        )
        for symbol in all_symbols:
            news_by_symbol[symbol] = self.data_manager.get_news_for_symbol(symbol, limit=5) or []

        context_dict = {
            "portfolio": portfolio,
            "positions": positions,
            "tracking_symbols": tracking_symbols,
            "news_by_symbol": news_by_symbol,
            "timestamp": datetime.now().isoformat(),
        }

        context_text = format_portfolio_context_for_prompt(context_dict)

        debate = self.debate_manager.conduct_portfolio_debate(context_text)

        # Use the report writer agent to build the final narrative report
        report = self.report_writer.write_portfolio_report(context_text, debate)

        # Log the detailed report so the debate can be inspected later
        logger = logging.getLogger("analyst_service")
        logger.info("Portfolio debate detailed report:\n%s", report)

        return {
            "portfolio": portfolio,
            "universe": tracking_symbols,
            "context": context_dict,
            "debate": debate,
            "summary": debate.get("summary", ""),
            "report": report,
            "timestamp": datetime.now().isoformat(),
        }

    # _build_portfolio_report is no longer used; kept as a possible fallback helper if needed.

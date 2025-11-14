from typing import Dict, Any, List
import sys
import os

from crewai import Crew, Process

from .trading_crew import TradingCrew
from .bull_agent import BullAgent
from .bear_agent import BearAgent

# Add shared directory to path for models
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
from models import MarketAnalysis, AgentAnalysis

from data_module.data_manager import DataManager


class DebateManager:
    def __init__(self, config_path: str = "analyst_service/config/settings.yaml"):
        """Initialize the debate manager with CrewAI trading crew."""
        self.trading_crew = TradingCrew(config_path)

    def conduct_debate(
        self, symbol: str, prices: List[float], sentiment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Conduct a CrewAI-powered debate between bull and bear agents for a single symbol.

        Args:
            symbol: Trading symbol under analysis
            prices: Historical prices for technical analysis
            sentiment_data: Sentiment analysis data

        Returns:
            Dictionary containing collaborative analysis results
        """
        return self.trading_crew.conduct_analysis(symbol, prices, sentiment_data)

    def conduct_portfolio_debate(self, context_text: str) -> Dict[str, Any]:
        """
        Conduct a portfolio-level CrewAI debate between bull and bear agents.

        Args:
            context_text: Formatted portfolio context block for the agents.

        Returns:
            Dictionary containing both perspectives and overall portfolio bias.
        """
        bull_agent = BullAgent()
        bear_agent = BearAgent()

        bull_task = bull_agent.create_portfolio_task(context_text)
        bear_task = bear_agent.create_portfolio_task(context_text)

        crew = Crew(
            agents=[bull_agent.agent, bear_agent.agent],
            tasks=[bull_task, bear_task],
            process=Process.sequential,
            verbose=True,
        )

        results = crew.kickoff()

        try:
            bull_result = results.tasks_output[0].pydantic
            bear_result = results.tasks_output[1].pydantic

            if not isinstance(bull_result, AgentAnalysis) or not isinstance(
                bear_result, AgentAnalysis
            ):
                bull_result = AgentAnalysis.parse_raw(str(results.tasks_output[0]))
                bear_result = AgentAnalysis.parse_raw(str(results.tasks_output[1]))

        except Exception as exc:
            raise RuntimeError(f"Failed to parse portfolio CrewAI results: {exc}")

        market_bias = bull_result.conviction - bear_result.conviction

        return MarketAnalysis(
            bull_case=bull_result,
            bear_case=bear_result,
            market_bias=market_bias,
            summary=(
                f"Portfolio debate bias is "
                f"{'bullish' if market_bias > 0 else 'bearish' if market_bias < 0 else 'neutral'} "
                f"with bull conviction {bull_result.conviction:.2f} "
                f"and bear conviction {bear_result.conviction:.2f}."
            ),
            crew_analysis=True,
        ).dict()


def main():
    """CLI entry point to test the symbol-level debate workflow directly."""
    # Ensure project root is on the path when executed as a script
    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )

    symbol = sys.argv[1] if len(sys.argv) > 1 else "AAPL"

    data_manager = DataManager()
    market_data = data_manager.get_market_data(symbol)
    historical = market_data.get("historical_data") or []
    prices = [bar["close"] for bar in historical if "close" in bar]

    # Minimal sentiment stub; agents mainly use DB context/news
    sentiment_data: Dict[str, Any] = {}

    debate_manager = DebateManager()
    result = debate_manager.conduct_debate(symbol, prices, sentiment_data)

    print(f"\n=== Debate Results for {symbol} ===")
    print(f"Market Bias: {result.get('market_bias')}")
    print(f"Summary: {result.get('summary')}")
    print("\nBull Case:", result.get("bull_case"))
    print("\nBear Case:", result.get("bear_case"))


if __name__ == "__main__":
    main()

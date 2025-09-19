from typing import Dict, Any, List
from .trading_crew import TradingCrew

class DebateManager:
    def __init__(self, config_path: str = None):
        """Initialize the debate manager with CrewAI trading crew."""
        self.trading_crew = TradingCrew()

    def conduct_debate(self, prices: List[float], sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct a CrewAI-powered debate between bull and bear agents.
        
        Args:
            prices: Historical prices for technical analysis
            sentiment_data: Sentiment analysis data
            
        Returns:
            Dictionary containing collaborative analysis results
        """
        return self.trading_crew.conduct_analysis(prices, sentiment_data)

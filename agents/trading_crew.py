from typing import Dict, Any, List
import json
from crewai import Crew, Process
from .bull_agent import BullAgent
from .bear_agent import BearAgent

class TradingCrew:
    def __init__(self):
        """Initialize the trading crew with bull and bear agents."""
        self.bull_agent = BullAgent()
        self.bear_agent = BearAgent()
        
        # Create the crew with both agents
        self.crew = Crew(
            agents=[self.bull_agent.agent, self.bear_agent.agent],
            tasks=[],  # Tasks will be added dynamically
            process=Process.sequential,
            verbose=True
        )

    def conduct_analysis(self, prices: List[float], sentiment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct a collaborative analysis between bull and bear agents.
        
        Args:
            prices: List of historical prices for technical analysis
            sentiment_data: Dictionary containing sentiment analysis data
            
        Returns:
            Dictionary containing both perspectives and overall market bias
        """
        # Create tasks for both agents
        bull_task = self.bull_agent.create_analysis_task(prices, sentiment_data)
        bear_task = self.bear_agent.create_analysis_task(prices, sentiment_data)
        
        # Update crew tasks
        self.crew.tasks = [bull_task, bear_task]
        
        # Execute the crew
        results = self.crew.kickoff()
        
        # Parse results
        try:
            # Results should be a list of task outputs
            bull_result = json.loads(str(results.tasks_output[0]))
            bear_result = json.loads(str(results.tasks_output[1]))
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            raise RuntimeError(f"Failed to parse CrewAI results: {e}")  
        
        # Calculate market bias
        bull_conviction = bull_result.get('conviction', 0.0)
        bear_conviction = bear_result.get('conviction', 0.0)
        market_bias = bull_conviction - bear_conviction
        
        return {
            'bull_case': {
                'arguments': bull_result.get('arguments', []),
                'conviction': bull_conviction,
                'recommendation': bull_result.get('recommendation', 'HOLD')
            },
            'bear_case': {
                'arguments': bear_result.get('arguments', []),
                'conviction': bear_conviction,
                'recommendation': bear_result.get('recommendation', 'HOLD')
            },
            'market_bias': market_bias,
            'summary': self._generate_summary(bull_result, bear_result, market_bias),
            'crew_analysis': True  # Flag to indicate this used CrewAI
        }
    
    def _generate_summary(self, bull_analysis: Dict[str, Any], 
                         bear_analysis: Dict[str, Any], 
                         market_bias: float) -> str:
        """Generate a summary of the crew analysis."""
        if market_bias > 0.3:
            bias = "strongly bullish"
        elif market_bias > 0:
            bias = "slightly bullish"
        elif market_bias < -0.3:
            bias = "strongly bearish"
        elif market_bias < 0:
            bias = "slightly bearish"
        else:
            bias = "neutral"

        bull_conviction = bull_analysis.get('conviction', 0.0)
        bear_conviction = bear_analysis.get('conviction', 0.0)
        
        return f"CrewAI analysis shows market bias is {bias} with bull conviction at {bull_conviction:.2f} " \
               f"and bear conviction at {bear_conviction:.2f}"
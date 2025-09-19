from typing import Dict, Any, List
import json
import sys
import os
from crewai import Crew, Process
from .bull_agent import BullAgent
from .bear_agent import BearAgent

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from models import MarketAnalysis, AgentAnalysis

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
        
        # Parse results - CrewAI returns Pydantic objects when output_pydantic is used
        try:
            bull_result = results.tasks_output[0].pydantic
            bear_result = results.tasks_output[1].pydantic
            
            if not isinstance(bull_result, AgentAnalysis) or not isinstance(bear_result, AgentAnalysis):
                # Fallback to JSON parsing if Pydantic parsing fails
                bull_result = AgentAnalysis.parse_raw(str(results.tasks_output[0]))
                bear_result = AgentAnalysis.parse_raw(str(results.tasks_output[1]))
                
        except Exception as e:
            raise RuntimeError(f"Failed to parse CrewAI results: {e}")  
        
        # Calculate market bias
        market_bias = bull_result.conviction - bear_result.conviction
        
        return MarketAnalysis(
            bull_case=bull_result,
            bear_case=bear_result,
            market_bias=market_bias,
            summary=self._generate_summary(bull_result, bear_result, market_bias),
            crew_analysis=True
        ).dict()
    
    def _generate_summary(self, bull_analysis: AgentAnalysis, 
                         bear_analysis: AgentAnalysis, 
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

        return f"CrewAI analysis shows market bias is {bias} with bull conviction at {bull_analysis.conviction:.2f} " \
               f"and bear conviction at {bear_analysis.conviction:.2f}"
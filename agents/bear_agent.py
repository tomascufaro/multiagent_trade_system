from typing import Dict, Any
import yaml
import json
from crewai import Agent, Task
from crewai.tools import tool
import sys
import os

# Add the features directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'features'))
from ta_signals import TechnicalAnalysis

@tool("get_technical_signals")
def get_technical_signals(prices: str) -> str:
    """
    Get technical analysis signals from price data.
    
    Args:
        prices: JSON string of price list
    
    Returns:
        JSON string containing RSI, MACD, and EMA signals
    """
    try:
        price_list = json.loads(prices)
        ta = TechnicalAnalysis()
        signals = ta.get_signals(price_list)
        return json.dumps(signals)
    except Exception as e:
        return json.dumps({"error": str(e)})

class BearAgent:
    def __init__(self):
        self.agent = Agent(
            role="Bearish Market Analyst",
            goal="Analyze market data to identify bearish signals and build strong cases for selling",
            backstory="""You are a cautious market analyst who specializes in finding bearish signals 
            in technical indicators and market sentiment. You excel at identifying overbought conditions, 
            negative momentum shifts, and bearish sentiment that could lead to profitable short positions.
            You use technical analysis tools like RSI, MACD, and EMA to support your bearish thesis.""",
            tools=[get_technical_signals],
            verbose=True,
            allow_delegation=False,
            max_iter=10
        )

    def create_analysis_task(self, prices: list, sentiment_data: Dict[str, Any]) -> Task:
        """Create a CrewAI task for bear analysis."""
        
        return Task(
            description=f"""Analyze the provided price data and sentiment to build a comprehensive bearish case.
            
            Price Data: {json.dumps(prices)}
            Sentiment Data: {json.dumps(sentiment_data)}
            
            Steps:
            1. Use the get_technical_signals tool with the price data to get RSI, MACD, and EMA signals
            2. Analyze the technical signals for bearish indicators:
               - RSI > 70 (overbought conditions)
               - MACD histogram < 0 and MACD < signal (bearish momentum)
               - EMA crossover < 0 (bearish crossover)
            3. Incorporate sentiment data if negative
            4. Calculate conviction level (0.0 to 1.0) based on signal strength
            5. Provide SELL recommendation if conviction > 0.5, otherwise HOLD
            
            Return a JSON with: arguments (list), conviction (float), recommendation (string)""",
            agent=self.agent,
            expected_output="JSON formatted analysis with bearish arguments, conviction level, and recommendation"
        )


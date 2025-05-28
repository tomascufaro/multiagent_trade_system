from typing import Dict, Any
import yaml
import json
from crewai import Agent, Task
from crewai.tools import tool
import sys
import os

# Add utils directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'utils'))
from models import AgentAnalysis

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
        raise Exception(f"Technical analysis failed: {str(e)}")

class BullAgent:
    def __init__(self):
        self.agent = Agent(
            role="Bullish Market Analyst",
            goal="Analyze market data to identify bullish opportunities and build strong cases for buying",
            backstory="""You are an optimistic market analyst who specializes in finding bullish signals 
            in technical indicators and market sentiment. You excel at identifying oversold conditions, 
            positive momentum shifts, and bullish sentiment that could lead to profitable long positions.
            You use technical analysis tools like RSI, MACD, and EMA to support your bullish thesis.""",
            tools=[get_technical_signals],
            verbose=True,
            allow_delegation=False,
            max_iter=5,
            llm="gpt-4.1-nano"
        )

    def create_analysis_task(self, prices: list, sentiment_data: Dict[str, Any]) -> Task:
        """Create a CrewAI task for bull analysis."""
        
        return Task(
            description=f"""Analyze the provided price data and sentiment to build a comprehensive bullish case.
            
            Price Data: {json.dumps(prices)}
            Sentiment Data: {json.dumps(sentiment_data)}
            
            Steps:
            1. Use the get_technical_signals tool with the price data to get RSI, MACD, and EMA signals
            2. Analyze the technical signals for bullish indicators:
               - RSI < 30 (oversold conditions)
               - MACD histogram > 0 and MACD > signal (bullish momentum)
               - EMA crossover > 0 (bullish crossover)
            3. Incorporate sentiment data if positive
            4. Calculate conviction level (0.0 to 1.0) based on signal strength
            5. Provide BUY recommendation if conviction > 0.5, otherwise HOLD
            
            Return ONLY valid JSON with: arguments (list), conviction (float), recommendation (string)""",
            agent=self.agent,
            expected_output="JSON formatted analysis with bullish arguments, conviction level, and recommendation",
            output_pydantic=AgentAnalysis
        )


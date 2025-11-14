from typing import Dict, Any
import yaml
import json
from crewai import Agent, Task
from crewai.tools import tool
import sys
import os

# Add shared directory to path for pydantic models
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from models import AgentAnalysis

# Import technical analysis from analysis module
from ..analysis.ta_signals import TechnicalAnalysis
from ..data_context import format_context_for_prompt

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
            max_iter=5,
            llm="gpt-4.1-nano"
        )

    def create_analysis_task(self, prices: list, sentiment_data: Dict[str, Any], db_context: Dict[str, Any]) -> Task:
        """Create a CrewAI task for symbol-level bear analysis."""
        formatted_context = format_context_for_prompt(db_context)
        return Task(
            description=f"""Analyze the provided price data and sentiment to build a comprehensive bearish case.
            
            Price Data: {json.dumps(prices)}
            Sentiment Data: {json.dumps(sentiment_data)}
            
            === DATABASE CONTEXT ===
            {formatted_context}
            
            Steps:
            1. Use the get_technical_signals tool with the price data to get RSI, MACD, and EMA signals
            2. Analyze the technical signals for bearish indicators:
               - RSI > 70 (overbought conditions)
               - MACD histogram < 0 and MACD < signal (bearish momentum)
               - EMA crossover < 0 (bearish crossover)
            3. Incorporate sentiment data if negative
            4. Incorporate database context:
               - Consider current {db_context.get('symbol', 'SYMBOL')} position performance if any
               - Use portfolio drawdowns to calibrate caution
               - Weigh negative news impact if notable
            5. Calculate conviction level (0.0 to 1.0) based on signal strength and context
            6. Provide SELL recommendation if conviction > 0.5, otherwise HOLD
            
            Return ONLY valid JSON with: arguments (list), conviction (float), recommendation (string)""",
            agent=self.agent,
            expected_output="JSON formatted analysis with bearish arguments, conviction level, and recommendation",
            output_pydantic=AgentAnalysis
        )

    def create_portfolio_task(self, context_text: str) -> Task:
        """Create a CrewAI task for portfolio-level bear analysis."""
        return Task(
            description=f"""You are a bearish portfolio risk manager.

Analyze the following portfolio context and build a cautious, risk-focused bearish case
for how the investor should think about their overall portfolio and wishlist.

=== PORTFOLIO CONTEXT ===
{context_text}

Focus on:
- Where the portfolio may be overexposed or concentrated
- Which existing positions look vulnerable or stretched
- Which wishlist/tracked symbols should be avoided or treated carefully
- How portfolio drawdowns, volatility, and correlations impact risk

Return ONLY valid JSON with: arguments (list), conviction (float), recommendation (string).
Recommendation is a high-level stance such as SELL, HOLD, or BUY to indicate overall risk posture.""",
            agent=self.agent,
            expected_output="JSON formatted portfolio-level bearish arguments, conviction level, and stance recommendation",
            output_pydantic=AgentAnalysis,
        )

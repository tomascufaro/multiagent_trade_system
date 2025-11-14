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

    def create_analysis_task(self, prices: list, sentiment_data: Dict[str, Any], db_context: Dict[str, Any]) -> Task:
        """Create a CrewAI task for symbol-level bull analysis."""
        formatted_context = format_context_for_prompt(db_context)
        return Task(
            description=f"""Analyze the provided price data and sentiment to build a comprehensive bullish case.
            
            Price Data: {json.dumps(prices)}
            Sentiment Data: {json.dumps(sentiment_data)}
            
            === DATABASE CONTEXT ===
            {formatted_context}
            
            Steps:
            1. Use the get_technical_signals tool with the price data to get RSI, MACD, and EMA signals
            2. Analyze the technical signals for bullish indicators:
               - RSI < 30 (oversold conditions)
               - MACD histogram > 0 and MACD > signal (bullish momentum)
               - EMA crossover > 0 (bullish crossover)
            3. Incorporate sentiment data if positive
            4. Incorporate database context:
               - Consider current {db_context.get('symbol', 'SYMBOL')} position performance if any
               - Use portfolio performance metrics to calibrate conviction
               - Weigh recent news impact if notable
            5. Calculate conviction level (0.0 to 1.0) based on signal strength and context
            6. Provide BUY recommendation if conviction > 0.5, otherwise HOLD
            
            Return ONLY valid JSON with: arguments (list), conviction (float), recommendation (string)""",
            agent=self.agent,
            expected_output="JSON formatted analysis with bullish arguments, conviction level, and recommendation",
            output_pydantic=AgentAnalysis
        )

    def create_portfolio_task(self, context_text: str) -> Task:
        """Create a CrewAI task for portfolio-level bull analysis."""
        return Task(
            description=f"""You are a bullish portfolio strategist.

Analyze the following portfolio context and build a constructive, risk-aware bullish case
for how the investor should think about their overall portfolio and wishlist.

=== PORTFOLIO CONTEXT ===
{context_text}

Focus on:
- Where the portfolio could lean in more aggressively (symbols, sectors, themes)
- Which existing positions look attractive to hold or increase
- Which wishlist/tracked symbols look compelling to consider
- How portfolio risk and diversification look from a bullish perspective

Return ONLY valid JSON with: arguments (list), conviction (float), recommendation (string).
Recommendation is a high-level stance such as BUY, HOLD, or SELL to indicate overall risk posture.""",
            agent=self.agent,
            expected_output="JSON formatted portfolio-level bullish arguments, conviction level, and stance recommendation",
            output_pydantic=AgentAnalysis,
        )

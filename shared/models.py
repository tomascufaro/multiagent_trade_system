from pydantic import BaseModel, Field
from typing import List
from enum import Enum


class Recommendation(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class AgentAnalysis(BaseModel):
    """Structured output for bull/bear agent analysis."""
    arguments: List[str] = Field(description="List of arguments supporting the analysis")
    conviction: float = Field(ge=0.0, le=1.0, description="Conviction level between 0.0 and 1.0")
    recommendation: Recommendation = Field(description="Trading recommendation")


class MarketAnalysis(BaseModel):
    """Structured output for complete market analysis."""
    bull_case: AgentAnalysis = Field(description="Bullish analysis")
    bear_case: AgentAnalysis = Field(description="Bearish analysis")
    market_bias: float = Field(ge=-1.0, le=1.0, description="Market bias between -1.0 and 1.0")
    summary: str = Field(description="Summary of the analysis")
    crew_analysis: bool = Field(default=True, description="Flag indicating CrewAI analysis")
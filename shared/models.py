from typing import List

from pydantic import BaseModel, Field


class AgentAnalysis(BaseModel):
    """Structured output for an individual agent's recommendation."""

    arguments: List[str] = Field(default_factory=list)
    conviction: float = 0.0
    recommendation: str = "HOLD"


class MarketAnalysis(BaseModel):
    """Aggregated market view derived from bull and bear agents."""

    bull_case: AgentAnalysis
    bear_case: AgentAnalysis
    market_bias: float
    summary: str
    crew_analysis: bool = False

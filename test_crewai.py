#!/usr/bin/env python3
"""
Test script for CrewAI-only trading bot agents.
"""
import sys
import os
from typing import List

# Add the current directory to Python path
sys.path.append(os.path.dirname(__file__))

from agents.debate_manager import DebateManager
from agents.decision_manager import DecisionManager
from utils.data_saver import save_data, load_latest_data


def test_crewai_integration():
    """Test the CrewAI-only trading crew system."""
    print("Testing CrewAI-Only Trading System...")

    # Try to load data from ingestion modules, fallback to sample data
    price_data = load_latest_data("price_feed")
    news_data = load_latest_data("news_feed")

    if price_data and price_data.get("historical_data"):
        sample_prices = [bar["close"] for bar in price_data["historical_data"][:10]]
        print(f"Using saved price data: {len(sample_prices)} prices")
    else:
        sample_prices = [150.0, 152.5, 151.0, 148.0, 147.5, 149.0, 150.5, 153.0, 154.5, 152.0]
        print("Using sample price data")

    if news_data and news_data.get("general_news"):
        sample_sentiment = {
            "sentiment": "bullish",
            "confidence": 0.8,
            "summary": f"Analysis from {len(news_data['general_news'])} recent articles",
        }
        print(f"Using saved news data: {len(news_data['general_news'])} articles")
    else:
        sample_sentiment = {
            "sentiment": "bullish",
            "confidence": 0.8,
            "summary": "Sample positive sentiment",
        }
        print("Using sample sentiment data")

    try:
        # Test 1: DebateManager (CrewAI-only)
        print("\n1. Testing DebateManager...")
        debate_manager = DebateManager()
        crew_result = debate_manager.conduct_debate(sample_prices, sample_sentiment)

        print(f"Market Bias: {crew_result['market_bias']:.2f}")
        print(f"Summary: {crew_result['summary']}")
        print(f"Used CrewAI: {crew_result.get('crew_analysis', True)}")

        # Test 2: Full DecisionManager
        print("\n2. Testing DecisionManager...")
        decision_manager = DecisionManager()
        decision = decision_manager.make_decision(sample_prices, sample_sentiment)

        print(f"Action: {decision['action']}")
        print(f"Confidence: {decision['confidence']:.2f}")
        print(f"Reason: {decision['reason']}")
        print(f"Market Bias: {decision['debate_results']['market_bias']:.2f}")

        # Save test results
        test_results = {
            "debate_result": crew_result,
            "decision_result": decision,
        }
        filepath = save_data("crewai_test", test_results)
        print(f"\nTest results saved to: {filepath}")

    except Exception as e:
        print(f"Error in CrewAI testing: {e}")


if __name__ == "__main__":
    test_crewai_integration()

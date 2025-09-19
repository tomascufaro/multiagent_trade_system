"""
Analyst Service - Main entry point for market analysis
"""
import sys
import os
from datetime import datetime

# Add shared directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

from analysis.market_analyzer import MarketAnalyzer
from shared.formatting import setup_logger

logger = setup_logger('analyst_service')

def main():
    """Main function for analyst service"""
    analyzer = MarketAnalyzer()
    
    # Analyze a symbol
    symbol = "AAPL"
    logger.info(f"Starting analysis for {symbol}")
    
    try:
        analysis = analyzer.analyze_symbol(symbol)
        
        # Print results
        print(f"\n=== Market Analysis for {symbol} ===")
        print(f"Current Price: ${analysis['market_data']['current_price']}")
        print(f"Position: {analysis['position_data'] or 'No position'}")
        print(f"Recommendation: {analysis['recommendation']['action']}")
        print(f"Confidence: {analysis['recommendation']['confidence']:.2f}")
        print(f"Reason: {analysis['recommendation']['reason']}")
        print(f"Position Context: {analysis['recommendation']['position_context']}")
        
        # Print sentiment summary
        if analysis['sentiment_analysis']:
            print(f"\nSentiment: {analysis['sentiment_analysis'].get('overall_sentiment', 'N/A')}")
            print(f"Confidence: {analysis['sentiment_analysis'].get('confidence', 'N/A')}")
        
        # Print technical analysis summary
        if analysis['technical_analysis']:
            print(f"\nTechnical Analysis:")
            for signal, value in analysis['technical_analysis'].items():
                if isinstance(value, dict) and 'signal' in value:
                    print(f"  {signal}: {value['signal']}")
        
        # Print debate results
        if analysis['debate_results']:
            print(f"\nDebate Results:")
            print(f"  Market Bias: {analysis['debate_results'].get('market_bias', 'N/A')}")
            print(f"  Summary: {analysis['debate_results'].get('summary', 'N/A')}")
        
        logger.info(f"Analysis completed for {symbol}")
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        raise

if __name__ == "__main__":
    main()

"""
Market Analyzer - Main orchestrator for market analysis
"""
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from models import MarketAnalysis, AgentAnalysis

from .sentiment_agent import SentimentAgent
from .ta_signals import TechnicalAnalysis
from ..agents.debate_manager import DebateManager
from data_module.data_manager import DataManager

class MarketAnalyzer:
    def __init__(self, config_path='analyst_service/config/settings.yaml'):
        self.data_manager = DataManager(config_path)
        self.sentiment_agent = SentimentAgent(config_path)
        self.ta_signals = TechnicalAnalysis(config_path)
        self.debate_manager = DebateManager(config_path)
    
    def analyze_symbol(self, symbol: str):
        """
        Complete market analysis for a symbol with position context
        """
        # Get all data
        market_data = self.data_manager.get_market_data(symbol)
        position_data = self.data_manager.get_position(symbol)
        portfolio_data = self.data_manager.get_portfolio_summary()
        
        # Extract prices for analysis
        prices = [d['close'] for d in market_data['historical_data']] if market_data['historical_data'] else []
        
        # Analyze sentiment
        sentiment_data = self.sentiment_agent.analyze_news(market_data['news_data'])
        
        # Get technical analysis
        ta_data = self.ta_signals.analyze(prices)
        
        # Conduct debate analysis
        debate_results = self.debate_manager.conduct_debate(prices, sentiment_data)
        
        # Generate position-aware recommendation
        recommendation = self._generate_recommendation(
            market_data, position_data, portfolio_data, 
            sentiment_data, ta_data, debate_results
        )
        
        return {
            'symbol': symbol,
            'market_data': market_data,
            'position_data': position_data,
            'portfolio_data': portfolio_data,
            'sentiment_analysis': sentiment_data,
            'technical_analysis': ta_data,
            'debate_results': debate_results,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_recommendation(self, market_data, position_data, portfolio_data, 
                                sentiment_data, ta_data, debate_results):
        """Generate position-aware trading recommendation"""
        market_bias = debate_results.get('market_bias', 0)
        
        # Default recommendation
        recommendation = {
            'action': 'HOLD',
            'confidence': 0,
            'reason': 'Insufficient conviction for trade',
            'position_context': 'No position analysis available'
        }
        
        # Position-aware logic
        if position_data:
            # We have a position - analyze exit/hedge opportunities
            if position_data['side'] == 'LONG':
                if market_bias < -0.2:
                    recommendation = {
                        'action': 'CLOSE_LONG',
                        'confidence': abs(market_bias),
                        'reason': 'Bearish signals suggest closing long position',
                        'position_context': f"Long position: {position_data['qty']} @ {position_data['avg_entry_price']}"
                    }
            elif position_data['side'] == 'SHORT':
                if market_bias > 0.2:
                    recommendation = {
                        'action': 'CLOSE_SHORT',
                        'confidence': market_bias,
                        'reason': 'Bullish signals suggest closing short position',
                        'position_context': f"Short position: {position_data['qty']} @ {position_data['avg_entry_price']}"
                    }
        else:
            # No position - analyze entry opportunities
            if abs(market_bias) > 0.3:
                if market_bias > 0:
                    recommendation = {
                        'action': 'BUY',
                        'confidence': market_bias,
                        'reason': 'Strong bullish conviction',
                        'position_context': 'No current position'
                    }
                else:
                    recommendation = {
                        'action': 'SELL',
                        'confidence': abs(market_bias),
                        'reason': 'Strong bearish conviction',
                        'position_context': 'No current position'
                    }
        
        return recommendation

from typing import Dict, Any, List
import yaml
from .debate_manager import DebateManager

class DecisionManager:
    def __init__(self, config_path: str = 'config/settings.yaml'):
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.debate_manager = DebateManager(config_path)

    def make_decision(self, 
                     prices: List[float], 
                     sentiment_data: Dict[str, Any],
                     current_position: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a final trading decision based on CrewAI debate results and current position.
        """
        # Get CrewAI debate results
        debate_results = self.debate_manager.conduct_debate(prices, sentiment_data)
        
        # Default decision
        decision = {
            'action': 'HOLD',
            'confidence': 0,
            'reason': 'Insufficient conviction for trade',
            'debate_summary': debate_results['summary']
        }

        market_bias = debate_results['market_bias']
        
        # Decision logic
        if abs(market_bias) > 0.3:  # Strong conviction threshold
            if market_bias > 0:
                decision['action'] = 'BUY'
                decision['confidence'] = market_bias
                decision['reason'] = 'Strong bullish conviction'
            else:
                decision['action'] = 'SELL'
                decision['confidence'] = abs(market_bias)
                decision['reason'] = 'Strong bearish conviction'

        # Position management logic
        if current_position:
            if current_position['side'] == 'LONG':
                if market_bias < -0.2:
                    decision['action'] = 'CLOSE'
                    decision['reason'] = 'Closing long position due to bearish signals'
            elif current_position['side'] == 'SHORT':
                if market_bias > 0.2:
                    decision['action'] = 'CLOSE'
                    decision['reason'] = 'Closing short position due to bullish signals'

        return {
            **decision,
            'prices': prices,
            'sentiment_data': sentiment_data,
            'debate_results': debate_results
        }

import json
from datetime import datetime
from typing import Dict, Any
import yaml
import os

class MockTrader:
    def __init__(self, config_path: str = '../config/settings.yaml'):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            self.initial_capital = config['trading']['initial_capital']
        
        self.portfolio = {
            'cash': self.initial_capital,
            'positions': {},
            'total_value': self.initial_capital,
            'trades': []
        }
        
        # Create trades directory if it doesn't exist
        os.makedirs('trades', exist_ok=True)

    def execute_trade(self, 
                     trade_decision: Dict[str, Any], 
                     symbol: str, 
                     current_price: float) -> Dict[str, Any]:
        """
        Execute a mock trade based on the decision.
        """
        if trade_decision['action'] == 'HOLD':
            return {'status': 'no_action', 'message': 'Holding position'}

        trade_result = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': trade_decision['action'],
            'price': current_price,
            'size': 0,
            'value': 0,
            'reason': trade_decision['reason']
        }

        if trade_decision['action'] in ['BUY', 'SELL']:
            # Calculate trade size based on available cash
            max_size = self.portfolio['cash'] / current_price
            trade_size = min(max_size, trade_decision.get('size', max_size))
            
            trade_result['size'] = trade_size
            trade_result['value'] = trade_size * current_price

            # Update portfolio
            if trade_decision['action'] == 'BUY':
                self.portfolio['cash'] -= trade_result['value']
                self.portfolio['positions'][symbol] = {
                    'side': 'LONG',
                    'size': trade_size,
                    'entry_price': current_price
                }
            else:  # SELL
                self.portfolio['cash'] += trade_result['value']
                self.portfolio['positions'][symbol] = {
                    'side': 'SHORT',
                    'size': trade_size,
                    'entry_price': current_price
                }

        elif trade_decision['action'] == 'CLOSE':
            if symbol in self.portfolio['positions']:
                position = self.portfolio['positions'][symbol]
                trade_result['size'] = position['size']
                trade_result['value'] = position['size'] * current_price
                
                if position['side'] == 'LONG':
                    self.portfolio['cash'] += trade_result['value']
                else:  # SHORT
                    self.portfolio['cash'] -= trade_result['value']
                
                del self.portfolio['positions'][symbol]

        # Record trade
        self.portfolio['trades'].append(trade_result)
        self._save_trade(trade_result)
        
        # Update portfolio value
        self._update_portfolio_value(current_price)
        
        return trade_result

    def _update_portfolio_value(self, current_price: float):
        """Update the total portfolio value."""
        position_value = sum(
            pos['size'] * current_price 
            for pos in self.portfolio['positions'].values()
        )
        self.portfolio['total_value'] = self.portfolio['cash'] + position_value

    def _save_trade(self, trade: Dict[str, Any]):
        """Save trade to a JSON file."""
        filename = f"trades/trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(trade, f, indent=2)

    def get_portfolio_status(self) -> Dict[str, Any]:
        """Get current portfolio status."""
        return {
            'total_value': self.portfolio['total_value'],
            'cash': self.portfolio['cash'],
            'positions': self.portfolio['positions'],
            'returns': (self.portfolio['total_value'] - self.initial_capital) 
                      / self.initial_capital,
            'trade_count': len(self.portfolio['trades'])
        }

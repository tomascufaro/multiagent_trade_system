from typing import Dict, Any
import yaml

class CapitalAllocator:
    def __init__(self, config_path: str = '../config/settings.yaml'):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            self.initial_capital = config['trading']['initial_capital']
            self.risk_per_trade = config['trading']['risk_per_trade']
            self.max_position_size = config['trading']['max_position_size']

    def calculate_trade_size(self, 
                           available_capital: float, 
                           current_positions: Dict[str, Any]) -> float:
        """
        Calculate the appropriate trade size based on available capital
        and current positions.
        """
        # Calculate total exposure from current positions
        total_exposure = sum(pos['size'] * pos['entry_price'] 
                           for pos in current_positions.values())

        # Calculate remaining capital available for new positions
        remaining_capital = available_capital - total_exposure

        # Calculate maximum trade size based on risk per trade
        max_trade_size = min(
            remaining_capital * self.risk_per_trade,
            self.max_position_size
        )

        return max_trade_size

    def validate_portfolio_risk(self, 
                              portfolio: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate overall portfolio risk levels.
        """
        validation = {
            'within_limits': True,
            'warnings': []
        }

        # Check total exposure
        total_exposure = portfolio.get('total_exposure', 0)
        if total_exposure > self.initial_capital:
            validation['within_limits'] = False
            validation['warnings'].append('Total exposure exceeds initial capital')

        # Check drawdown
        current_drawdown = portfolio.get('drawdown', 0)
        if current_drawdown > 0.15:  # 15% max drawdown
            validation['within_limits'] = False
            validation['warnings'].append('Portfolio drawdown exceeds 15%')

        return validation

    def adjust_position_sizes(self, 
                            positions: Dict[str, Any], 
                            market_conditions: str) -> Dict[str, Any]:
        """
        Adjust position sizes based on market conditions.
        """
        adjustments = {}
        
        # Scale position sizes based on market conditions
        scale_factor = {
            'highly_volatile': 0.5,    # Reduce position sizes
            'normal': 1.0,             # Normal position sizes
            'trending': 1.2            # Slightly larger positions in trending markets
        }.get(market_conditions, 1.0)

        for symbol, position in positions.items():
            adjustments[symbol] = {
                'current_size': position['size'],
                'adjusted_size': position['size'] * scale_factor,
                'adjustment_factor': scale_factor
            }

        return adjustments

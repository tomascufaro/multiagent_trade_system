from typing import Dict, Any
import yaml

class CapitalAllocator:
    """
    CapitalAllocator manages capital allocation for trading, including trade sizing,
    portfolio risk validation, and position size adjustments based on market conditions.

    Attributes:
        initial_capital (float): The starting capital for trading.
        risk_per_trade (float): Fraction of available capital to risk per trade (e.g., 0.02 for 2%).
        max_position_size (float): Maximum allowed size for any single position.
    """
    def __init__(self, config_path: str = '../config/settings.yaml'):
        """
        Initialize the CapitalAllocator with trading parameters loaded from a YAML config file.

        Args:
            config_path (str): Path to the YAML configuration file containing trading settings.
        """
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            self.initial_capital = config['trading']['initial_capital']
            self.risk_per_trade = config['trading']['risk_per_trade']
            self.max_position_size = config['trading']['max_position_size']

    def calculate_trade_size(self, 
                           available_capital: float, 
                           current_positions: Dict[str, Any]) -> float:
        """
        Calculate the appropriate trade size based on available capital and current positions.

        Args:
            available_capital (float): The total capital currently available for trading.
            current_positions (dict): Dictionary of current open positions, keyed by symbol.
                Each value should have 'size' and 'entry_price'.

        Returns:
            float: The maximum allowed trade size for a new position.
        """
        # Calculate total exposure from current positions
        total_exposure = sum(pos['size'] * pos['entry_price'] 
                           for pos in current_positions.values())

        # Calculate remaining capital available for new positions
        remaining_capital = available_capital - total_exposure

        # Calculate maximum trade size based on risk per trade and max position size
        max_trade_size = min(
            remaining_capital * self.risk_per_trade,
            self.max_position_size
        )

        return max_trade_size

    def validate_portfolio_risk(self, 
                              portfolio: Dict[str, Any]) -> Dict[str, bool]:
        """
        Validate overall portfolio risk levels, such as exposure and drawdown.

        Args:
            portfolio (dict): Dictionary containing portfolio information, including
                'total_exposure' and 'drawdown'.

        Returns:
            dict: Validation result with 'within_limits' (bool) and 'warnings' (list of str).
        """
        validation = {
            'within_limits': True,
            'warnings': []
        }

        # Check if total exposure exceeds initial capital
        total_exposure = portfolio.get('total_exposure', 0)
        if total_exposure > self.initial_capital:
            validation['within_limits'] = False
            validation['warnings'].append('Total exposure exceeds initial capital')

        # Check if drawdown exceeds 15%
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

        Args:
            positions (dict): Dictionary of current positions, keyed by symbol. Each value should have 'size'.
            market_conditions (str): Description of current market conditions. Supported values:
                'highly_volatile', 'normal', 'trending'.

        Returns:
            dict: Dictionary keyed by symbol, with current and adjusted sizes and the adjustment factor.
        """
        adjustments = {}
        
        # Determine scale factor based on market conditions
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

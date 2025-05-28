from typing import Dict, Any
import yaml

class RiskManager:
    def __init__(self, config_path: str = '../config/settings.yaml'):
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            self.max_drawdown = config['risk']['max_drawdown']
            self.stop_loss = config['risk']['stop_loss']
            self.take_profit = config['risk']['take_profit']

    def calculate_position_size(self, 
                             capital: float, 
                             entry_price: float, 
                             stop_loss_price: float) -> float:
        """
        Calculate the appropriate position size based on risk parameters.
        """
        if not all([capital, entry_price, stop_loss_price]):
            return 0

        risk_amount = capital * self.stop_loss
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return 0

        position_size = risk_amount / price_risk
        return position_size

    def check_stop_loss(self, 
                       position: Dict[str, Any], 
                       current_price: float) -> bool:
        """
        Check if stop loss has been triggered.
        """
        if not position:
            return False

        entry_price = position['entry_price']
        side = position['side']

        if side == 'LONG':
            return current_price <= entry_price * (1 - self.stop_loss)
        else:  # SHORT
            return current_price >= entry_price * (1 + self.stop_loss)

    def check_take_profit(self, 
                         position: Dict[str, Any], 
                         current_price: float) -> bool:
        """
        Check if take profit has been triggered.
        """
        if not position:
            return False

        entry_price = position['entry_price']
        side = position['side']

        if side == 'LONG':
            return current_price >= entry_price * (1 + self.take_profit)
        else:  # SHORT
            return current_price <= entry_price * (1 - self.take_profit)

    def validate_trade(self, 
                      trade: Dict[str, Any], 
                      portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a potential trade against risk parameters.
        """
        validation = {
            'valid': True,
            'reason': 'Trade meets risk parameters'
        }

        # Check if we're within drawdown limits
        if portfolio['drawdown'] >= self.max_drawdown:
            validation['valid'] = False
            validation['reason'] = f'Maximum drawdown of {self.max_drawdown*100}% exceeded'
            return validation

        # Add more validation rules as needed

        return validation

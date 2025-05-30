from typing import Dict, Any
import yaml

class RiskManager:
    """
    RiskManager handles risk management logic for trading, including position sizing,
    stop loss and take profit checks, and trade validation against risk parameters.

    Attributes:
        max_drawdown (float): Maximum allowed drawdown as a fraction (e.g., 0.2 for 20%).
        stop_loss (float): Stop loss threshold as a fraction (e.g., 0.05 for 5%).
        take_profit (float): Take profit threshold as a fraction (e.g., 0.1 for 10%).
    """
    def __init__(self, config_path: str = '../config/settings.yaml'):
        """
        Initialize the RiskManager with risk parameters loaded from a YAML config file.

        Args:
            config_path (str): Path to the YAML configuration file containing risk settings.
        """
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

        Args:
            capital (float): Total capital available for trading.
            entry_price (float): The price at which the position will be entered.
            stop_loss_price (float): The price at which the stop loss will be triggered.

        Returns:
            float: The calculated position size. Returns 0 if inputs are invalid or price risk is zero.
        """
        if not all([capital, entry_price, stop_loss_price]):
            return 0

        # Amount of capital to risk per trade
        risk_amount = capital * self.stop_loss
        # Price difference between entry and stop loss
        price_risk = abs(entry_price - stop_loss_price)
        
        if price_risk == 0:
            return 0

        # Position size = risk amount divided by price risk
        position_size = risk_amount / price_risk
        return position_size

    def check_stop_loss(self, 
                       position: Dict[str, Any], 
                       current_price: float) -> bool:
        """
        Check if stop loss has been triggered for a given position.

        Args:
            position (dict): Dictionary containing at least 'entry_price' and 'side' ('LONG' or 'SHORT').
            current_price (float): The current market price of the asset.

        Returns:
            bool: True if stop loss is triggered, False otherwise.
        """
        if not position:
            return False

        entry_price = position['entry_price']
        side = position['side']

        if side == 'LONG':
            # For long positions, stop loss triggers if price falls below threshold
            return current_price <= entry_price * (1 - self.stop_loss)
        else:  # SHORT
            # For short positions, stop loss triggers if price rises above threshold
            return current_price >= entry_price * (1 + self.stop_loss)

    def check_take_profit(self, 
                         position: Dict[str, Any], 
                         current_price: float) -> bool:
        """
        Check if take profit has been triggered for a given position.

        Args:
            position (dict): Dictionary containing at least 'entry_price' and 'side' ('LONG' or 'SHORT').
            current_price (float): The current market price of the asset.

        Returns:
            bool: True if take profit is triggered, False otherwise.
        """
        if not position:
            return False

        entry_price = position['entry_price']
        side = position['side']

        if side == 'LONG':
            # For long positions, take profit triggers if price rises above threshold
            return current_price >= entry_price * (1 + self.take_profit)
        else:  # SHORT
            # For short positions, take profit triggers if price falls below threshold
            return current_price <= entry_price * (1 - self.take_profit)

    def validate_trade(self, 
                      trade: Dict[str, Any], 
                      portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a potential trade against risk parameters, such as max drawdown.

        Args:
            trade (dict): Dictionary representing the trade to validate.
            portfolio (dict): Dictionary containing portfolio information, including 'drawdown'.

        Returns:
            dict: Validation result with 'valid' (bool) and 'reason' (str).
        """
        validation = {
            'valid': True,
            'reason': 'Trade meets risk parameters'
        }

        # Debug logging for drawdown
        print(f"[RiskManager] Portfolio drawdown: {portfolio.get('drawdown')}, Max allowed: {self.max_drawdown}")
        print(f"[RiskManager] Portfolio equity: {portfolio.get('equity')}, cash: {portfolio.get('cash')}")
        print(f"[RiskManager] Trade action: {trade.get('action')}, size: {trade.get('size')}, reason: {trade.get('reason')}")

        # Check if portfolio drawdown exceeds the maximum allowed
        if portfolio['drawdown'] >= self.max_drawdown:
            print(f"[RiskManager] Trade rejected due to drawdown limit.")
            validation['valid'] = False
            validation['reason'] = f'Maximum drawdown of {self.max_drawdown*100}% exceeded'
            return validation

        # Additional validation rules can be added here

        return validation

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_saver import load_latest_data, save_data

    # Load latest account status and open positions using data_saver
    account_data = load_latest_data('account_status')
    positions_data = load_latest_data('open_positions') or []

    # Example symbol to test
    symbol = 'AAPL'
    # Find current position for the symbol
    current_position = None
    for pos in positions_data:
        if pos.get('symbol') == symbol:
            current_position = {
                'symbol': pos.get('symbol'),
                'side': 'LONG' if float(pos.get('qty', 0)) > 0 else 'SHORT',
                'qty': abs(float(pos.get('qty', 0))),
                'avg_entry_price': float(pos.get('avg_entry_price', 0)),
                'market_value': float(pos.get('market_value', 0))
            }
            break

    equity = float(account_data.get('equity', 0)) if account_data else 0
    cash = float(account_data.get('cash', 0)) if account_data else 0
    initial_equity = cash + equity if (cash + equity) > 0 else 1
    current_drawdown = max(0, (initial_equity - equity) / initial_equity) if initial_equity > 0 else 0

    portfolio_status = {
        'cash': cash,
        'equity': equity,
        'drawdown': current_drawdown,
        'positions': {pos.get('symbol'): pos for pos in positions_data}
    }

    # Example trade decision
    trade_decision = {
        'action': 'BUY',
        'reason': 'Test buy for risk validation',
        'size': 1
    }

    print("Testing RiskManager.validate_trade with latest snapshots...")
    risk_manager = RiskManager()
    validation = risk_manager.validate_trade(trade_decision, portfolio_status)
    print(f"Validation result: {validation}")
    save_data('risk_manager_test_result', validation)

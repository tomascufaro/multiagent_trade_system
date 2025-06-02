import sys
import os
import yaml
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from risk_control.risk_manager import RiskManager
from utils.data_saver import load_latest_data, save_data

# Load latest account status and open positions using data_saver
account_data = load_latest_data('account_status')
positions_data = load_latest_data('open_positions') or []

# Load initial equity from config
with open('config/settings.yaml', 'r') as f:
    config = yaml.safe_load(f)
initial_equity = float(config['trading']['initial_capital'])

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
current_drawdown = max(0, (initial_equity - equity) / initial_equity) if initial_equity > 0 else 0

portfolio_status = {
    'cash': cash,
    'equity': equity,
    'drawdown': current_drawdown,
    'positions': {pos.get('symbol'): pos for pos in positions_data}
}

# Example trade decision
decision = {
    'action': 'BUY',
    'reason': 'Test buy for risk validation',
    'size': 1
}

print("Testing RiskManager.validate_trade with latest snapshots...")
risk_manager = RiskManager(config_path='config/settings.yaml')
validation = risk_manager.validate_trade(decision, portfolio_status)
print(f"Validation result: {validation}")
save_data('risk_manager_test_result', validation) 
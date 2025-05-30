"""
mock_trader.py - Handles trade execution for the trading bot by placing real (paper) orders with Alpaca.

This class is responsible for sending trade orders to Alpaca's /v2/orders endpoint based on trade decisions
from the trading logic. It loads API credentials, builds the order payload, sends the request, and saves the
order response for record-keeping.
"""
import json
from datetime import datetime
from typing import Dict, Any
import yaml
import os
import requests
from dotenv import load_dotenv

class MockTrader:
    """
    MockTrader places real (paper) orders with Alpaca based on trade decisions from the trading bot.
    It loads API credentials, builds the order payload, sends the order, and saves the response.
    """
    def __init__(self, config_path: str = '../config/settings.yaml'):
        """
        Initialize MockTrader by loading API credentials and initial capital from config.
        Creates a directory for saving trade records.
        """
        load_dotenv()
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets/v2/orders"
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
            self.initial_capital = config['trading']['initial_capital']
        os.makedirs('trades', exist_ok=True)

    def execute_trade(self, 
                     trade_decision: Dict[str, Any], 
                     symbol: str, 
                     current_price: float) -> Dict[str, Any]:
        """
        Place a real order with Alpaca based on the trade decision.
        """
        if trade_decision['action'] == 'HOLD':
            return {'status': 'no_action', 'message': 'Holding position'}

        # Map your decision to Alpaca's order params
        side = trade_decision['action'].lower()  # 'buy' or 'sell'
        qty = str(trade_decision.get('size', 1))  # Alpaca expects string
        order_type = trade_decision.get('order_type', 'market')  # default to market
        time_in_force = trade_decision.get('time_in_force', 'day')  # default to day

        order_payload = {
            "symbol": symbol,
            "qty": qty,
            "side": side,
            "type": order_type,
            "time_in_force": time_in_force
        }
        # Add limit_price, stop_price, etc. if needed for advanced orders
        if 'limit_price' in trade_decision:
            order_payload['limit_price'] = str(trade_decision['limit_price'])
        if 'stop_price' in trade_decision:
            order_payload['stop_price'] = str(trade_decision['stop_price'])
        if 'notional' in trade_decision:
            order_payload['notional'] = str(trade_decision['notional'])

        headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
            "Content-Type": "application/json"
        }

        try:
            # Send the order to Alpaca
            response = requests.post(self.base_url, headers=headers, json=order_payload)
            response.raise_for_status()
            order_result = response.json()
            # Save the order details to a file for record-keeping
            self._save_trade(order_result)
            return {"status": "submitted", "order": order_result}
        except requests.RequestException as e:
            error_response = getattr(e, 'response', None)
            error_content = error_response.text if error_response is not None else str(e)
            return {"status": "error", "message": str(e), "response": error_content}

    def _save_trade(self, trade: Dict[str, Any]):
        """
        Save the trade/order details to a JSON file in the 'trades' directory.
        """
        filename = f"trades/trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(trade, f, indent=2)

"""
Data Manager - Simple data orchestration for analyst service
"""
import json
from datetime import datetime, timedelta
from .price_feed import PriceFeed
from .news_feed import NewsFeed
from .account_status import AccountStatus
from .open_positions import OpenPositions

class DataManager:
    def __init__(self, config_path='analyst_service/config/settings.yaml'):
        self.price_feed = PriceFeed(config_path)
        self.news_feed = NewsFeed(config_path)
        self.account_status = AccountStatus()
        self.open_positions = OpenPositions()
    
    def get_market_data(self, symbol: str):
        """Get market data for a symbol"""
        current_price = self.price_feed.get_current_price(symbol)
        historical_data = self.price_feed.get_historical_data(symbol)
        news_data = self.news_feed.get_news([symbol])
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'historical_data': historical_data,
            'news_data': news_data,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_position(self, symbol: str):
        """Get current position for symbol"""
        positions = self.open_positions.get_positions()
        for pos in positions:
            if pos.get('symbol') == symbol:
                return {
                    'symbol': pos.get('symbol'),
                    'side': 'LONG' if float(pos.get('qty', 0)) > 0 else 'SHORT',
                    'qty': abs(float(pos.get('qty', 0))),
                    'avg_entry_price': float(pos.get('avg_entry_price', 0)),
                    'market_value': float(pos.get('market_value', 0))
                }
        return None
    
    def get_portfolio_summary(self):
        """Get portfolio summary"""
        account_data = self.account_status.get_status()
        positions_data = self.open_positions.get_positions()
        
        return {
            'cash': float(account_data.get('cash', 0)),
            'equity': float(account_data.get('equity', 0)),
            'positions': positions_data,
            'timestamp': datetime.now().isoformat()
        }

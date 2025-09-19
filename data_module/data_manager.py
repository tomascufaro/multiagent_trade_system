"""
Data Manager - Simple data orchestration for analyst service

This module provides a unified interface for data access and portfolio tracking.
It manages the portfolio universe (current, historical, and watchlist assets)
and provides methods for data retrieval and analysis.
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Set, Optional
from price_feed import PriceFeed
from news_feed import NewsFeed
from account_status import AccountStatus
from open_positions import OpenPositions
from portfolio_tracker import PortfolioTracker

class DataManager:
    """
    Data Manager for portfolio tracking and analysis.
    
    Manages the portfolio universe (current positions, historical assets, and watchlist)
    and provides unified access to market data, account information, and portfolio tracking.
    
    Attributes:
        price_feed: Price data fetcher for stocks
        news_feed: News data fetcher for sentiment analysis
        account_status: Account information fetcher
        open_positions: Current positions fetcher
        portfolio_tracker: Portfolio tracking and database manager
        config_path: Path to configuration file
    """
    
    def __init__(self, config_path: str = 'analyst_service/config/settings.yaml'):
        """
        Initialize the DataManager with all required components.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = config_path
        self.price_feed = PriceFeed(config_path)
        self.news_feed = NewsFeed(config_path)
        self.account_status = AccountStatus()
        self.open_positions = OpenPositions()
        self.portfolio_tracker = PortfolioTracker()
        
        # Load watchlist from config on initialization
        self._load_watchlist_from_config()
    
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
    
    def save_portfolio_snapshot(self):
        """Save current portfolio state to database"""
        account_data = self.account_status.get_status()
        positions_data = self.open_positions.get_positions()
        
        # Get current prices for all positions
        current_prices = {}
        for pos in positions_data:
            symbol = pos.get('symbol')
            if symbol:
                current_prices[symbol] = self.price_feed.get_current_price(symbol)
        
        # Save portfolio snapshot
        snapshot = self.portfolio_tracker.save_portfolio_snapshot(account_data, positions_data)
        
        # Save positions with current prices
        self.portfolio_tracker.save_positions(positions_data, current_prices)
        
        return snapshot
    
    def get_performance_metrics(self, period: str = 'all_time'):
        """Get calculated performance metrics"""
        return self.portfolio_tracker.calculate_performance_metrics(period)
    
    def get_portfolio_history(self, days: int = 30):
        """Get portfolio history for analysis"""
        return self.portfolio_tracker.get_portfolio_history(days)
    
    def export_portfolio_data(self, output_path: str = "data/portfolio_export.json"):
        """Export portfolio data to JSON"""
        return self.portfolio_tracker.export_to_json(output_path)
    
    # Portfolio Universe Management Methods
    
    def update_universe(self) -> Set[str]:
        """
        Update portfolio universe with current positions.
        
        Discovers current positions from Alpaca and updates the universe database.
        Marks previously owned positions as historical if they're no longer held.
        
        Returns:
            Set of current position symbols
        """
        positions = self.open_positions.get_positions()
        current_symbols: Set[str] = set()
        
        for pos in positions:
            symbol = pos.get('symbol')
            if symbol:
                current_symbols.add(symbol)
                self._add_to_universe(symbol, 'current', f"Current position: {pos.get('qty', 0)} shares")
        
        # Mark sold positions as historical
        self._mark_sold_positions(current_symbols)
        
        return current_symbols
    
    def get_all_tracking_symbols(self) -> Set[str]:
        """
        Get all symbols we should track (current + historical + watchlist).
        
        Returns:
            Set of all symbols in the portfolio universe
        """
        conn = sqlite3.connect(self.portfolio_tracker.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT symbol FROM portfolio_universe')
        symbols = {row[0] for row in cursor.fetchall()}
        
        conn.close()
        
        # Fallback to AAPL if universe is empty (for testing)
        return symbols if symbols else {'AAPL'}
    
    def get_universe_summary(self) -> Dict[str, Any]:
        """
        Get summary of the portfolio universe.
        
        Returns:
            Dictionary with universe statistics and breakdown by status
        """
        conn = sqlite3.connect(self.portfolio_tracker.db_path)
        cursor = conn.cursor()
        
        # Count by status
        cursor.execute('''
            SELECT status, COUNT(*) 
            FROM portfolio_universe 
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())
        
        # Get frequently traded stocks
        cursor.execute('''
            SELECT symbol, times_owned 
            FROM portfolio_universe 
            WHERE times_owned > 1 
            ORDER BY times_owned DESC 
            LIMIT 5
        ''')
        frequent_trades = cursor.fetchall()
        
        conn.close()
        
        return {
            'status_counts': status_counts,
            'total_symbols': sum(status_counts.values()),
            'frequently_traded': frequent_trades,
            'last_updated': datetime.now().isoformat()
        }
    
    def add_watchlist_symbol(self, symbol: str, notes: Optional[str] = None) -> None:
        """
        Add a symbol to the watchlist.
        
        Args:
            symbol: Stock symbol to add to watchlist
            notes: Optional notes about why this symbol is being watched
        """
        self._add_to_universe(
            symbol, 
            'watchlist', 
            notes or f"Added to watchlist on {datetime.now().strftime('%Y-%m-%d')}"
        )
    
    def _add_to_universe(self, symbol: str, status: str, notes: Optional[str] = None) -> None:
        """
        Add or update a symbol in the portfolio universe.
        
        Args:
            symbol: Stock symbol
            status: Status ('current', 'historical', 'watchlist')
            notes: Optional notes about the symbol
        """
        conn = sqlite3.connect(self.portfolio_tracker.db_path)
        cursor = conn.cursor()
        
        # Check if symbol exists
        cursor.execute('SELECT symbol, times_owned FROM portfolio_universe WHERE symbol = ?', (symbol,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing symbol
            times_owned = existing[1]
            if status == 'current' and existing:
                # If we're buying back a stock we previously owned
                cursor.execute('''
                    UPDATE portfolio_universe 
                    SET status = ?, last_seen = ?, notes = ?, times_owned = ?
                    WHERE symbol = ?
                ''', (status, datetime.now().isoformat(), notes, times_owned + 1, symbol))
            else:
                # Regular update
                cursor.execute('''
                    UPDATE portfolio_universe 
                    SET status = ?, last_seen = ?, notes = ?
                    WHERE symbol = ?
                ''', (status, datetime.now().isoformat(), notes, symbol))
        else:
            # Insert new symbol
            cursor.execute('''
                INSERT INTO portfolio_universe 
                (symbol, first_seen, last_seen, status, times_owned, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                symbol, 
                datetime.now().isoformat(), 
                datetime.now().isoformat(),
                status, 
                1 if status == 'current' else 0,
                notes
            ))
        
        conn.commit()
        conn.close()
    
    def _mark_sold_positions(self, current_symbols: Set[str]) -> None:
        """
        Mark positions that are no longer current as historical.
        
        Args:
            current_symbols: Set of symbols currently held
        """
        conn = sqlite3.connect(self.portfolio_tracker.db_path)
        cursor = conn.cursor()
        
        # Get all symbols that were marked as 'current'
        cursor.execute("SELECT symbol FROM portfolio_universe WHERE status = 'current'")
        previously_current = {row[0] for row in cursor.fetchall()}
        
        # Find symbols that are no longer current
        sold_symbols = previously_current - current_symbols
        
        for symbol in sold_symbols:
            cursor.execute('''
                UPDATE portfolio_universe 
                SET status = 'historical', last_seen = ?
                WHERE symbol = ?
            ''', (datetime.now().isoformat(), symbol))
        
        conn.commit()
        conn.close()
    
    def _load_watchlist_from_config(self) -> None:
        """
        Load watchlist symbols from configuration file.
        
        Reads the watchlist from the YAML config and adds symbols to the universe.
        """
        try:
            import yaml
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            watchlist = config.get('portfolio', {}).get('watchlist', [])
            for symbol in watchlist:
                self._add_to_universe(
                    symbol, 
                    'watchlist', 
                    f"Added from config on {datetime.now().strftime('%Y-%m-%d')}"
                )
        except Exception as e:
            print(f"Could not load watchlist from config: {e}")
            # Add some default watchlist symbols for testing
            default_watchlist = ['NVDA', 'GOOGL', 'AMD']
            for symbol in default_watchlist:
                self._add_to_universe(
                    symbol, 
                    'watchlist', 
                    f"Default watchlist symbol added on {datetime.now().strftime('%Y-%m-%d')}"
                )

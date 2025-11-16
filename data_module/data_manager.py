"""
Data Manager - Orchestration layer for analyst service data operations

Coordinates between API clients and data repositories, contains business logic.
"""
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Set

from data_module.api_clients import PriceFeed, NewsFeed, AccountStatus, OpenPositions
from data_module.repositories import PortfolioRepository, NewsRepository, UniverseRepository


class DataManager:
    """
    Orchestrates data operations between APIs and database repositories.
    Contains business logic for portfolio tracking and analysis.
    """

    def __init__(self, config_path: str = 'analyst_service/config/settings.yaml'):
        # API clients
        self.price_feed = PriceFeed(config_path)
        self.news_feed = NewsFeed(config_path)
        self.account_status = AccountStatus()
        self.open_positions = OpenPositions()

        # Data repositories
        self.portfolio_repo = PortfolioRepository()
        self.news_repo = NewsRepository()
        self.universe_repo = UniverseRepository()

        self.config_path = config_path
        self._load_watchlist_from_config()

    # Market Data Operations

    def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive market data for a symbol"""
        return {
            'symbol': symbol,
            'current_price': self.price_feed.get_current_price(symbol),
            'historical_data': self.price_feed.get_historical_data(symbol),
            'news_data': self.news_feed.get_news([symbol]),
            'timestamp': datetime.now().isoformat()
        }

    def get_position(self, symbol: str) -> Dict[str, Any]:
        """Get current position for a symbol"""
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

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary"""
        account_data = self.account_status.get_status()
        positions_data = self.open_positions.get_positions()

        return {
            'cash': float(account_data.get('cash', 0)),
            'equity': float(account_data.get('equity', 0)),
            'positions': positions_data,
            'timestamp': datetime.now().isoformat()
        }

    # Portfolio Operations

    def save_portfolio_snapshot(self) -> Dict[str, Any]:
        """
        Save current portfolio state to database.
        Business logic: fetches data from APIs, calculates metrics, saves to DB.
        """
        account_data = self.account_status.get_status()
        positions_data = self.open_positions.get_positions()

        # Calculate portfolio metrics
        total_equity = float(account_data.get('equity', 0))
        cash = float(account_data.get('cash', 0))
        invested_capital = total_equity - cash

        unrealized_pnl = sum(
            float(pos.get('market_value', 0)) - float(pos.get('avg_entry_price', 0)) * abs(float(pos.get('qty', 0)))
            for pos in positions_data
        )

        prev_equity = self.portfolio_repo.get_previous_equity()
        day_change = total_equity - prev_equity if prev_equity else 0
        day_change_pct = (day_change / prev_equity * 100) if prev_equity else 0

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'account_id': account_data.get('id'),
            'total_equity': total_equity,
            'cash': cash,
            'invested_capital': invested_capital,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': 0.0,
            'total_pnl': unrealized_pnl,
            'day_change': day_change,
            'day_change_pct': day_change_pct
        }

        self.portfolio_repo.save_snapshot(snapshot)

        # Save positions with calculated metrics
        current_prices = {}
        for pos in positions_data:
            symbol = pos.get('symbol')
            if symbol:
                current_prices[symbol] = self.price_feed.get_current_price(symbol)

        self._save_positions_with_metrics(positions_data, current_prices, total_equity)

        return snapshot

    def _save_positions_with_metrics(self, positions_data: List[Dict], current_prices: Dict, total_equity: float):
        """Helper to calculate and save position metrics"""
        timestamp = datetime.now().isoformat()
        positions = []

        for pos in positions_data:
            symbol = pos.get('symbol')
            if not symbol:
                continue

            current_price = current_prices.get(symbol, 0)
            quantity = abs(float(pos.get('qty', 0)))
            avg_entry_price = float(pos.get('avg_entry_price', 0))
            market_value = float(pos.get('market_value', 0))

            cost_basis = quantity * avg_entry_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            position_size_pct = (market_value / total_equity * 100) if total_equity > 0 else 0

            positions.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': 'LONG' if float(pos.get('qty', 0)) > 0 else 'SHORT',
                'quantity': quantity,
                'avg_entry_price': avg_entry_price,
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct,
                'position_size_pct': position_size_pct,
                'days_held': 1
            })

        self.portfolio_repo.save_positions(positions)

    def calculate_performance_metrics(self, period: str = 'all_time') -> Dict[str, Any]:
        """Calculate portfolio performance metrics (business logic)"""
        df = self.portfolio_repo.get_history(days=365 if period == 'all_time' else 30)

        if df.empty:
            return {}

        df['returns'] = df['total_equity'].pct_change()
        df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1

        total_return = df['cumulative_returns'].iloc[-1] if not df.empty else 0
        sharpe_ratio = df['returns'].mean() / df['returns'].std() * (252 ** 0.5) if df['returns'].std() > 0 else 0

        df['peak'] = df['total_equity'].cummax()
        df['drawdown'] = (df['total_equity'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min()

        return {
            'total_return': total_return,
            'total_return_pct': total_return * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': df['returns'].std() * (252 ** 0.5)
        }

    def get_portfolio_history(self, days: int = 30) -> pd.DataFrame:
        """Get portfolio history"""
        return self.portfolio_repo.get_history(days)

    def export_portfolio_data(self, output_path: str = "data/portfolio_export.json") -> str:
        """Export portfolio data"""
        return self.portfolio_repo.export_to_json(output_path)

    # News Operations

    def save_news(self, articles: List[Dict[str, Any]]) -> int:
        """Save news articles"""
        return self.news_repo.save_articles(articles)

    def get_news_for_symbol(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get news for a symbol"""
        return self.news_repo.get_by_symbol(symbol, limit)

    # Universe Operations

    def update_universe(self) -> Set[str]:
        """Update portfolio universe with current positions"""
        positions = self.open_positions.get_positions()
        current_symbols = set()

        for pos in positions:
            symbol = pos.get('symbol')
            if symbol:
                current_symbols.add(symbol)
                self.universe_repo.add_symbol(
                    symbol,
                    status='current',
                    notes=f"Current position: {pos.get('qty', 0)} shares"
                )

        self.universe_repo.mark_as_historical(current_symbols)
        return current_symbols

    def get_all_tracking_symbols(self) -> Set[str]:
        """Get all symbols being tracked"""
        symbols = self.universe_repo.get_all_symbols()
        return symbols if symbols else {'AAPL'}

    def get_universe_summary(self) -> Dict[str, Any]:
        """Get universe summary"""
        return self.universe_repo.get_summary()

    def add_to_watchlist(self, symbol: str, notes: str = None):
        """Add symbol to watchlist"""
        self.universe_repo.add_symbol(symbol, status='watchlist', notes=notes)

    def _load_watchlist_from_config(self):
        """Seed watchlist from WISHLIST_SYMBOLS environment variable."""
        symbols_env = os.getenv("WISHLIST_SYMBOLS")
        if not symbols_env:
            return

        existing_symbols = self.universe_repo.get_all_symbols()
        for raw_symbol in symbols_env.split(','):
            symbol = raw_symbol.strip().upper()
            if not symbol or symbol in existing_symbols:
                continue
            self.add_to_watchlist(symbol)

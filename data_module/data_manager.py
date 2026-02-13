"""
Data Manager - Orchestration layer for analyst service data operations

Coordinates between API clients and data repositories, contains business logic.
"""
import os
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Set, Optional

from data_module.api_clients import PriceFeed, NewsFeed
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
        """Get current holding for a symbol"""
        holdings = self.portfolio_repo.get_holdings()
        for pos in holdings:
            if pos.get('symbol') == symbol:
                current_price = self.price_feed.get_current_price(symbol)
                market_value = (pos.get('quantity') or 0) * (current_price or 0)
                return {
                    'symbol': pos.get('symbol'),
                    'side': 'LONG',
                    'qty': pos.get('quantity'),
                    'avg_entry_price': pos.get('avg_entry_price'),
                    'market_value': market_value,
                    'current_price': current_price,
                }
        return None

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get current portfolio summary (manual holdings)."""
        summary = self.get_portfolio_value()
        return {
            'equity': summary.get('total_equity', 0),
            'net_contributed': summary.get('net_contributed', 0),
            'positions': summary.get('positions', []),
            'timestamp': datetime.now().isoformat()
        }

    # Portfolio Operations

    def save_portfolio_snapshot(self) -> Dict[str, Any]:
        """
        Save current portfolio state to database.
        Business logic: calculates metrics from manual holdings, saves to DB.
        """
        portfolio = self.get_portfolio_value()
        positions_data = portfolio.get('positions', [])
        total_equity = portfolio.get('total_equity', 0)
        invested_capital = total_equity
        unrealized_pnl = sum(float(pos.get('unrealized_pnl', 0)) for pos in positions_data)

        prev_equity = self.portfolio_repo.get_previous_equity()
        day_change = total_equity - prev_equity if prev_equity else 0
        day_change_pct = (day_change / prev_equity * 100) if prev_equity else 0

        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'account_id': None,
            'total_equity': total_equity,
            'cash': 0.0,
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
                current_prices[symbol] = pos.get('current_price') or self.price_feed.get_current_price(symbol)

        self._save_positions_with_metrics(positions_data, current_prices, total_equity)

        return snapshot

    def _save_positions_with_metrics(self, positions_data: List[Dict], current_prices: Dict, total_equity: float):
        """Helper to calculate and save position metrics from manual holdings."""
        timestamp = datetime.now().isoformat()
        positions = []

        for pos in positions_data:
            symbol = pos.get('symbol')
            if not symbol:
                continue

            current_price = current_prices.get(symbol, 0) or 0
            quantity = abs(float(pos.get('quantity', 0)))
            avg_entry_price = float(pos.get('avg_entry_price', 0))
            market_value = float(pos.get('market_value', 0)) or (quantity * current_price)

            cost_basis = quantity * avg_entry_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            position_size_pct = (market_value / total_equity * 100) if total_equity > 0 else 0

            positions.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': 'LONG',
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
        positions = self.portfolio_repo.get_holdings()
        current_symbols = set()

        for pos in positions:
            symbol = pos.get('symbol')
            if symbol:
                current_symbols.add(symbol)
                self.universe_repo.add_symbol(
                    symbol,
                    status='current',
                    notes=f"Current position: {pos.get('quantity', 0)} shares"
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

    def record_deposit(self, amount: float, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record a capital deposit."""
        assert amount > 0, "Deposit amount must be positive"
        flow = {
            'timestamp': datetime.now().isoformat(),
            'type': 'DEPOSIT',
            'amount': amount,
            'notes': notes
        }
        self.portfolio_repo.save_capital_flow(flow)
        return flow

    def record_withdrawal(self, amount: float, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record a capital withdrawal."""
        assert amount > 0, "Withdrawal amount must be positive"
        flow = {
            'timestamp': datetime.now().isoformat(),
            'type': 'WITHDRAWAL',
            'amount': amount,
            'notes': notes
        }
        self.portfolio_repo.save_capital_flow(flow)
        return flow

    def record_buy(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fees: float = 0.0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record a buy trade and update holdings."""
        import uuid

        assert quantity > 0, "Quantity must be positive"
        assert price > 0, "Price must be positive"

        total_value = quantity * price
        net_amount = total_value + fees

        trade = {
            'trade_id': f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol.upper(),
            'action': 'BUY',
            'quantity': quantity,
            'price': price,
            'total_value': total_value,
            'commission': 0.0,
            'net_amount': net_amount,
            'reason': notes or 'Manual trade entry',
            'analysis_confidence': None,
            'fees': fees,
            'notes': notes,
            'realized_pnl': None
        }

        self.portfolio_repo.save_trade(trade)
        self._update_holding_after_buy(symbol, quantity, price)

        print(f"✅ Bought {quantity} shares of {symbol} at ${price:.2f}")
        print(f"   Total cost: ${net_amount:.2f} (including ${fees:.2f} fees)")

        return trade

    def record_sell(
        self,
        symbol: str,
        quantity: float,
        price: float,
        fees: float = 0.0,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Record a sell trade and update holdings."""
        import uuid

        assert quantity > 0, "Quantity must be positive"
        assert price > 0, "Price must be positive"

        holding = self._get_holding(symbol)
        if not holding:
            raise ValueError(f"No open holding for {symbol}")
        if holding['quantity'] < quantity:
            raise ValueError(f"Insufficient quantity. Have {holding['quantity']}, trying to sell {quantity}")

        total_value = quantity * price
        net_amount = total_value - fees

        cost_basis = holding['avg_entry_price'] * quantity
        realized_pnl = total_value - cost_basis - fees

        trade = {
            'trade_id': f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol.upper(),
            'action': 'SELL',
            'quantity': quantity,
            'price': price,
            'total_value': total_value,
            'commission': 0.0,
            'net_amount': net_amount,
            'reason': notes or 'Manual trade entry',
            'analysis_confidence': None,
            'fees': fees,
            'notes': notes,
            'realized_pnl': realized_pnl
        }

        self.portfolio_repo.save_trade(trade)
        self._update_holding_after_sell(symbol, quantity)

        print(f"✅ Sold {quantity} shares of {symbol} at ${price:.2f}")
        print(f"   Total received: ${net_amount:.2f} (after ${fees:.2f} fees)")
        print(f"   Realized P&L: ${realized_pnl:.2f}")

        return trade

    def get_portfolio_value(self) -> Dict[str, Any]:
        """Calculate current portfolio value from manual holdings."""
        capital = self.portfolio_repo.get_capital_flow_summary()
        net_contributed = capital['deposits'] - capital['withdrawals']

        positions = self.portfolio_repo.get_holdings()

        positions_value = 0.0
        positions_data = []

        for pos in positions:
            symbol = pos['symbol']
            quantity = pos['quantity']
            avg_entry_price = pos['avg_entry_price']

            current_price = self.price_feed.get_current_price(symbol)

            market_value = quantity * (current_price or 0)
            cost_basis = quantity * avg_entry_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0

            positions_value += market_value

            positions_data.append({
                'symbol': symbol,
                'quantity': quantity,
                'avg_entry_price': avg_entry_price,
                'current_price': current_price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': unrealized_pnl,
                'unrealized_pnl_pct': unrealized_pnl_pct
            })

        total_equity = positions_value
        total_pnl = total_equity - net_contributed
        total_pnl_pct = (total_pnl / net_contributed * 100) if net_contributed > 0 else 0

        return {
            'total_equity': total_equity,
            'positions_value': positions_value,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'num_positions': len(positions_data),
            'positions': positions_data,
            'net_contributed': net_contributed,
            'total_deposits': capital['deposits'],
            'total_withdrawals': capital['withdrawals']
        }

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all holdings with current prices."""
        positions = self.portfolio_repo.get_holdings()

        for pos in positions:
            symbol = pos['symbol']
            pos['current_price'] = self.price_feed.get_current_price(symbol)
            pos['market_value'] = pos['quantity'] * (pos['current_price'] or 0)
            pos['unrealized_pnl'] = pos['market_value'] - (pos['quantity'] * pos['avg_entry_price'])

        return positions

    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Analyze a stock using existing AnalystService."""
        from analyst_service.analysis.analyst_service import AnalystService

        analyst = AnalystService(self.config_path)
        analysis = analyst.analyze(symbol)

        debate = analysis.get('debate', {})
        summary = debate.get('summary', '')

        recommendation = 'HOLD'
        if 'strong buy' in summary.lower() or 'strongly recommend buying' in summary.lower():
            recommendation = 'STRONG_BUY'
        elif 'buy' in summary.lower() or 'bullish' in summary.lower():
            recommendation = 'BUY'
        elif 'sell' in summary.lower() or 'bearish' in summary.lower():
            recommendation = 'SELL'

        analysis_record = {
            'symbol': symbol,
            'analysis_date': datetime.now().isoformat(),
            'recommendation': recommendation,
            'confidence_score': debate.get('confidence', 0.5),
            'current_price': self.price_feed.get_current_price(symbol),
            'analyst_notes': summary,
            'bull_case': debate.get('bull_perspective', ''),
            'bear_case': debate.get('bear_perspective', ''),
            'technical_signals': str(analysis.get('ta_signals', {}))
        }

        self.portfolio_repo.save_asset_analysis(analysis_record)

        return analysis_record

    def _get_holding(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get holding for symbol."""
        holdings = self.portfolio_repo.get_holdings()
        for pos in holdings:
            if pos['symbol'] == symbol:
                return pos
        return None

    def _update_holding_after_buy(self, symbol: str, quantity: float, price: float):
        """Update or create holding after buy."""
        holding = self._get_holding(symbol)

        if holding:
            old_qty = holding['quantity']
            old_price = holding['avg_entry_price']
            new_qty = old_qty + quantity
            new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty

            self.portfolio_repo.update_holding(holding['id'], {
                'quantity': new_qty,
                'avg_entry_price': new_avg_price
            })
        else:
            self.portfolio_repo.create_holding({
                'symbol': symbol,
                'quantity': quantity,
                'avg_entry_price': price
            })

    def _update_holding_after_sell(self, symbol: str, quantity: float):
        """Update holding after sell."""
        holding = self._get_holding(symbol)
        new_qty = holding['quantity'] - quantity

        if new_qty <= 0:
            self.portfolio_repo.delete_holding(holding['id'])
        else:
            self.portfolio_repo.update_holding(holding['id'], {'quantity': new_qty})

"""
Data Manager - Orchestration layer for analyst service data operations

Coordinates between API clients and data repositories, contains business logic.
"""
import os
import math
import pandas as pd
from datetime import datetime, timedelta
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
                current_price = self._get_current_or_latest_price(symbol)
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
        """Calculate portfolio performance metrics from the equity curve."""
        days = 365 if period == 'all_time' else 30
        curve = self.compute_equity_curve(days)
        if not curve:
            return {}

        equities = [point['equity'] for point in curve]
        returns = []
        for i in range(1, len(equities)):
            prev = equities[i - 1]
            curr = equities[i]
            if prev == 0:
                continue
            returns.append((curr / prev) - 1)

        if not returns:
            return {}

        cumulative = (equities[-1] / equities[0] - 1) if equities[0] else 0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        volatility = math.sqrt(variance) * math.sqrt(252)
        sharpe_ratio = (mean / math.sqrt(variance)) * math.sqrt(252) if variance > 0 else 0

        peak = equities[0]
        max_drawdown = 0.0
        for value in equities:
            if value > peak:
                peak = value
            drawdown = (value - peak) / peak if peak else 0
            max_drawdown = min(max_drawdown, drawdown)

        return {
            'total_return': cumulative,
            'total_return_pct': cumulative * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
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
        latest_daily_prices = self.portfolio_repo.get_latest_daily_prices(
            [pos['symbol'] for pos in positions if pos.get('symbol')]
        )

        positions_value = 0.0
        positions_data = []

        for pos in positions:
            symbol = pos['symbol']
            quantity = pos['quantity']
            avg_entry_price = pos['avg_entry_price']

            current_price = self._get_current_or_latest_price(symbol, latest_daily_prices)

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
        latest_daily_prices = self.portfolio_repo.get_latest_daily_prices(
            [pos['symbol'] for pos in positions if pos.get('symbol')]
        )

        for pos in positions:
            symbol = pos['symbol']
            pos['current_price'] = self._get_current_or_latest_price(symbol, latest_daily_prices)
            pos['market_value'] = pos['quantity'] * (pos['current_price'] or 0)
            pos['unrealized_pnl'] = pos['market_value'] - (pos['quantity'] * pos['avg_entry_price'])

        return positions

    def collect_daily_prices(self, symbols: Optional[List[str]] = None) -> int:
        """Collect latest daily prices for symbols and persist to DB."""
        if symbols is None:
            symbols = sorted(
                set(self.portfolio_repo.get_holding_symbols())
                | set(self.portfolio_repo.get_trade_symbols())
            )

        if not symbols:
            return 0

        price_rows: List[Dict[str, Any]] = []
        for symbol in symbols:
            bars = self.price_feed.get_historical_data(
                symbol, timeframe="1D", limit=1, days_back=5
            )
            if not bars:
                continue
            bar = bars[0]
            timestamp = str(bar.get("timestamp", ""))[:10]
            if not timestamp:
                continue
            price_rows.append(
                {"symbol": symbol, "date": timestamp, "close": float(bar.get("close", 0))}
            )

        return self.portfolio_repo.save_daily_prices(price_rows)

    def backfill_daily_prices(self, days_back: int = 365) -> int:
        """Backfill daily prices for all symbols (idempotent)."""
        symbols = sorted(
            set(self.portfolio_repo.get_holding_symbols())
            | set(self.portfolio_repo.get_trade_symbols())
        )
        if not symbols:
            return 0

        total_inserted = 0
        for symbol in symbols:
            bars = self.price_feed.get_historical_data(
                symbol, timeframe="1D", limit=1000, days_back=days_back
            )
            if not bars:
                continue
            price_rows: List[Dict[str, Any]] = []
            for bar in bars:
                timestamp = str(bar.get("timestamp", ""))[:10]
                if not timestamp:
                    continue
                price_rows.append(
                    {
                        "symbol": symbol,
                        "date": timestamp,
                        "close": float(bar.get("close", 0)),
                    }
                )
            total_inserted += self.portfolio_repo.save_daily_prices(price_rows)

        return total_inserted

    def compute_asset_metrics(self, days: int = 90) -> List[Dict[str, Any]]:
        """Compute per-asset metrics and signals from daily prices."""
        from analyst_service.analysis.ta_signals import TechnicalAnalysis

        holdings = self.portfolio_repo.get_holdings()
        if not holdings:
            return []

        symbols = [h["symbol"] for h in holdings if h.get("symbol")]
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days + 5)
        prices_by_symbol = self.portfolio_repo.get_daily_prices(
            symbols, start_date.isoformat(), end_date.isoformat()
        )

        ta = TechnicalAnalysis(self.config_path)
        realized_by_symbol = self.portfolio_repo.get_realized_pnl_by_symbol()
        total_equity = self.get_portfolio_value().get("total_equity", 0) or 0

        results: List[Dict[str, Any]] = []
        for holding in holdings:
            symbol = holding.get("symbol")
            if not symbol:
                continue

            rows = prices_by_symbol.get(symbol, [])
            closes = [float(r["close"]) for r in rows]

            latest_close = closes[-1] if closes else self.price_feed.get_current_price(symbol)
            if latest_close is None:
                latest_close = 0.0

            returns_7d = self._pct_return(closes, 7)
            returns_30d = self._pct_return(closes, 30)
            volatility_90d = self._volatility(closes, 90)
            drawdown_30d = self._max_drawdown(closes, 30)

            ta_signals = ta.get_signals(closes) if closes else {}
            signal_flags = self._classify_signals(ta_signals, latest_close)

            qty = float(holding.get("quantity") or 0)
            avg_entry = float(holding.get("avg_entry_price") or 0)
            market_value = qty * float(latest_close or 0)
            unrealized_pnl = market_value - (qty * avg_entry)
            realized_pnl = realized_by_symbol.get(symbol, 0.0)
            weight_pct = (market_value / total_equity * 100) if total_equity > 0 else 0.0

            results.append(
                {
                    "symbol": symbol,
                    "price": latest_close,
                    "returns_7d": returns_7d,
                    "returns_30d": returns_30d,
                    "volatility_90d": volatility_90d,
                    "drawdown_30d": drawdown_30d,
                    "position_pct": weight_pct,
                    "unrealized_pnl": unrealized_pnl,
                    "realized_pnl": realized_pnl,
                    "signals": signal_flags,
                    "raw_signals": ta_signals,
                }
            )

        return results

    def compute_equity_curve(self, days: int = 90) -> List[Dict[str, Any]]:
        """Compute equity curve from trades, capital flows, and daily prices."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        trades = self.portfolio_repo.get_all_trades()
        flows = self.portfolio_repo.get_capital_flows()

        # Load daily prices for all symbols in trades/holdings
        symbols = sorted(
            set(self.portfolio_repo.get_holding_symbols())
            | set(self.portfolio_repo.get_trade_symbols())
        )
        prices_by_symbol = self.portfolio_repo.get_daily_prices(
            symbols, start_date.isoformat(), end_date.isoformat()
        )

        # Build a date index from daily_prices
        all_dates = set()
        for rows in prices_by_symbol.values():
            for row in rows:
                all_dates.add(row["date"])
        date_list = sorted(all_dates)

        holdings: Dict[str, float] = {}
        cash = 0.0

        # Organize trades by date
        trades_by_date: Dict[str, List[Dict[str, Any]]] = {}
        for trade in trades:
            ts = str(trade.get("timestamp", ""))[:10]
            trades_by_date.setdefault(ts, []).append(trade)

        flows_by_date: Dict[str, List[Dict[str, Any]]] = {}
        for flow in flows:
            ts = str(flow.get("timestamp", ""))[:10]
            flows_by_date.setdefault(ts, []).append(flow)

        # Apply events before the start date to initialize state
        for date in sorted(set(trades_by_date.keys()) | set(flows_by_date.keys())):
            if date >= start_date.isoformat():
                continue
            for flow in flows_by_date.get(date, []):
                amount = float(flow.get("amount") or 0)
                if flow.get("type") == "DEPOSIT":
                    cash += amount
                elif flow.get("type") == "WITHDRAWAL":
                    cash -= amount
            for trade in trades_by_date.get(date, []):
                symbol = trade.get("symbol")
                qty = float(trade.get("quantity") or 0)
                price = float(trade.get("price") or 0)
                fees = float(trade.get("fees") or 0)
                action = trade.get("action")
                if action == "BUY":
                    cash -= (qty * price + fees)
                    holdings[symbol] = holdings.get(symbol, 0) + qty
                elif action == "SELL":
                    cash += (qty * price - fees)
                    holdings[symbol] = holdings.get(symbol, 0) - qty

        equity_curve: List[Dict[str, Any]] = []
        for date in date_list:
            if date < start_date.isoformat():
                continue
            # Apply trades for the day
            for flow in flows_by_date.get(date, []):
                amount = float(flow.get("amount") or 0)
                if flow.get("type") == "DEPOSIT":
                    cash += amount
                elif flow.get("type") == "WITHDRAWAL":
                    cash -= amount

            for trade in trades_by_date.get(date, []):
                symbol = trade.get("symbol")
                qty = float(trade.get("quantity") or 0)
                price = float(trade.get("price") or 0)
                fees = float(trade.get("fees") or 0)
                action = trade.get("action")

                if action == "BUY":
                    cash -= (qty * price + fees)
                    holdings[symbol] = holdings.get(symbol, 0) + qty
                elif action == "SELL":
                    cash += (qty * price - fees)
                    holdings[symbol] = holdings.get(symbol, 0) - qty

            # Compute equity using daily close
            total_value = cash
            for symbol, qty in holdings.items():
                if qty == 0:
                    continue
                rows = prices_by_symbol.get(symbol, [])
                close_map = {r["date"]: r["close"] for r in rows}
                price = close_map.get(date)
                if price is None:
                    continue
                total_value += qty * float(price)

            equity_curve.append({"date": date, "equity": total_value})

        return equity_curve

    def _pct_return(self, closes: List[float], days: int) -> float:
        if len(closes) <= days:
            return 0.0
        start = closes[-(days + 1)]
        end = closes[-1]
        if start == 0:
            return 0.0
        return (end / start - 1) * 100

    def _volatility(self, closes: List[float], days: int) -> float:
        if len(closes) <= days:
            return 0.0
        slice_closes = closes[-days:]
        returns = []
        for i in range(1, len(slice_closes)):
            prev = slice_closes[i - 1]
            curr = slice_closes[i]
            if prev == 0:
                continue
            returns.append((curr / prev) - 1)
        if not returns:
            return 0.0
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance) * math.sqrt(252) * 100

    def _max_drawdown(self, closes: List[float], days: int) -> float:
        if len(closes) <= days:
            return 0.0
        slice_closes = closes[-days:]
        peak = slice_closes[0]
        max_dd = 0.0
        for price in slice_closes:
            if price > peak:
                peak = price
            dd = (price - peak) / peak if peak else 0
            max_dd = min(max_dd, dd)
        return max_dd * 100

    def _classify_signals(self, ta_signals: Dict[str, Any], price: float) -> Dict[str, Any]:
        rsi = ta_signals.get("rsi", 0.0)
        macd = ta_signals.get("macd", {})
        ema = ta_signals.get("ema", {})
        sma = ta_signals.get("sma", {})

        signals = {}

        if rsi >= 70:
            signals["rsi"] = {"value": rsi, "signal": "SELL"}
        elif rsi <= 30 and rsi > 0:
            signals["rsi"] = {"value": rsi, "signal": "BULL"}
        else:
            signals["rsi"] = {"value": rsi, "signal": "NEUTRAL"}

        macd_val = macd.get("macd", 0.0)
        macd_sig = macd.get("signal", 0.0)
        if macd_val > macd_sig:
            signals["macd"] = {"value": macd_val, "signal": "BULL"}
        elif macd_val < macd_sig:
            signals["macd"] = {"value": macd_val, "signal": "SELL"}
        else:
            signals["macd"] = {"value": macd_val, "signal": "NEUTRAL"}

        ema_short = ema.get("short_ema", 0.0)
        ema_long = ema.get("long_ema", 0.0)
        if price > ema_short:
            signals["ema20"] = {"value": ema_short, "signal": "BULL"}
        elif price < ema_short:
            signals["ema20"] = {"value": ema_short, "signal": "SELL"}
        else:
            signals["ema20"] = {"value": ema_short, "signal": "NEUTRAL"}

        if price > ema_long:
            signals["ema50"] = {"value": ema_long, "signal": "BULL"}
        elif price < ema_long:
            signals["ema50"] = {"value": ema_long, "signal": "SELL"}
        else:
            signals["ema50"] = {"value": ema_long, "signal": "NEUTRAL"}

        sma_short = sma.get("short_sma", 0.0)
        sma_long = sma.get("long_sma", 0.0)
        if sma_short == 0.0 or sma_long == 0.0:
            signals["sma50_200"] = {"value": sma_short - sma_long, "signal": "N/A"}
        elif sma_short > sma_long:
            signals["sma50_200"] = {"value": sma_short - sma_long, "signal": "BULL"}
        elif sma_short < sma_long:
            signals["sma50_200"] = {"value": sma_short - sma_long, "signal": "SELL"}
        else:
            signals["sma50_200"] = {"value": sma_short - sma_long, "signal": "NEUTRAL"}

        return signals

    def analyze_stock(self, symbol: str) -> Dict[str, Any]:
        """Analyze a stock using existing AnalystService."""
        from analyst_service.analysis.analyst_service import AnalystService

        symbol = symbol.upper()

        try:
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

            confidence = debate.get('confidence', 0.5)
            bull_case = debate.get('bull_perspective', '')
            bear_case = debate.get('bear_perspective', '')
            technical_signals = analysis.get('ta_signals', {})
            analyst_notes = summary
        except Exception as exc:
            market_data = self.get_market_data(symbol)
            historical = market_data.get("historical_data") or []
            closes = [bar["close"] for bar in historical if "close" in bar]

            ta_data = {}
            signal_flags = {}
            if closes:
                from analyst_service.analysis.ta_signals import TechnicalAnalysis

                ta = TechnicalAnalysis(self.config_path)
                ta_data = ta.get_signals(closes)
                latest_close = closes[-1]
                signal_flags = self._classify_signals(ta_data, latest_close)

            bull_votes = sum(1 for value in signal_flags.values() if value.get("signal") == "BULL")
            sell_votes = sum(1 for value in signal_flags.values() if value.get("signal") == "SELL")
            confidence = 0.5
            recommendation = "HOLD"
            if bull_votes > sell_votes:
                recommendation = "BUY"
                confidence = min(0.9, 0.5 + (bull_votes - sell_votes) * 0.1)
            elif sell_votes > bull_votes:
                recommendation = "SELL"
                confidence = min(0.9, 0.5 + (sell_votes - bull_votes) * 0.1)

            analyst_notes = (
                "Fallback analysis generated from technical indicators because AI debate "
                f"service was unavailable ({type(exc).__name__})."
            )
            bull_case = f"Bullish signals: {bull_votes}"
            bear_case = f"Bearish signals: {sell_votes}"
            technical_signals = ta_data


        analysis_record = {
            'symbol': symbol,
            'analysis_date': datetime.now().isoformat(),
            'recommendation': recommendation,
            'confidence_score': confidence,
            'current_price': self._get_current_or_latest_price(symbol),
            'analyst_notes': analyst_notes,
            'bull_case': bull_case,
            'bear_case': bear_case,
            'technical_signals': str(technical_signals)
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

    def _get_current_or_latest_price(
        self,
        symbol: str,
        latest_daily_prices: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> float:
        """Use live price when available, otherwise fall back to the latest stored close."""
        if self.price_feed.api_key and self.price_feed.secret_key:
            live_price = self.price_feed.get_current_price(symbol)
            if live_price is not None:
                return float(live_price)

        latest_daily_prices = latest_daily_prices or self.portfolio_repo.get_latest_daily_prices([symbol])
        latest = latest_daily_prices.get(symbol) if latest_daily_prices else None
        if latest is None:
            return 0.0
        return float(latest.get("close") or 0.0)

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

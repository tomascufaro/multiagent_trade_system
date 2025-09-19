"""
Portfolio Tracker - Comprehensive investment progress tracking
"""
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import os

class PortfolioTracker:
    def __init__(self, db_path: str = "data/portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with portfolio tracking tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Portfolio snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                account_id TEXT,
                total_equity REAL,
                cash REAL,
                invested_capital REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                total_pnl REAL,
                day_change REAL,
                day_change_pct REAL,
                UNIQUE(timestamp, account_id)
            )
        ''')
        
        # Positions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT,
                quantity REAL,
                avg_entry_price REAL,
                current_price REAL,
                market_value REAL,
                cost_basis REAL,
                unrealized_pnl REAL,
                unrealized_pnl_pct REAL,
                position_size_pct REAL,
                days_held INTEGER
            )
        ''')
        
        # Trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT UNIQUE,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT,
                quantity REAL,
                price REAL,
                total_value REAL,
                commission REAL,
                net_amount REAL,
                reason TEXT,
                analysis_confidence REAL
            )
        ''')
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                period TEXT,
                total_return REAL,
                total_return_pct REAL,
                sharpe_ratio REAL,
                max_drawdown REAL,
                win_rate REAL,
                avg_win REAL,
                avg_loss REAL,
                profit_factor REAL,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER
            )
        ''')
        
        # Portfolio universe table - tracks current, historical, and watchlist assets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_universe (
                symbol TEXT PRIMARY KEY,
                first_seen TEXT NOT NULL,
                last_seen TEXT,
                status TEXT NOT NULL DEFAULT 'current',
                times_owned INTEGER DEFAULT 1,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_portfolio_snapshot(self, account_data: Dict[str, Any], 
                               positions_data: List[Dict[str, Any]]):
        """Save current portfolio snapshot"""
        timestamp = datetime.now().isoformat()
        
        # Calculate portfolio metrics
        total_equity = float(account_data.get('equity', 0))
        cash = float(account_data.get('cash', 0))
        invested_capital = total_equity - cash
        
        # Calculate unrealized P&L from positions
        unrealized_pnl = sum(
            float(pos.get('market_value', 0)) - float(pos.get('avg_entry_price', 0)) * abs(float(pos.get('qty', 0)))
            for pos in positions_data
        )
        
        # Get previous day's equity for day change calculation
        prev_equity = self._get_previous_equity()
        day_change = total_equity - prev_equity if prev_equity else 0
        day_change_pct = (day_change / prev_equity * 100) if prev_equity else 0
        
        snapshot = {
            'timestamp': timestamp,
            'account_id': account_data.get('id'),
            'total_equity': total_equity,
            'cash': cash,
            'invested_capital': invested_capital,
            'unrealized_pnl': unrealized_pnl,
            'realized_pnl': 0.0,  # Will be calculated from trades
            'total_pnl': unrealized_pnl,
            'day_change': day_change,
            'day_change_pct': day_change_pct
        }
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO portfolio_snapshots 
            (timestamp, account_id, total_equity, cash, invested_capital, 
             unrealized_pnl, realized_pnl, total_pnl, day_change, day_change_pct)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            snapshot['timestamp'], snapshot['account_id'], snapshot['total_equity'],
            snapshot['cash'], snapshot['invested_capital'], snapshot['unrealized_pnl'],
            snapshot['realized_pnl'], snapshot['total_pnl'], snapshot['day_change'],
            snapshot['day_change_pct']
        ))
        
        conn.commit()
        conn.close()
        
        return snapshot
    
    def save_positions(self, positions_data: List[Dict[str, Any]], 
                      current_prices: Dict[str, float]):
        """Save current positions with calculated metrics"""
        timestamp = datetime.now().isoformat()
        
        # Get total portfolio value for position size calculation
        total_equity = self._get_latest_equity()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for pos in positions_data:
            symbol = pos.get('symbol')
            if not symbol:
                continue
                
            current_price = current_prices.get(symbol, 0)
            quantity = abs(float(pos.get('qty', 0)))
            avg_entry_price = float(pos.get('avg_entry_price', 0))
            market_value = float(pos.get('market_value', 0))
            
            # Calculate metrics
            cost_basis = quantity * avg_entry_price
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0
            position_size_pct = (market_value / total_equity * 100) if total_equity > 0 else 0
            
            # Calculate days held (simplified - would need trade history for accurate calculation)
            days_held = 1  # Placeholder
            
            cursor.execute('''
                INSERT INTO positions 
                (timestamp, symbol, side, quantity, avg_entry_price, current_price,
                 market_value, cost_basis, unrealized_pnl, unrealized_pnl_pct,
                 position_size_pct, days_held)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp, symbol, 'LONG' if float(pos.get('qty', 0)) > 0 else 'SHORT',
                quantity, avg_entry_price, current_price, market_value, cost_basis,
                unrealized_pnl, unrealized_pnl_pct, position_size_pct, days_held
            ))
        
        conn.commit()
        conn.close()
    
    def save_trade(self, trade_data: Dict[str, Any]):
        """Save individual trade record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO trades 
            (trade_id, timestamp, symbol, action, quantity, price, total_value,
             commission, net_amount, reason, analysis_confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('trade_id'),
            trade_data.get('timestamp'),
            trade_data.get('symbol'),
            trade_data.get('action'),
            trade_data.get('quantity'),
            trade_data.get('price'),
            trade_data.get('total_value'),
            trade_data.get('commission', 0),
            trade_data.get('net_amount'),
            trade_data.get('reason'),
            trade_data.get('analysis_confidence')
        ))
        
        conn.commit()
        conn.close()
    
    def get_portfolio_history(self, days: int = 30) -> pd.DataFrame:
        """Get portfolio history for analysis"""
        conn = sqlite3.connect(self.db_path)
        
        query = '''
            SELECT * FROM portfolio_snapshots 
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return df
    
    def get_position_history(self, symbol: str = None, days: int = 30) -> pd.DataFrame:
        """Get position history for analysis"""
        conn = sqlite3.connect(self.db_path)
        
        if symbol:
            query = '''
                SELECT * FROM positions 
                WHERE symbol = ? AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days)
            df = pd.read_sql_query(query, conn, params=(symbol,))
        else:
            query = '''
                SELECT * FROM positions 
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days)
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df
    
    def calculate_performance_metrics(self, period: str = 'all_time') -> Dict[str, Any]:
        """Calculate performance metrics"""
        conn = sqlite3.connect(self.db_path)
        
        # Get portfolio history
        query = '''
            SELECT total_equity, timestamp FROM portfolio_snapshots 
            ORDER BY timestamp ASC
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if df.empty:
            return {}
        
        # Calculate returns
        df['returns'] = df['total_equity'].pct_change()
        df['cumulative_returns'] = (1 + df['returns']).cumprod() - 1
        
        # Calculate metrics
        total_return = df['cumulative_returns'].iloc[-1] if not df.empty else 0
        total_return_pct = total_return * 100
        
        # Sharpe ratio (simplified - would need risk-free rate)
        sharpe_ratio = df['returns'].mean() / df['returns'].std() * (252 ** 0.5) if df['returns'].std() > 0 else 0
        
        # Maximum drawdown
        df['peak'] = df['total_equity'].cummax()
        df['drawdown'] = (df['total_equity'] - df['peak']) / df['peak']
        max_drawdown = df['drawdown'].min()
        
        return {
            'total_return': total_return,
            'total_return_pct': total_return_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'volatility': df['returns'].std() * (252 ** 0.5),
            'total_trades': 0,  # Would need trade data
            'win_rate': 0.0     # Would need trade data
        }
    
    def _get_previous_equity(self) -> float:
        """Get previous day's equity for comparison"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_equity FROM portfolio_snapshots 
            WHERE timestamp < datetime('now', '-1 day')
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def _get_latest_equity(self) -> float:
        """Get latest portfolio equity"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT total_equity FROM portfolio_snapshots 
            ORDER BY timestamp DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else 0
    
    def export_to_json(self, output_path: str = "data/portfolio_export.json"):
        """Export portfolio data to JSON for backup/analysis"""
        conn = sqlite3.connect(self.db_path)
        
        # Get all data
        portfolio_df = pd.read_sql_query("SELECT * FROM portfolio_snapshots", conn)
        positions_df = pd.read_sql_query("SELECT * FROM positions", conn)
        trades_df = pd.read_sql_query("SELECT * FROM trades", conn)
        
        conn.close()
        
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_records': {
                    'portfolio_snapshots': len(portfolio_df),
                    'positions': len(positions_df),
                    'trades': len(trades_df)
                }
            },
            'portfolio_snapshots': portfolio_df.to_dict('records'),
            'positions': positions_df.to_dict('records'),
            'trades': trades_df.to_dict('records'),
            'performance_metrics': self.calculate_performance_metrics()
        }
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return output_path

"""Portfolio Repository - Data access for portfolio snapshots, positions, and trades"""
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any


class PortfolioRepository:
    def __init__(self, db_path: str = "data/portfolio.db"):
        self.db_path = db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize portfolio-related tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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

        conn.commit()
        conn.close()

    def save_snapshot(self, snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Save portfolio snapshot"""
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

    def save_positions(self, positions: List[Dict[str, Any]]):
        """Save current positions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for pos in positions:
            cursor.execute('''
                INSERT INTO positions
                (timestamp, symbol, side, quantity, avg_entry_price, current_price,
                 market_value, cost_basis, unrealized_pnl, unrealized_pnl_pct,
                 position_size_pct, days_held)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pos['timestamp'], pos['symbol'], pos['side'], pos['quantity'],
                pos['avg_entry_price'], pos['current_price'], pos['market_value'],
                pos['cost_basis'], pos['unrealized_pnl'], pos['unrealized_pnl_pct'],
                pos['position_size_pct'], pos['days_held']
            ))

        conn.commit()
        conn.close()

    def get_history(self, days: int = 30) -> pd.DataFrame:
        """Get portfolio history"""
        conn = sqlite3.connect(self.db_path)
        query = '''
            SELECT * FROM portfolio_snapshots
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df



    def get_previous_equity(self) -> float:
        """Get previous day's equity"""
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

    def export_to_json(self, output_path: str = "data/portfolio_export.json") -> str:
        """Export portfolio data to JSON"""
        conn = sqlite3.connect(self.db_path)

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
            'trades': trades_df.to_dict('records')
        }

        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        return output_path

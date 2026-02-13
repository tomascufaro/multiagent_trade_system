"""Portfolio Repository - Data access for portfolio snapshots, positions, and trades"""
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
from typing import Dict, List, Any


class PortfolioRepository:
    def __init__(self, db_path: str = "data/portfolio.db"):
        env_db_path = os.getenv("PORTFOLIO_DB_PATH")
        self.db_path = env_db_path or db_path
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
                days_held INTEGER,
                notes TEXT
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
                analysis_confidence REAL,
                fees REAL,
                notes TEXT,
                realized_pnl REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                quantity REAL NOT NULL,
                avg_entry_price REAL NOT NULL,
                notes TEXT,
                updated_at TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS capital_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT
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

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                confidence_score REAL,
                current_price REAL,
                analyst_notes TEXT,
                bull_case TEXT,
                bear_case TEXT,
                technical_signals TEXT,
                UNIQUE(symbol, analysis_date)
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

    def save_capital_flow(self, flow: Dict[str, Any]) -> int:
        """Save a deposit or withdrawal."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO capital_flows (timestamp, type, amount, notes)
            VALUES (?, ?, ?, ?)
        ''', (flow['timestamp'], flow['type'], flow['amount'], flow.get('notes')))
        flow_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return flow_id

    def get_capital_flow_summary(self) -> Dict[str, float]:
        """Get total deposits and withdrawals."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM capital_flows WHERE type = 'DEPOSIT'")
        deposits = cursor.fetchone()[0]
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM capital_flows WHERE type = 'WITHDRAWAL'")
        withdrawals = cursor.fetchone()[0]
        conn.close()
        return {'deposits': deposits, 'withdrawals': withdrawals}

    def save_trade(self, trade: Dict[str, Any]) -> int:
        """Save a trade record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO trades
            (trade_id, timestamp, symbol, action, quantity, price, total_value,
             commission, net_amount, reason, analysis_confidence, fees, notes, realized_pnl)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade['trade_id'], trade['timestamp'], trade['symbol'], trade['action'],
            trade['quantity'], trade['price'], trade['total_value'], trade['commission'],
            trade['net_amount'], trade['reason'], trade['analysis_confidence'],
            trade.get('fees', 0.0), trade.get('notes'), trade.get('realized_pnl')
        ))

        trade_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return trade_id

    def get_holdings(self) -> List[Dict[str, Any]]:
        """Get all current holdings."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, symbol, quantity, avg_entry_price, notes
            FROM holdings
            ORDER BY symbol
        ''')

        columns = ['id', 'symbol', 'quantity', 'avg_entry_price', 'notes']
        holdings = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return holdings

    def update_holding(self, holding_id: int, updates: Dict[str, Any]) -> bool:
        """Update holding fields."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [holding_id]

        cursor.execute(f'''
            UPDATE holdings
            SET {set_clause}
            WHERE id = ?
        ''', values)

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def create_holding(self, position: Dict[str, Any]) -> int:
        """Create new holding."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO holdings
            (symbol, quantity, avg_entry_price, notes, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            position['symbol'],
            position['quantity'],
            position['avg_entry_price'],
            position.get('notes'),
            datetime.now().isoformat()
        ))

        position_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return position_id

    def delete_holding(self, holding_id: int) -> bool:
        """Delete holding (position closed)."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM holdings WHERE id = ?', (holding_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def save_asset_analysis(self, analysis: Dict[str, Any]) -> int:
        """Save asset analysis to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO asset_analysis
            (symbol, analysis_date, recommendation, confidence_score, current_price,
             analyst_notes, bull_case, bear_case, technical_signals)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis['symbol'], analysis['analysis_date'], analysis['recommendation'],
            analysis.get('confidence_score'), analysis.get('current_price'),
            analysis.get('analyst_notes'), analysis.get('bull_case'),
            analysis.get('bear_case'), analysis.get('technical_signals')
        ))

        analysis_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return analysis_id

    def get_trade_history(self, days: int = 30, symbol: str = None) -> List[Dict[str, Any]]:
        """Get trade history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if symbol:
            cursor.execute('''
                SELECT * FROM trades
                WHERE symbol = ? AND timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days), (symbol,))
        else:
            cursor.execute('''
                SELECT * FROM trades
                WHERE timestamp >= datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days))

        columns = [desc[0] for desc in cursor.description]
        trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return trades

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

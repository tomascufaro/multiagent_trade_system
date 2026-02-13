"""Universe Repository - Data access for portfolio universe (symbol tracking)"""
import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Set, Tuple


class UniverseRepository:
    def __init__(self, db_path: str = "data/portfolio.db"):
        env_db_path = os.getenv("PORTFOLIO_DB_PATH")
        self.db_path = env_db_path or db_path
        self._init_tables()

    def _init_tables(self):
        """Initialize universe tracking table"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

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

    def add_symbol(self, symbol: str, status: str = 'current', notes: str = None):
        """Add or update symbol in universe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT symbol, times_owned FROM portfolio_universe WHERE symbol = ?', (symbol,))
        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE portfolio_universe
                SET last_seen = ?, status = ?, times_owned = times_owned + 1, notes = ?
                WHERE symbol = ?
            ''', (datetime.now().isoformat(), status, notes, symbol))
        else:
            cursor.execute('''
                INSERT INTO portfolio_universe (symbol, first_seen, last_seen, status, times_owned, notes)
                VALUES (?, ?, ?, ?, 1, ?)
            ''', (symbol, datetime.now().isoformat(), datetime.now().isoformat(), status, notes))

        conn.commit()
        conn.close()


    def get_all_symbols(self) -> Set[str]:
        """Get all symbols in universe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT symbol FROM portfolio_universe')
        symbols = {row[0] for row in cursor.fetchall()}

        conn.close()
        return symbols


    def get_summary(self) -> Dict[str, any]:
        """Get universe summary statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT status, COUNT(*)
            FROM portfolio_universe
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())

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
            'frequent_trades': frequent_trades
        }

    def mark_as_historical(self, symbols_to_keep: Set[str]):
        """Mark symbols not in the provided set as historical"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT symbol FROM portfolio_universe WHERE status = ?', ('current',))
        current_symbols = {row[0] for row in cursor.fetchall()}

        sold_symbols = current_symbols - symbols_to_keep

        for symbol in sold_symbols:
            cursor.execute('''
                UPDATE portfolio_universe
                SET status = ?, last_seen = ?
                WHERE symbol = ?
            ''', ('historical', datetime.now().isoformat(), symbol))

        conn.commit()
        conn.close()

        return sold_symbols

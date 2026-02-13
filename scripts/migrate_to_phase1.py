"""Simple database migration for Phase 1"""
import sqlite3
import shutil
from datetime import datetime


def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate():
    db_path = "data/portfolio.db"

    backup_path = f"data/portfolio_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        if not _column_exists(cursor, "positions", "notes"):
            cursor.execute("ALTER TABLE positions ADD COLUMN notes TEXT")
        if not _column_exists(cursor, "trades", "fees"):
            cursor.execute("ALTER TABLE trades ADD COLUMN fees REAL DEFAULT 0.0")
        if not _column_exists(cursor, "trades", "notes"):
            cursor.execute("ALTER TABLE trades ADD COLUMN notes TEXT")
        if not _column_exists(cursor, "trades", "realized_pnl"):
            cursor.execute("ALTER TABLE trades ADD COLUMN realized_pnl REAL")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                quantity REAL NOT NULL,
                avg_entry_price REAL NOT NULL,
                notes TEXT,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capital_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT
            )
        """)

        cursor.execute("""
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
        """)

        conn.commit()
        print("✅ Migration completed successfully")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()

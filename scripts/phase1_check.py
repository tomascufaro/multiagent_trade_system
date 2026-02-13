"""Phase 1 gate checks."""
import argparse
import os
import sqlite3
import subprocess
import sys


def _get_db_path():
    return os.getenv("PORTFOLIO_DB_PATH", "data/portfolio.db")


def _get_columns(cursor, table):
    cursor.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def check_schema():
    db_path = _get_db_path()
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        required_tables = {
            "holdings",
            "capital_flows",
            "asset_analysis",
            "trades",
            "positions",
        }
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}

        missing_tables = required_tables - existing_tables
        if missing_tables:
            print(f"❌ Missing tables: {sorted(missing_tables)}")
            return False

        trades_columns = _get_columns(cursor, "trades")
        for col in ["fees", "notes", "realized_pnl"]:
            if col not in trades_columns:
                print(f"❌ Missing column trades.{col}")
                return False

        positions_columns = _get_columns(cursor, "positions")
        if "notes" not in positions_columns:
            print("❌ Missing column positions.notes")
            return False

        holdings_columns = _get_columns(cursor, "holdings")
        for col in ["symbol", "quantity", "avg_entry_price", "updated_at"]:
            if col not in holdings_columns:
                print(f"❌ Missing column holdings.{col}")
                return False

        flows_columns = _get_columns(cursor, "capital_flows")
        for col in ["timestamp", "type", "amount"]:
            if col not in flows_columns:
                print(f"❌ Missing column capital_flows.{col}")
                return False

    finally:
        conn.close()

    print("✅ Schema check passed")
    return True


def run_pytest(test_path):
    cmd = [sys.executable, "-m", "pytest", test_path]
    result = subprocess.run(cmd)
    return result.returncode == 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["schema", "all"], help="Which gate to run")
    args = parser.parse_args()

    if args.mode == "schema":
        ok = check_schema()
        sys.exit(0 if ok else 1)

    if args.mode == "all":
        if not check_schema():
            sys.exit(1)

        tests_ok = run_pytest("tests/phase1")
        sys.exit(0 if tests_ok else 1)


if __name__ == "__main__":
    main()

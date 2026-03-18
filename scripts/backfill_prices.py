#!/usr/bin/env python3
"""Backfill daily prices for all symbols (idempotent)."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_module.data_manager import DataManager


def main():
    dm = DataManager()
    inserted = dm.backfill_daily_prices(days_back=365)
    print(f"Inserted {inserted} daily price rows")


if __name__ == "__main__":
    main()

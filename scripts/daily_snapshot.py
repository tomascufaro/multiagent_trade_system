#!/usr/bin/env python3
"""
Daily Portfolio Snapshot Script for GitHub Actions

This script runs twice daily to:
1. Update portfolio universe with current holdings
2. Take portfolio snapshots
3. Save data to the database
4. Generate summary reports
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_module.data_manager import DataManager

def main():
    """Main function to run daily portfolio snapshot."""
    print(f"🔄 Starting daily portfolio snapshot at {datetime.now()}")
    
    try:
        # Initialize data manager
        data_manager = DataManager()
        
        # 1. Update portfolio universe
        print("📊 Updating portfolio universe...")
        current_symbols = data_manager.update_universe()
        print(f"✅ Current positions: {list(current_symbols)}")
        
        # 2. Collect daily prices
        print("💾 Collecting daily prices...")
        inserted = data_manager.collect_daily_prices()
        print(f"✅ Stored {inserted} daily price rows")

        # 3. Take portfolio snapshot
        print("📸 Taking portfolio snapshot...")
        snapshot = data_manager.save_portfolio_snapshot()
        print(f"✅ Snapshot saved with timestamp: {snapshot.get('timestamp')}")
        
        # 4. Get universe summary
        print("📈 Generating universe summary...")
        universe_summary = data_manager.get_universe_summary()
        print(f"✅ Tracking {universe_summary['total_symbols']} symbols")
        print(f"   Status breakdown: {universe_summary['status_counts']}")
        
        # 5. Save summary to file for GitHub Actions
        summary_file = project_root / "data" / f"daily_summary_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        import json
        with open(summary_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'current_positions': list(current_symbols),
                'universe_summary': universe_summary,
                'snapshot_id': snapshot.get('id')
            }, f, indent=2)
        
        print(f"✅ Summary saved to {summary_file}")
        print("🎉 Daily snapshot completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during snapshot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

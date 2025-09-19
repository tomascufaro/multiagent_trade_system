"""
Example usage of the enhanced portfolio tracking system
"""
from data_manager import DataManager
import pandas as pd

def main():
    # Initialize data manager with portfolio tracking
    data_manager = DataManager()
    
    print("=== Portfolio Tracking Example ===\n")
    
    # 1. Update portfolio universe
    print("1. Updating portfolio universe...")
    current_symbols = data_manager.update_universe()
    print(f"Current positions: {list(current_symbols)}")
    
    # 2. Get universe summary
    print("\n2. Portfolio Universe Summary:")
    universe_summary = data_manager.get_universe_summary()
    print(f"Total symbols tracked: {universe_summary['total_symbols']}")
    print(f"Status breakdown: {universe_summary['status_counts']}")
    if universe_summary['frequently_traded']:
        print(f"Frequently traded: {universe_summary['frequently_traded']}")
    
    # 3. Get all tracking symbols
    all_symbols = data_manager.get_all_tracking_symbols()
    print(f"\nAll symbols to track: {list(all_symbols)}")
    
    # 4. Save current portfolio snapshot
    print("\n4. Saving portfolio snapshot...")
    snapshot = data_manager.save_portfolio_snapshot()
    print(f"Portfolio Equity: ${snapshot['total_equity']:,.2f}")
    print(f"Cash: ${snapshot['cash']:,.2f}")
    print(f"Invested Capital: ${snapshot['invested_capital']:,.2f}")
    print(f"Unrealized P&L: ${snapshot['unrealized_pnl']:,.2f}")
    print(f"Day Change: ${snapshot['day_change']:,.2f} ({snapshot['day_change_pct']:.2f}%)\n")
    
    # 5. Get performance metrics
    print("5. Performance Metrics:")
    metrics = data_manager.get_performance_metrics()
    print(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
    print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")
    print(f"Max Drawdown: {metrics.get('max_drawdown', 0)*100:.2f}%")
    print(f"Volatility: {metrics.get('volatility', 0)*100:.2f}%\n")
    
    # 6. Get portfolio history
    print("6. Portfolio History (Last 7 days):")
    history = data_manager.get_portfolio_history(days=7)
    if not history.empty:
        print(history[['timestamp', 'total_equity', 'day_change_pct']].head())
    else:
        print("No historical data available yet.\n")
    
    # 7. Export data for analysis
    print("7. Exporting portfolio data...")
    export_path = data_manager.export_portfolio_data()
    print(f"Data exported to: {export_path}\n")
    
    # 8. Example of adding a watchlist symbol
    print("8. Adding watchlist symbol example:")
    data_manager.add_watchlist_symbol('MSFT', 'Microsoft - Cloud computing leader')
    print("Added MSFT to watchlist")
    
    # 9. Show updated universe
    print("\n9. Updated Universe:")
    updated_summary = data_manager.get_universe_summary()
    print(f"Total symbols: {updated_summary['total_symbols']}")
    print(f"Status breakdown: {updated_summary['status_counts']}")
    
    # 10. Example of saving a trade (when you make trades)
    print("\n10. Example trade record:")
    example_trade = {
        'trade_id': 'trade_20250115_001',
        'timestamp': '2025-01-15T14:30:00Z',
        'symbol': 'AAPL',
        'action': 'BUY',
        'quantity': 10.0,
        'price': 150.25,
        'total_value': 1502.50,
        'commission': 0.0,
        'net_amount': 1502.50,
        'reason': 'Strong bullish conviction from analysis',
        'analysis_confidence': 0.75
    }
    
    # Uncomment when you want to save actual trades:
    # data_manager.portfolio_tracker.save_trade(example_trade)
    print("Trade record structure:")
    for key, value in example_trade.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()

"""
Manual test script for Phase 1 functionality
Run this to verify everything works
"""
from data_module.data_manager import DataManager


def test_phase1():
    """Test all Phase 1 functionality"""
    dm = DataManager()

    print("=" * 60)
    print("PHASE 1 MANUAL TEST")
    print("=" * 60)

    # Test 1: Record a deposit
    print("\n1. Testing DEPOSIT...")
    try:
        dm.record_deposit(10000, notes='Test deposit')
        print("✅ DEPOSIT successful")
    except Exception as e:
        print(f"❌ DEPOSIT failed: {e}")

    # Test 2: Record a buy
    print("\n2. Testing BUY trade...")
    try:
        dm.record_buy('AAPL', 10, 150.00, fees=1.0, notes='Test buy')
        print("✅ BUY trade successful")
    except Exception as e:
        print(f"❌ BUY trade failed: {e}")

    # Test 3: Get portfolio value
    print("\n3. Testing portfolio value calculation...")
    try:
        portfolio = dm.get_portfolio_value()
        print(f"✅ Portfolio value: ${portfolio['total_equity']:,.2f}")
        print(f"   Positions: {portfolio['num_positions']}")
    except Exception as e:
        print(f"❌ Portfolio calculation failed: {e}")

    # Test 4: Get positions
    print("\n4. Testing get positions...")
    try:
        positions = dm.get_open_positions()
        print(f"✅ Found {len(positions)} open positions")
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['quantity']} shares")
    except Exception as e:
        print(f"❌ Get positions failed: {e}")

    # Test 5: Record a sell
    print("\n5. Testing SELL trade...")
    try:
        dm.record_sell('AAPL', 5, 155.00, fees=1.0, notes='Test sell')
        print("✅ SELL trade successful")
    except Exception as e:
        print(f"❌ SELL trade failed: {e}")

    # Test 6: Analyze stock
    print("\n6. Testing stock analysis...")
    try:
        analysis = dm.analyze_stock('AAPL')
        print(f"✅ Analysis complete: {analysis['recommendation']}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

    # Test 7: Get trade history
    print("\n7. Testing trade history...")
    try:
        trades = dm.portfolio_repo.get_trade_history(days=30)
        print(f"✅ Found {len(trades)} trades in last 30 days")
    except Exception as e:
        print(f"❌ Trade history failed: {e}")

    print("\n" + "=" * 60)
    print("MANUAL TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_phase1()

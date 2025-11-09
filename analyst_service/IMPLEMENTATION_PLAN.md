# Implementation Plan: Core Data Integration for Bull/Bear Agents

## Overview
Integrate database data into the analysis agents using pre-fetched core data (no tools yet). This provides agents with rich context from portfolio history, positions, trades, and news.

---

## Phase 1: Create Data Context Builder

### File: `analyst_service/data_context.py`

**Purpose**: Centralized module to fetch database data using existing DataManager methods.

**Function**: `build_analysis_context(symbol: str) -> Dict[str, Any]`

**Data Sources** (using existing DataManager methods):
- `DataManager.get_portfolio_summary()` - Current portfolio (equity, cash, positions)
- `DataManager.get_position(symbol)` - Current position for symbol
- `DataManager.calculate_performance_metrics('30d')` - Performance stats
- `DataManager.get_news_for_symbol(symbol, limit=10)` - Recent news

**Returns structured context**:
```python
{
    'symbol': 'AAPL',
    
    # From DataManager.get_portfolio_summary()
    'portfolio': {
        'cash': 99706.03,
        'equity': 99992.09,
        'positions': [...],  # All current positions
        'timestamp': '...'
    },
    
    # From DataManager.get_position(symbol) - returns None if no position
    'position': {
        'symbol': 'AAPL',
        'side': 'LONG',
        'qty': 10.0,
        'avg_entry_price': 150.25,
        'market_value': 1523.00
    } or None,
    
    # From DataManager.calculate_performance_metrics('30d')
    'performance': {
        'total_return': 0.0175,
        'total_return_pct': 1.75,
        'sharpe_ratio': 1.25,
        'max_drawdown': -0.05,
        'volatility': 0.12
    },
    
    # From DataManager.get_news_for_symbol(symbol, limit=10)
    'recent_news': [
        {'id': '...', 'headline': '...', 'summary': '...', 'created_at': '...', ...},
        ...
    ],
    
    # Optional: Direct DB queries (if needed for historical context)
    'position_history': [],  # Query positions table directly if needed
    'trade_history': []      # Query trades table directly if needed
}
```

---

## Phase 2: Format Context for LLM Prompts

### Function in `analyst_service/data_context.py`

**Function**: `format_context_for_prompt(context: Dict) -> str`

**Purpose**: Convert structured context dictionary into readable text for LLM prompts.

**Format Example**:
```
=== PORTFOLIO CONTEXT ===
Current Equity: $99,992.09
Cash: $99,706.03
Total P&L: $170.75 (+0.17%)
Today's Change: -$7.91 (-0.79%)

=== POSITION STATUS ===
Symbol: AAPL
Position: LONG (10.0 shares)
Entry Price: $150.25
Current Price: $152.30
Unrealized P&L: +$20.50 (+1.36%)
Days Held: 5

=== POSITION HISTORY (Last 30 Days) ===
- Day 1: +1.2% (10 shares)
- Day 2: +0.8% (10 shares)
...

=== TRADE HISTORY ===
- 2025-01-10: BUY 10 shares @ $150.25 (Reason: "Strong bullish conviction", Confidence: 0.75)
- 2025-01-05: BUY 5 shares @ $148.50 (Reason: "...", Confidence: 0.65)

=== PERFORMANCE METRICS ===
Total Return: +1.75%
Sharpe Ratio: 1.25
Max Drawdown: -5.0%
Win Rate: 65%
Average Win: $125.50
Average Loss: -$75.25

=== RECENT NEWS ===
- "Apple announces new product" (Positive, 2 days ago)
- "Market volatility concerns" (Neutral, 5 days ago)
...
```

---

## Phase 3: Update Agents and Trading Crew

### Update `bull_agent.py` and `bear_agent.py`

**Changes**:
1. **Update `create_analysis_task()` to accept `db_context`**:
   ```python
   def create_analysis_task(
       self, 
       prices: List[float], 
       sentiment_data: Dict[str, Any],
       db_context: Dict[str, Any]  # NEW
   ) -> Task:
   ```

2. **Enhance task description** to include formatted DB context and updated instructions

### Update `trading_crew.py`

**Changes**:
1. Initialize DataManager
2. Fetch context in `conduct_analysis()`
3. Pass context to agent tasks

**Enhanced Agent Instructions**:

For Bull Agent:
- Consider current position performance (if LONG and profitable, this is bullish)
- Analyze trade history success rate
- Factor in portfolio context (if portfolio is doing well, more confident)
- Consider news sentiment trends
- Use position history to identify trends

For Bear Agent:
- Consider current position performance (if LONG and losing, this is bearish)
- Analyze trade history failure rate
- Factor in portfolio drawdowns
- Consider negative news sentiment
- Use position history to identify downtrends

---

## Implementation Order

1. **Step 1**: Create `data_context.py` with `build_analysis_context()` and `format_context_for_prompt()`
2. **Step 2**: Update `bull_agent.py` to accept `db_context` parameter
3. **Step 3**: Update `bear_agent.py` to accept `db_context` parameter
4. **Step 4**: Update `trading_crew.py` to fetch context and pass to agents
5. **Step 5**: Test with existing data

---

## Testing Strategy

1. **Test data fetching**: Verify all DB queries return expected data
2. **Test context formatting**: Ensure formatted text is readable and complete
3. **Test agent integration**: Verify agents receive and use context correctly
4. **Test analysis quality**: Compare analysis with/without DB context

---

## Backlog: Future Enhancements

### Phase 2: Repository Methods (If Needed Later)
- `get_position_history(symbol, days)` - Dedicated method for position history
- `get_trade_history(symbol, limit)` - Dedicated method for trade history  
- `get_latest_position_from_db(symbol)` - DB version of position (vs API)
- `get_performance_by_symbol(symbol)` - Symbol-specific performance metrics

### Phase 3: Tools for Agents
- `get_historical_position_data(symbol, days)` - Tool for deeper position queries
- `get_trade_success_rate(symbol)` - Tool for trade analysis
- `get_extended_news(symbol, days)` - Tool for extended news search
- `get_related_symbols(symbol)` - Tool to find correlated symbols

### Phase 4: Advanced Features
- Performance benchmarking (compare analysis quality with/without DB context)
- Caching for frequently accessed data
- Data validation and error handling
- Real-time data streaming updates
- Multi-symbol analysis support


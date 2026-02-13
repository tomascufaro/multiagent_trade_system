# Portfolio Database Schema Diagram

```mermaid
erDiagram
    portfolio_snapshots {
        INTEGER id PK
        TEXT timestamp
        TEXT account_id
        REAL total_equity
        REAL cash
        REAL invested_capital
        REAL unrealized_pnl
        REAL realized_pnl
        REAL total_pnl
        REAL day_change
        REAL day_change_pct
    }
    
    positions {
        INTEGER id PK
        TEXT timestamp
        TEXT symbol
        TEXT side
        REAL quantity
        REAL avg_entry_price
        REAL current_price
        REAL market_value
        REAL cost_basis
        REAL unrealized_pnl
        REAL unrealized_pnl_pct
        REAL position_size_pct
        INTEGER days_held
        TEXT notes
    }
    
    trades {
        INTEGER id PK
        TEXT trade_id UK
        TEXT timestamp
        TEXT symbol
        TEXT action
        REAL quantity
        REAL price
        REAL total_value
        REAL commission
        REAL net_amount
        TEXT reason
        REAL analysis_confidence
        REAL fees
        TEXT notes
        REAL realized_pnl
    }

    holdings {
        INTEGER id PK
        TEXT symbol UK
        REAL quantity
        REAL avg_entry_price
        TEXT notes
        TEXT updated_at
    }

    capital_flows {
        INTEGER id PK
        TEXT timestamp
        TEXT type
        REAL amount
        TEXT notes
    }
    
    performance_metrics {
        INTEGER id PK
        TEXT timestamp
        TEXT period
        REAL total_return
        REAL total_return_pct
        REAL sharpe_ratio
        REAL max_drawdown
        REAL win_rate
        REAL avg_win
        REAL avg_loss
        REAL profit_factor
        INTEGER total_trades
        INTEGER winning_trades
        INTEGER losing_trades
    }
    
    news_articles {
        TEXT id PK
        TEXT headline
        TEXT author
        TEXT summary
        TEXT content
        TEXT url
        TEXT created_at
        TEXT updated_at
        TEXT source
        TEXT saved_at
    }
    
    news_symbols {
        TEXT news_id PK,FK
        TEXT symbol PK
    }
    
    portfolio_universe {
        TEXT symbol PK
        TEXT first_seen
        TEXT last_seen
        TEXT status
        INTEGER times_owned
        TEXT notes
    }
    
    %% Relationships
    portfolio_snapshots ||--o{ positions : "has"
    holdings ||--o{ trades : "generates"
    portfolio_snapshots ||--o{ performance_metrics : "calculated_from"
    news_articles ||--o{ news_symbols : "linked_to"
```

## Table Descriptions

### Core Portfolio Tables
- **portfolio_snapshots**: Daily snapshots of overall portfolio performance
- **positions**: Individual position details and performance tracking
- **trades**: Record of all buy/sell transactions
- **holdings**: Current open holdings (manual positions)
- **capital_flows**: Deposits and withdrawals
- **performance_metrics**: Calculated performance metrics by period

### News Tables
- **news_articles**: News articles fetched from Alpaca news API
- **news_symbols**: Junction table linking articles to symbols (many-to-many)

### Universe Tracking
- **portfolio_universe**: Tracks all symbols that have been in the portfolio

## Relationship Notes

- `portfolio_snapshots` → `positions`: Linked via timestamp and account_id
- `positions` → `trades`: Linked via symbol and timestamp
- `portfolio_snapshots` → `performance_metrics`: Metrics calculated from snapshots
- `news_articles` → `news_symbols`: Many-to-many relationship (articles can mention multiple symbols)
- `portfolio_universe`: Standalone table tracking symbol metadata

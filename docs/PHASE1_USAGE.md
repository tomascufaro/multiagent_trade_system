# Phase 1 Usage Guide

## Setup

1. Run migration: `poetry run python scripts/migrate_to_phase1.py`
2. Record deposits via CLI
3. Record trades via CLI

## Daily Workflow

### Recording Deposits

```bash
portfolio deposit 10000 --notes "Initial funding"
```

### Recording Trades

After executing a trade with your broker:

```bash
portfolio trade BUY AAPL 10 150.50 --fees 1.50 --notes "Entry position"
```

### Checking Portfolio

View your current portfolio anytime:

```bash
portfolio show
```

### Analyzing Stocks

```bash
portfolio analyze TSLA
```

### Reviewing History

Check your trade history:

```bash
portfolio history --days 7
```

## Tips

- Record trades immediately after execution
- Include fees for accurate P&L tracking
- Add notes to remember your reasoning
- Run analysis before major trades
- Check portfolio value regularly

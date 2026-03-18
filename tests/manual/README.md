# Manual Smoke Tests

Run these checks manually when validating live integrations.

## Local API flow
```
poetry run python tests/manual/api_smoke.py
```

## Price feed
```
poetry run python tests/manual/price_feed_smoke.py AAPL
```

## AI analysis
```
poetry run python tests/manual/analysis_smoke.py AAPL
```

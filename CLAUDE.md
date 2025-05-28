# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Architecture

This is a multi-agent trading bot system that follows a debate-driven decision making process:

**Data Flow**: Price/News Ingestion → Technical/Sentiment Analysis → Bull/Bear Agent Debate → Risk-Validated Decision → Mock Execution

**Key Components**:
- **Agents**: Bull/bear agents debate market conditions, DecisionManager makes final calls based on conviction threshold (|market_bias| > 0.3)
- **Data Ingestion**: Alpaca APIs for price data and news feeds
- **Features**: Technical analysis (RSI, MACD, EMA) and OpenAI-powered sentiment analysis
- **Risk Control**: Stop loss (2%), take profit (4%), max drawdown (15%), position sizing
- **Execution**: Paper trading with JSON logging

## Development Commands

**Run the trading bot**:
```bash
python main.py
```

**Test data ingestion**:
```bash
python test_data_ingestion.py
```

## Environment Setup

Required environment variables in `.env` file:
- `APCA-API-KEY-ID`: Alpaca API key
- `APCA-API-SECRET-KEY`: Alpaca secret key  
- `OPENAI_API_KEY`: OpenAI API key for sentiment analysis

Configuration managed via `config/settings.yaml` for technical parameters, risk thresholds, and trading settings.

## Key Dependencies

Core libraries: pandas, numpy, requests, openai, pyyaml, python-dotenv

## Architecture Notes

- Trading decisions require strong conviction (debate bias > 0.3) to execute
- All trades are paper trades logged to JSON files in execution/
- Technical indicators and risk parameters are configurable via settings.yaml
- The system operates on a 60-second loop for AAPL by default
- Bull and bear agents use the same data but analyze from opposing perspectives
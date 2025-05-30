"""
main.py - Entry point for the trading bot.

This script initializes and runs the TradingBot, which orchestrates data ingestion, analysis, decision-making,
risk management, capital allocation, and trade execution in a loop for a given trading symbol.
"""
import logging
from datetime import datetime
import time
import yaml

from data_ingestion.price_feed import PriceFeed
from data_ingestion.news_feed import NewsFeed
from data_ingestion.account_status import AccountStatus
from data_ingestion.open_positions import OpenPositions
from features.sentiment_agent import SentimentAgent
from agents.decision_manager import DecisionManager
from risk_control.risk_manager import RiskManager
from risk_control.capital_allocator import CapitalAllocator
from execution.mock_trader import MockTrader
from utils.formatting import setup_logger, format_price, format_percentage

logger = setup_logger('trading_bot')

class TradingBot:
    """
    TradingBot coordinates all components of the trading system, including data ingestion,
    sentiment analysis, decision making, risk management, capital allocation, and trade execution.

    Attributes:
        price_feed (PriceFeed): Fetches current and historical price data.
        news_feed (NewsFeed): Fetches news articles for sentiment analysis.
        sentiment_agent (SentimentAgent): Analyzes news for sentiment signals.
        decision_manager (DecisionManager): Makes trading decisions based on data and signals.
        risk_manager (RiskManager): Validates trades against risk parameters.
        capital_allocator (CapitalAllocator): Determines trade sizes and portfolio allocation.
        mock_trader (MockTrader): Simulates trade execution and tracks portfolio status.
        config (dict): Loaded configuration settings.
    """
    def __init__(self, config_path: str = 'config/settings.yaml'):
        """
        Initialize all trading bot components and load configuration.

        Args:
            config_path (str): Path to the YAML configuration file.
        """
        # Initialize all major components with config
        self.price_feed = PriceFeed(config_path)
        self.news_feed = NewsFeed(config_path)
        self.account_status = AccountStatus()
        self.open_positions = OpenPositions()
        self.sentiment_agent = SentimentAgent(config_path)
        self.decision_manager = DecisionManager(config_path)
        self.risk_manager = RiskManager(config_path)
        self.capital_allocator = CapitalAllocator(config_path)
        self.mock_trader = MockTrader(config_path)
        
        # Load trading symbols and other config
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def run(self, symbol: str):
        """
        Main trading loop for a given symbol. Ingests data, analyzes sentiment, makes decisions,
        validates risk, allocates capital, and executes trades in a continuous loop.

        Args:
            symbol (str): The trading symbol (e.g., 'AAPL', 'BTC/USD') to run the bot on.
        """
        logger.info(f"Starting trading bot for {symbol}")

        while True:
            try:
                # 1. Get current market data
                current_price = self.price_feed.get_current_price(symbol)
                if not current_price:
                    logger.error(f"Could not get price for {symbol}")
                    continue

                # 2. Get historical data for technical analysis
                historical_data = self.price_feed.get_historical_data(symbol)
                if not historical_data:
                    logger.error(f"Could not get historical data for {symbol}")
                    continue

                # 3. Get news data for sentiment analysis
                news_data = self.news_feed.get_news([symbol])
                
                # 4. Analyze data - extract prices and sentiment
                prices = [d['close'] for d in historical_data]
                sentiment_data = self.sentiment_agent.analyze_news(news_data)
                
                # 5. Get current account status and position for the symbol
                account_data = self.account_status.get_status()
                positions_data = self.open_positions.get_positions()
                
                # Find current position for the symbol
                current_position = None
                for pos in positions_data:
                    if pos.get('symbol') == symbol:
                        current_position = {
                            'symbol': pos.get('symbol'),
                            'side': 'LONG' if float(pos.get('qty', 0)) > 0 else 'SHORT',
                            'qty': abs(float(pos.get('qty', 0))),
                            'avg_entry_price': float(pos.get('avg_entry_price', 0)),
                            'market_value': float(pos.get('market_value', 0))
                        }
                        break
                
                # Get portfolio status for risk management
                equity = float(account_data.get('equity', 0))
                cash = float(account_data.get('cash', 0))
                
                # Calculate drawdown (assuming starting equity from config or initial value)
                # For now, using a simple calculation - could be improved with historical tracking
                initial_equity = cash + equity  # Simplified for demo
                current_drawdown = max(0, (initial_equity - equity) / initial_equity) if initial_equity > 0 else 0
                
                portfolio_status = {
                    'cash': cash,
                    'equity': equity,
                    'drawdown': current_drawdown,
                    'positions': {pos.get('symbol'): pos for pos in positions_data}
                }

                # 6. Make trading decision using all available data
                decision = self.decision_manager.make_decision(
                    prices,
                    sentiment_data,
                    current_position
                )

                # 7. Validate trade against risk parameters if not HOLD
                if decision['action'] != 'HOLD':
                    risk_validation = self.risk_manager.validate_trade(
                        decision,
                        portfolio_status
                    )

                    if not risk_validation['valid']:
                        logger.warning(f"Trade rejected: {risk_validation['reason']}")
                        continue

                    # 8. Calculate position size using capital allocator
                    trade_size = self.capital_allocator.calculate_trade_size(
                        portfolio_status['cash'],
                        portfolio_status['positions']
                    )
                    decision['size'] = trade_size

                # 9. Execute trade (or hold)
                trade_result = self.mock_trader.execute_trade(
                    decision,
                    symbol,
                    current_price
                )

                # 10. Log results and portfolio status
                logger.info(f"Trade executed: {trade_result}")
                logger.info(f"Portfolio status: {portfolio_status}")

                # 11. Sleep for a while before next iteration
                time.sleep(60)  # 1-minute interval

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    bot = TradingBot()
    bot.run("AAPL")  # Example: trading Apple stock

import logging
from datetime import datetime
import time
import yaml

from data_ingestion.price_feed import PriceFeed
from data_ingestion.news_feed import NewsFeed
from features.sentiment_agent import SentimentAgent
from agents.decision_manager import DecisionManager
from risk_control.risk_manager import RiskManager
from risk_control.capital_allocator import CapitalAllocator
from execution.mock_trader import MockTrader
from utils.formatting import setup_logger, format_price, format_percentage

logger = setup_logger('trading_bot')

class TradingBot:
    def __init__(self, config_path: str = 'config/settings.yaml'):
        # Initialize components
        self.price_feed = PriceFeed(config_path)
        self.news_feed = NewsFeed(config_path)
        self.sentiment_agent = SentimentAgent(config_path)
        self.decision_manager = DecisionManager(config_path)
        self.risk_manager = RiskManager(config_path)
        self.capital_allocator = CapitalAllocator(config_path)
        self.mock_trader = MockTrader(config_path)
        
        # Load trading symbols
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

    def run(self, symbol: str):
        """Main trading loop."""
        logger.info(f"Starting trading bot for {symbol}")

        while True:
            try:
                # Get current market data
                current_price = self.price_feed.get_current_price(symbol)
                if not current_price:
                    logger.error(f"Could not get price for {symbol}")
                    continue

                # Get historical data for technical analysis
                historical_data = self.price_feed.get_historical_data(symbol)
                if not historical_data:
                    logger.error(f"Could not get historical data for {symbol}")
                    continue

                # Get news data
                news_data = self.news_feed.get_news([symbol])
                
                # Analyze data - extract prices for CrewAI
                prices = [d['close'] for d in historical_data]
                sentiment_data = self.sentiment_agent.analyze_news(news_data)
                
                # Get current portfolio status
                portfolio_status = self.mock_trader.get_portfolio_status()
                current_position = portfolio_status['positions'].get(symbol)

                # Make trading decision using CrewAI
                decision = self.decision_manager.make_decision(
                    prices,
                    sentiment_data,
                    current_position
                )

                # Validate trade against risk parameters
                if decision['action'] != 'HOLD':
                    risk_validation = self.risk_manager.validate_trade(
                        decision,
                        portfolio_status
                    )

                    if not risk_validation['valid']:
                        logger.warning(f"Trade rejected: {risk_validation['reason']}")
                        continue

                    # Calculate position size
                    trade_size = self.capital_allocator.calculate_trade_size(
                        portfolio_status['cash'],
                        portfolio_status['positions']
                    )
                    decision['size'] = trade_size

                # Execute trade
                trade_result = self.mock_trader.execute_trade(
                    decision,
                    symbol,
                    current_price
                )

                # Log results
                logger.info(f"Trade executed: {trade_result}")
                logger.info(f"Portfolio status: {portfolio_status}")

                # Sleep for a while
                time.sleep(60)  # 1-minute interval

            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    bot = TradingBot()
    bot.run("AAPL")  # Example: trading Apple stock

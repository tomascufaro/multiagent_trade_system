import requests
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv

class PriceFeed:
    def __init__(self, config_path='analyst_service/config/settings.yaml'):
        load_dotenv()
        self.api_key = os.getenv('APCA_API_KEY_ID')
        self.secret_key = os.getenv('APCA_API_SECRET_KEY')
        self.base_url = "https://data.alpaca.markets/v1beta3/crypto/us/bars"

    def get_current_price(self, symbol: str) -> float:
        """Get the current price for a given symbol by fetching latest bar."""
        try:
            bars = self.get_historical_data(symbol, timeframe='1Min', limit=1)
            if bars and len(bars) > 0:
                return float(bars[0]['close'])
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request error for {symbol}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status: {e.response.status_code}, Content: {e.response.text}")
            return None
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return None

    def get_historical_data(self, symbol: str, timeframe: str = '1D', limit: int = 100, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get historical price data for a crypto symbol."""
        try:
            headers = {
                'APCA-API-KEY-ID': self.api_key,
                'APCA-API-SECRET-KEY': self.secret_key
            }
            
            start_time = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%dT%H:%M:%SZ')
            end_time = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
            
            params = {
                'symbols': symbol,
                'timeframe': timeframe,
                'start': start_time,
                'end': end_time,
                'limit': limit,
                'sort': 'desc'
            }

            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            bars = data.get('bars', {}).get(symbol, [])
            
            return [
                {
                    'timestamp': bar['t'],
                    'open': bar['o'],
                    'high': bar['h'],
                    'low': bar['l'],
                    'close': bar['c'],
                    'volume': bar['v']
                }
                for bar in bars
            ]
        except requests.exceptions.RequestException as e:
            print(f"Request error for {symbol}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Status: {e.response.status_code}, Content: {e.response.text}")
            return []
        except Exception as e:
            print(f"Error fetching historical data for {symbol}: {e}")
            return []


def main():
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_saver import save_data
    
    price_feed = PriceFeed()
    
    current_price = price_feed.get_current_price('BTC/USD')
    print(f"BTC current: ${current_price}")
    
    historical = price_feed.get_historical_data('BTC/USD', '1H', 5)
    print(f"Historical bars: {len(historical)}")
    if historical:
        latest = historical[0]
        print(f"Latest: O:{latest['open']} H:{latest['high']} L:{latest['low']} C:{latest['close']}")
    
    # Save data
    data = {
        'current_price': current_price,
        'historical_data': historical
    }
    filepath = save_data('price_feed', data)
    print(f"Data saved to: {filepath}")


if __name__ == "__main__":
    main()

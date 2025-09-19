import requests
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

class OpenPositions:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets/v2/positions"

    def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch open positions from Alpaca API, returning only selected fields."""
        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
            }
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Only keep the required fields for each position
            filtered = [
                {k: pos.get(k) for k in [
                    "asset_id", "symbol", "exchange", "asset_class", "avg_entry_price", "qty", "qty_available", "side", "market_value"
                ] if k in pos}
                for pos in data
            ]
            return filtered
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
                print(f"Response content: {e.response.text}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching open positions: {e}")
            return []

def main():
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_saver import save_data

    print("Testing OpenPositions...")
    open_positions = OpenPositions()
    positions = open_positions.get_positions()
    print("Open positions:")
    for pos in positions:
        print(pos)
    filepath = save_data('open_positions', positions)
    print(f"\nData saved to: {filepath}")

if __name__ == "__main__":
    main() 
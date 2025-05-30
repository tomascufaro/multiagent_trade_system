import requests
import os
from typing import Dict, Any
from dotenv import load_dotenv

class AccountStatus:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("APCA_API_KEY_ID")
        self.secret_key = os.getenv("APCA_API_SECRET_KEY")
        self.base_url = "https://paper-api.alpaca.markets/v2/account"

    def get_status(self) -> Dict[str, Any]:
        """Fetch account status from Alpaca API, returning only selected fields."""
        try:
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
            }
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
            data = response.json()
            # Only keep the required fields
            filtered = {k: data[k] for k in [
                "id", "account_number", "status", "currency", "cash", "equity"
            ] if k in data}
            return filtered
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response status code: {e.response.status_code}")
                print(f"Response headers: {dict(e.response.headers)}")
                print(f"Response content: {e.response.text}")
            return {}
        except Exception as e:
            print(f"Unexpected error fetching account status: {e}")
            return {}


def main():
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_saver import save_data

    print("Testing AccountStatus...")
    account_status = AccountStatus()
    status = account_status.get_status()
    print("Account status:")
    print(status)
    filepath = save_data('account_status', status)
    print(f"\nData saved to: {filepath}")

if __name__ == "__main__":
    main() 
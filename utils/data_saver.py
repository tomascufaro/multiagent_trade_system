import json
import os
from datetime import datetime
from typing import Any


def save_data(module_name: str, data: Any) -> str:
    """Save module output to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{module_name}_{timestamp}.json"
    filepath = os.path.join("data", filename)
    
    os.makedirs("data", exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    return filepath


def load_latest_data(module_name: str) -> Any:
    """Load the latest output from a module."""
    data_dir = "data"
    if not os.path.exists(data_dir):
        return None
    
    files = [f for f in os.listdir(data_dir) if f.startswith(f"{module_name}_")]
    if not files:
        return None
    
    latest_file = sorted(files)[-1]
    filepath = os.path.join(data_dir, latest_file)
    
    with open(filepath, 'r') as f:
        return json.load(f)
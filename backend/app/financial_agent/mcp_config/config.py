
import os
import json
from pathlib import Path

def load_mcp_config():
    config_path = Path(__file__).parent / "mcp_config.json"
    with open(config_path, 'r') as f:
        config_str = f.read()
    
    # Expand environment variables
    config_str = os.path.expandvars(config_str)
    
    return json.loads(config_str)

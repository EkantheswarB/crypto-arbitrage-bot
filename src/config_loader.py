import os
import yaml

def load_config(config_path="config/settings.yaml"):
    abs_path = os.path.join(os.path.dirname(__file__), "..", config_path)
    abs_path = os.path.abspath(abs_path)

    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Config file not found: {abs_path}")

    with open(abs_path, "r") as f:
        return yaml.safe_load(f)

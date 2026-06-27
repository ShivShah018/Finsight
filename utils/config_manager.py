"""
Manages local config file for saving login credentials (Remember Me).
Stores email + JWT token in ~/.finsight/config.json
Also loads .env file for configuration.
"""

import os
import json
from dotenv import load_dotenv

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".finsight")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def load_env():
    """Load .env file from project root. Safe to call multiple times."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(project_root, ".env")
    if os.path.isfile(env_path):
        load_dotenv(env_path)
    else:
        load_dotenv()


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def save_credentials(email: str, token: str) -> None:
    """Save credentials (email + JWT token) to local config."""
    _ensure_dir()
    data = {
        "email": email,
        "token": token,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)


def load_credentials() -> dict | None:
    """Load saved credentials. Returns {email, token} or None."""
    if not os.path.isfile(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        if "email" in data and "token" in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def clear_credentials() -> None:
    """Remove saved credentials file."""
    if os.path.isfile(CONFIG_PATH):
        os.remove(CONFIG_PATH)

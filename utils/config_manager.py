"""
Manages local config file for saving login credentials (Remember Me).
Stores email + plain password in ~/.finsight/config.json
"""

import os
import json

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".finsight")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")


def _ensure_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def save_credentials(email: str, password: str) -> None:
    """Save credentials to local config."""
    _ensure_dir()
    data = {
        "email": email,
        "password": password,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f)


def load_credentials() -> dict | None:
    """Load saved credentials. Returns {email, password} or None."""
    if not os.path.isfile(CONFIG_PATH):
        return None
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        if "email" in data and "password" in data:
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def clear_credentials() -> None:
    """Remove saved credentials file."""
    if os.path.isfile(CONFIG_PATH):
        os.remove(CONFIG_PATH)

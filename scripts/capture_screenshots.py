"""
Automated screenshot capture for FinSight README.
Usage:
  1. Run: uv run python scripts/seed_demo.py
  2. Run: uv run python main.py
  3. Login with: demo@finsight.app / demo123
  4. Once Dashboard is visible, run this script:
     uv run python scripts/capture_screenshots.py
"""
import time
import os
import sys
import pyautogui

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

SCREENSHOTS = {
    "screenshot_dashboard": "ctrl+d",
    "screenshot_add_tx":    "ctrl+n",
    "screenshot_goals":     "ctrl+g",
    "screenshot_budget":    "ctrl+b",
}

def capture():
    print("Screenshot capture starting in 3 seconds...")
    print("Make sure FinSight is running and you're logged in on Dashboard.")
    time.sleep(3)

    for name, shortcut in SCREENSHOTS.items():
        print(f"  Navigating to {name}...")
        key = shortcut.split("+")[1]
        pyautogui.hotkey("ctrl", key)
        time.sleep(1.5)

        path = os.path.join(ASSETS_DIR, f"{name}.png")
        img = pyautogui.screenshot()
        img.save(path)
        print(f"  Saved {path} ({img.size})")

    # Return to Dashboard
    pyautogui.hotkey("ctrl", "d")
    time.sleep(0.5)
    print("\nDone! 4 screenshots saved to assets/")

if __name__ == "__main__":
    capture()

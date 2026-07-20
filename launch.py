"""
launch.py

Convenience launcher — checks the venv, verifies the API key, then
starts the Streamlit UI. Run this instead of `streamlit run ui.py`
if you want the pre-flight checks.
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

load_dotenv()

def check_env():
    if not os.getenv("FOOTBALL_API_KEY"):
        print("ERROR: FOOTBALL_API_KEY not found in .env")
        print("Open .env, add your key, and try again.")
        sys.exit(1)

def check_packages():
    missing = []
    for pkg in ["streamlit", "pandas", "matplotlib", "requests", "PIL"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg if pkg != "PIL" else "pillow")
    if missing:
        print(f"Missing packages: {', '.join(missing)}")
        print(f"Run: pip install {' '.join(missing)}")
        sys.exit(1)

if __name__ == "__main__":
    print("World Cup Stat Bot — pre-flight checks...")
    check_env()
    check_packages()
    print("All checks passed. Opening UI in your browser...\n")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "ui.py",
         "--server.headless", "false",
         "--browser.gatherUsageStats", "false"],
        check=True,
    )

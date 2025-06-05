"""
Run script for the Flashgram Bot.

This script starts both the FastAPI server and the Telegram bot.
Make sure your PYTHONPATH includes the project root directory.
"""

import sys
import os
import threading

# Add the project root to the Python path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import after setting the path
from app.main import run_fastapi, start_bot

if __name__ == "__main__":
    # Start FastAPI server in background thread
    thread = threading.Thread(target=run_fastapi, daemon=True)
    thread.start()
    print("FastAPI server started in background")

    # Run the Telegram bot in the main thread
    print("Starting Telegram bot...")
    start_bot()
import threading
import uvicorn
import asyncio
import signal
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from pydantic import SecretStr

from app.my_telegram.bot import init_application
from app.config import settings, logger
from app.database import init_database, close_database

# Initialize FastAPI app
app = FastAPI(title=settings.app_name)

# Database client instance
db_client = None

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"Hello": "World!"}


# Function to run FastAPI server
def run_fastapi():
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=False)


# Main function to start the Telegram bot
def start_bot():
    global db_client
    
    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully."""
        logger.info("Received interrupt signal. Shutting down gracefully...")
        if db_client:
            try:
                # Create a new event loop for cleanup if needed
                cleanup_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(cleanup_loop)
                cleanup_loop.run_until_complete(close_database(db_client))
                logger.info("Database connection closed successfully")
                cleanup_loop.close()
            except Exception as e:
                logger.error(f"Error during database cleanup: {e}")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        logger.info("Initializing database...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Initialize DB in this loop
        db_client, _ = loop.run_until_complete(init_database())

        # Start bot — this call will manage its own loop
        bot = init_application(settings.token)
        logger.info("Starting Telegram bot...")
        bot.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        if db_client:
            try:
                loop.run_until_complete(close_database(db_client))
                loop.close()
            except RuntimeError:
                # Loop might be closed already, create a new one
                cleanup_loop = asyncio.new_event_loop()
                cleanup_loop.run_until_complete(close_database(db_client))
                cleanup_loop.close()


# Entry point
if __name__ == "__main__":
    # Start FastAPI server in background thread
    thread = threading.Thread(target=run_fastapi, daemon=True)
    thread.start()
    logger.info("FastAPI server started in background")

    # Run the Telegram bot in the main thread
    start_bot()

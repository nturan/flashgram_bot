import threading
import uvicorn
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update
from pydantic import SecretStr

from app.my_telegram.bot import init_application
from app.config import settings, logger

# Initialize FastAPI app
app = FastAPI(title=settings.app_name)

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

# Main async function to start the Telegram bot
def start_bot():
    # Initialize the bot
    bot = init_application(settings.token)
    logger.info("Starting Telegram bot...")
    bot.run_polling(allowed_updates=Update.ALL_TYPES)

# Entry point
if __name__ == "__main__":
    # Start FastAPI server in background thread
    thread = threading.Thread(target=run_fastapi, daemon=True)
    thread.start()
    logger.info("FastAPI server started in background")

    # Run the Telegram bot in the main thread
    start_bot()

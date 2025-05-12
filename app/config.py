from pydantic_settings import BaseSettings
import os
import sys
from dotenv import load_dotenv
import logging

load_dotenv()


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    app_name: str = "Flashgram Bot"
    token: str = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        logger.error("No token found!")
        sys.exit(1)


settings = Settings()

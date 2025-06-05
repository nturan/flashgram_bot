from pydantic_settings import BaseSettings
from pydantic import SecretStr
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
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")

    if not token:
        logger.error("No Telegram token found!")
        sys.exit(1)

    if not openai_api_key:
        logger.error("No OpenAI API key found!")
        sys.exit(1)


settings = Settings()

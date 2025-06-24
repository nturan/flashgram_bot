"""User lifecycle middleware for automatic user creation and management."""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.models.users import User
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


async def ensure_user_exists(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ensure user exists in database before processing any request."""
    if update.effective_user:
        telegram_user = update.effective_user
        user_service = UserService()
        
        try:
            # Get or create user with telegram details
            user = await user_service.get_or_create_user(
                telegram_user_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name
            )
            
            if user:
                logger.debug(f"User ensured for Telegram ID {telegram_user.id}: {user.get_display_name()}")
            else:
                logger.error(f"Failed to ensure user exists for Telegram ID {telegram_user.id}")
                
        except Exception as e:
            logger.error(f"Error ensuring user exists for Telegram ID {telegram_user.id}: {e}")
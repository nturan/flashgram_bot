"""User service using Beanie ODM."""

import logging
from typing import Optional
from app.models.users import User, UserStatus
from app.common.encryption import get_encryption_manager

logger = logging.getLogger(__name__)


class UserService:
    """Service for user operations using Beanie ODM."""

    async def get_user_by_telegram_id(self, telegram_user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        try:
            user = await User.find_one(User.telegram_user_id == telegram_user_id)
            return user
        except Exception as e:
            logger.error(f"Error getting user by Telegram ID: {e}")
            return None

    async def create_user(
        self, 
        telegram_user_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None, 
        last_name: Optional[str] = None
    ) -> Optional[User]:
        """Create a new user."""
        try:
            user = User(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            await user.insert()
            logger.info(f"Created user with Telegram ID: {telegram_user_id}")
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    async def get_or_create_user(
        self, 
        telegram_user_id: int, 
        username: Optional[str] = None,
        first_name: Optional[str] = None, 
        last_name: Optional[str] = None
    ) -> Optional[User]:
        """Get existing user or create new one."""
        try:
            # Try to find existing user
            user = await self.get_user_by_telegram_id(telegram_user_id)
            
            if user:
                # Update last active time
                user.update_last_active()
                await user.save()
                return user
            
            # Create new user
            return await self.create_user(telegram_user_id, username, first_name, last_name)
            
        except Exception as e:
            logger.error(f"Error in get_or_create_user: {e}")
            return None

    async def update_user_api_key(self, telegram_user_id: int, encrypted_api_key: str) -> bool:
        """Update user's encrypted API key."""
        try:
            user = await self.get_user_by_telegram_id(telegram_user_id)
            if not user:
                return False
            
            user.encrypted_openai_api_key = encrypted_api_key
            user.api_key_set = True
            user.update_last_active()
            await user.save()
            
            logger.info(f"Updated API key for user {telegram_user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user API key: {e}")
            return False

    async def get_user_api_key(self, telegram_user_id: int) -> Optional[str]:
        """Get user's decrypted API key."""
        try:
            user = await self.get_user_by_telegram_id(telegram_user_id)
            if user and user.has_custom_api_key():
                encryption_manager = get_encryption_manager()
                return encryption_manager.decrypt_api_key(user.encrypted_openai_api_key)
            return None
        except Exception as e:
            logger.error(f"Error getting user API key: {e}")
            return None

    async def update_user_status(self, telegram_user_id: int, status: UserStatus) -> bool:
        """Update user's status."""
        try:
            user = await self.get_user_by_telegram_id(telegram_user_id)
            if not user:
                return False
            
            user.status = status
            user.update_last_active()
            await user.save()
            
            logger.info(f"Updated status for user {telegram_user_id} to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating user status: {e}")
            return False


# Global service instance
user_service = UserService()
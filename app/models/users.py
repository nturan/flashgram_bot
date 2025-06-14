"""User models using Beanie documents for MongoDB integration."""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Document):
    """User document with encrypted API key storage."""
    
    # Identification - indexed for fast lookups
    telegram_user_id: Indexed(int, unique=True) = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="User's first name")
    last_name: Optional[str] = Field(None, description="User's last name")
    
    # Account information
    status: UserStatus = Field(default=UserStatus.ACTIVE, description="Account status")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Account creation timestamp")
    last_active: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    
    # API key (encrypted)
    encrypted_openai_api_key: Optional[str] = Field(None, description="Encrypted OpenAI API key")
    api_key_set: bool = Field(default=False, description="Whether user has set their own API key")

    class Settings:
        name = "users"

    def get_display_name(self) -> str:
        """Get user's display name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User {self.telegram_user_id}"
    
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self.status == UserStatus.ACTIVE
    
    def has_custom_api_key(self) -> bool:
        """Check if user has set their own API key."""
        return self.api_key_set and self.encrypted_openai_api_key is not None
    
    def update_last_active(self) -> None:
        """Update last active timestamp."""
        self.last_active = datetime.utcnow()

    @classmethod
    async def find_by_telegram_id(cls, telegram_user_id: int) -> Optional["User"]:
        """Find user by Telegram ID."""
        return await cls.find_one(cls.telegram_user_id == telegram_user_id)

    @classmethod
    async def get_or_create_user(cls, telegram_user_id: int, username: Optional[str] = None, 
                               first_name: Optional[str] = None, last_name: Optional[str] = None) -> "User":
        """Get existing user or create new one."""
        user = await cls.find_by_telegram_id(telegram_user_id)
        if user:
            user.update_last_active()
            await user.save()
            return user
        
        # Create new user
        user = cls(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        await user.insert()
        return user
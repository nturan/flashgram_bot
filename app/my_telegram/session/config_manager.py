"""User configuration management for the Telegram bot."""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class UserConfig:
    """Represents a user's configuration settings."""

    user_id: int

    # Available settings
    model: str = "gpt-4o"  # Default model
    confirm_flashcards: bool = False  # Default flashcard confirmation setting
    cards_per_session: int = 20  # Default number of cards per learning session

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "model": self.model,
            "confirm_flashcards": self.confirm_flashcards,
            "cards_per_session": self.cards_per_session,
        }

    def update_setting(self, setting_name: str, value: Any) -> bool:
        """Update a specific setting.

        Args:
            setting_name: Name of the setting to update
            value: New value for the setting

        Returns:
            True if setting was updated successfully, False otherwise
        """
        if setting_name == "model":
            if isinstance(value, str):
                self.model = value
                return True
        elif setting_name == "confirm_flashcards":
            if isinstance(value, bool):
                self.confirm_flashcards = value
                return True
            elif isinstance(value, str):
                # Handle string boolean values
                if value.lower() in ["true", "yes", "1", "on"]:
                    self.confirm_flashcards = True
                    return True
                elif value.lower() in ["false", "no", "0", "off"]:
                    self.confirm_flashcards = False
                    return True
        elif setting_name == "cards_per_session":
            if isinstance(value, int) and 1 <= value <= 10000:
                self.cards_per_session = value
                return True
            elif isinstance(value, str):
                try:
                    int_value = int(value)
                    if 1 <= int_value <= 100:
                        self.cards_per_session = int_value
                        return True
                except ValueError:
                    pass

        return False

    def get_setting(self, setting_name: str) -> Optional[Any]:
        """Get a specific setting value.

        Args:
            setting_name: Name of the setting to get

        Returns:
            Setting value or None if setting doesn't exist
        """
        if setting_name == "model":
            return self.model
        elif setting_name == "confirm_flashcards":
            return self.confirm_flashcards
        elif setting_name == "cards_per_session":
            return self.cards_per_session
        return None


class ConfigManager:
    """Manages user configurations for the Telegram bot."""

    def __init__(self):
        self._configs: Dict[int, UserConfig] = {}

    def get_config(self, user_id: int) -> UserConfig:
        """Get or create a user configuration.

        Args:
            user_id: Telegram user ID

        Returns:
            UserConfig object
        """
        if user_id not in self._configs:
            self._configs[user_id] = UserConfig(user_id=user_id)

        return self._configs[user_id]

    def update_setting(self, user_id: int, setting_name: str, value: Any) -> bool:
        """Update a user's setting.

        Args:
            user_id: Telegram user ID
            setting_name: Name of the setting to update
            value: New value for the setting

        Returns:
            True if setting was updated successfully, False otherwise
        """
        config = self.get_config(user_id)
        success = config.update_setting(setting_name, value)

        if success:
            logger.info(
                f"Updated setting '{setting_name}' to '{value}' for user {user_id}"
            )
        else:
            logger.warning(
                f"Failed to update setting '{setting_name}' to '{value}' for user {user_id}"
            )

        return success

    def get_setting(self, user_id: int, setting_name: str) -> Optional[Any]:
        """Get a user's setting value.

        Args:
            user_id: Telegram user ID
            setting_name: Name of the setting to get

        Returns:
            Setting value or None if setting doesn't exist
        """
        config = self.get_config(user_id)
        return config.get_setting(setting_name)

    def get_all_settings(self, user_id: int) -> Dict[str, Any]:
        """Get all settings for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary of all settings
        """
        config = self.get_config(user_id)
        return config.to_dict()

    def get_available_settings(self) -> Dict[str, str]:
        """Get all available settings with descriptions.

        Returns:
            Dictionary mapping setting names to descriptions
        """
        return {
            "model": "LLM model name (e.g., gpt-4o, gpt-4o-mini)",
            "confirm_flashcards": "Whether to ask for confirmation before creating flashcards (true/false)",
            "cards_per_session": "Number of flashcards per learning session (1-100, default: 20)",
        }


# Global config manager instance
config_manager = ConfigManager()

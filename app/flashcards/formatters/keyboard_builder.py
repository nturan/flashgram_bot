"""Inline keyboard builders for flashcard interactions."""

import logging
from typing import Optional, Any
from app.models.flashcards import Flashcard, FlashcardType
from app.common.telegram_utils import (
    create_edit_delete_keyboard,
    create_multiple_choice_keyboard,
)

logger = logging.getLogger(__name__)


class KeyboardBuilder:
    """Builds inline keyboards for flashcard interactions."""

    def create_edit_delete_keyboard(self, flashcard: Flashcard) -> Optional[Any]:
        """Create inline keyboard with edit and delete buttons for non-multiple choice cards."""
        try:
            return create_edit_delete_keyboard(
                item_id=str(flashcard.id), show_answer=True
            )
        except Exception as e:
            logger.error(f"Error creating edit/delete keyboard: {e}")
            return None

    def create_multiple_choice_keyboard_with_controls(
        self, flashcard: Flashcard
    ) -> Optional[Any]:
        """Create inline keyboard for multiple choice questions with edit/delete controls."""
        try:
            options = flashcard.content.get('options', [])
            return create_multiple_choice_keyboard(
                options=options,
                item_id=str(flashcard.id),
                include_controls=True,
            )
        except Exception as e:
            logger.error(f"Error creating multiple choice keyboard with controls: {e}")
            return None

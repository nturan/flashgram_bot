"""Question formatting for Telegram bot display."""

import logging
from typing import Tuple, Optional, Any
from app.flashcards.models import (
    FlashcardUnion,
    TwoSidedCard,
    FillInTheBlank,
    MultipleChoice,
)
from app.common.text_processing import escape_markdown
from .keyboard_builder import KeyboardBuilder

logger = logging.getLogger(__name__)


class QuestionFormatter:
    """Formats flashcard questions for display in the Telegram bot."""

    def __init__(self):
        self.keyboard_builder = KeyboardBuilder()

    def format_question_for_bot(
        self, flashcard: FlashcardUnion
    ) -> Tuple[str, Optional[Any]]:
        """Format a flashcard question for display in the Telegram bot.
        Returns (question_text, optional_keyboard)"""
        try:
            if isinstance(flashcard, TwoSidedCard):
                return self._format_two_sided_card(flashcard)

            elif isinstance(flashcard, FillInTheBlank):
                return self._format_fill_in_blank_card(flashcard)

            elif isinstance(flashcard, MultipleChoice):
                return self._format_multiple_choice_card(flashcard)

            else:
                return f"❓ Unknown flashcard type: {flashcard.type}", None

        except Exception as e:
            logger.error(f"Error formatting question: {e}")
            return "❌ Error displaying question", None

    def _format_two_sided_card(
        self, flashcard: TwoSidedCard
    ) -> Tuple[str, Optional[Any]]:
        """Format a two-sided flashcard."""
        text = f"📝 *Two-sided Card*\n\n{flashcard.front}"
        keyboard = self.keyboard_builder.create_edit_delete_keyboard(flashcard)
        return text, keyboard

    def _format_fill_in_blank_card(
        self, flashcard: FillInTheBlank
    ) -> Tuple[str, Optional[Any]]:
        """Format a fill-in-the-blank flashcard."""
        question = flashcard.get_question()

        # Escape markdown special characters in the question
        escaped_question = escape_markdown(question)

        # Get the grammatical form hint from metadata
        form_hint = "the missing ending"
        if hasattr(flashcard, "metadata") and flashcard.metadata:
            grammatical_key = flashcard.metadata.get("grammatical_key", "")
            dictionary_form = flashcard.metadata.get("dictionary_form", "")
            if grammatical_key and dictionary_form:
                form_hint = f"{grammatical_key} of '{dictionary_form}'"

        text = (
            f"📝 *Fill in the Blank*\n\n{escaped_question}\n\n"
            f"💡 *Hint:* Complete the {form_hint}"
        )

        # Create keyboard with edit/delete buttons
        keyboard = self.keyboard_builder.create_edit_delete_keyboard(flashcard)
        return text, keyboard

    def _format_multiple_choice_card(
        self, flashcard: MultipleChoice
    ) -> Tuple[str, Optional[Any]]:
        """Format a multiple choice flashcard."""
        question = flashcard.get_question()
        choice_type = "multiple answers" if flashcard.allow_multiple else "one answer"
        text = f"📝 *Multiple Choice* (select {choice_type})\n\n{question}"

        # Create inline keyboard with options and edit/delete buttons
        keyboard = self.keyboard_builder.create_multiple_choice_keyboard_with_controls(
            flashcard
        )
        return text, keyboard

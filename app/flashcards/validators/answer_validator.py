"""Answer validation logic for different flashcard types."""

import logging
from typing import Tuple, List
from app.models.flashcards import Flashcard, FlashcardType
from .input_parser import InputParser

logger = logging.getLogger(__name__)


class AnswerValidator:
    """Validates user answers against flashcard correct answers."""

    def __init__(self):
        self.input_parser = InputParser()

    def check_answer(
        self, flashcard: Flashcard, user_input: str
    ) -> Tuple[bool, str]:
        """
        Check if the user's answer is correct and return feedback.
        Returns (is_correct, feedback_message)
        """
        try:
            if flashcard.type == FlashcardType.TWO_SIDED:
                return self._check_two_sided_answer(flashcard, user_input)

            elif flashcard.type == FlashcardType.FILL_IN_BLANK:
                return self._check_fill_in_blank_answer(flashcard, user_input)

            elif flashcard.type == FlashcardType.MULTIPLE_CHOICE:
                return self._check_multiple_choice_answer(flashcard, user_input)

            else:
                return False, "❌ Unknown flashcard type"

        except Exception as e:
            logger.error(f"Error checking answer: {e}")
            return False, "❌ Error checking answer"

    def _check_two_sided_answer(
        self, flashcard: Flashcard, user_input: str
    ) -> Tuple[bool, str]:
        """Check answer for two-sided flashcard."""
        is_correct = flashcard.check_answer(user_input)
        back = flashcard.content.get('back', '')
        feedback = (
            f"✅ Correct!"
            if is_correct
            else f"❌ Incorrect. The answer is: {back}"
        )
        return is_correct, feedback

    def _check_fill_in_blank_answer(
        self, flashcard: Flashcard, user_input: str
    ) -> Tuple[bool, str]:
        """Check answer for fill-in-the-blank flashcard."""
        # Parse user input for multiple blanks
        answers = flashcard.content.get('answers', [])
        user_answers = self.input_parser.parse_fill_in_blank_answer(
            user_input, len(answers)
        )
        is_correct = flashcard.check_answer(user_answers)

        if is_correct:
            feedback = "✅ Correct!"
        else:
            correct_answers = ", ".join(answers)
            feedback = f"❌ Incorrect. The correct answers are: {correct_answers}"

        return is_correct, feedback

    def _check_multiple_choice_answer(
        self, flashcard: Flashcard, user_input: str
    ) -> Tuple[bool, str]:
        """Check answer for multiple choice flashcard."""
        # Parse user input for multiple choice
        options = flashcard.content.get('options', [])
        correct_indices = flashcard.content.get('correct_indices', [])
        selected_indices = self.input_parser.parse_multiple_choice_answer(
            user_input, len(options)
        )
        is_correct = flashcard.check_answer(selected_indices)

        if is_correct:
            feedback = "✅ Correct!"
        else:
            correct_letters = [chr(65 + i) for i in correct_indices]
            correct_str = ", ".join(correct_letters)
            feedback = f"❌ Incorrect. The correct answer{'s' if len(correct_letters) > 1 else ''}: {correct_str}"

        return is_correct, feedback

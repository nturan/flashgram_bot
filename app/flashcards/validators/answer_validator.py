"""Answer validation logic for different flashcard types."""

import logging
from typing import Tuple, List
from app.flashcards.models import FlashcardUnion, TwoSidedCard, FillInTheBlank, MultipleChoice
from .input_parser import InputParser

logger = logging.getLogger(__name__)


class AnswerValidator:
    """Validates user answers against flashcard correct answers."""
    
    def __init__(self):
        self.input_parser = InputParser()
    
    def check_answer(self, flashcard: FlashcardUnion, user_input: str) -> Tuple[bool, str]:
        """
        Check if the user's answer is correct and return feedback.
        Returns (is_correct, feedback_message)
        """
        try:
            if isinstance(flashcard, TwoSidedCard):
                return self._check_two_sided_answer(flashcard, user_input)
            
            elif isinstance(flashcard, FillInTheBlank):
                return self._check_fill_in_blank_answer(flashcard, user_input)
            
            elif isinstance(flashcard, MultipleChoice):
                return self._check_multiple_choice_answer(flashcard, user_input)
            
            else:
                return False, "❌ Unknown flashcard type"
                
        except Exception as e:
            logger.error(f"Error checking answer: {e}")
            return False, "❌ Error checking answer"
    
    def _check_two_sided_answer(self, flashcard: TwoSidedCard, user_input: str) -> Tuple[bool, str]:
        """Check answer for two-sided flashcard."""
        is_correct = flashcard.check_answer(user_input)
        feedback = f"✅ Correct!" if is_correct else f"❌ Incorrect. The answer is: {flashcard.back}"
        return is_correct, feedback
    
    def _check_fill_in_blank_answer(self, flashcard: FillInTheBlank, user_input: str) -> Tuple[bool, str]:
        """Check answer for fill-in-the-blank flashcard."""
        # Parse user input for multiple blanks
        user_answers = self.input_parser.parse_fill_in_blank_answer(user_input, flashcard.get_blank_count())
        is_correct = flashcard.check_answer(user_answers)
        
        if is_correct:
            feedback = "✅ Correct!"
        else:
            correct_answers = ", ".join(flashcard.answers)
            feedback = f"❌ Incorrect. The correct answers are: {correct_answers}"
        
        return is_correct, feedback
    
    def _check_multiple_choice_answer(self, flashcard: MultipleChoice, user_input: str) -> Tuple[bool, str]:
        """Check answer for multiple choice flashcard."""
        # Parse user input for multiple choice
        selected_indices = self.input_parser.parse_multiple_choice_answer(user_input, len(flashcard.options))
        is_correct = flashcard.check_answer(selected_indices)
        
        if is_correct:
            feedback = "✅ Correct!"
        else:
            correct_letters = flashcard.get_correct_letters()
            correct_str = ", ".join(correct_letters)
            feedback = f"❌ Incorrect. The correct answer{'s' if len(correct_letters) > 1 else ''}: {correct_str}"
        
        return is_correct, feedback
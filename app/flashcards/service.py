import logging
import random
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime

from app.flashcards.models import (
    FlashcardUnion, 
    FlashcardType, 
    TwoSidedCard, 
    FillInTheBlank, 
    MultipleChoice
)
from app.flashcards.database import flashcard_db_v2

logger = logging.getLogger(__name__)

class FlashcardService:
    """Service layer for handling flashcard operations in the bot."""
    
    def __init__(self):
        self.db = flashcard_db_v2
    
    def get_learning_session_flashcards(self, limit: int = 20) -> List[FlashcardUnion]:
        """Get flashcards for a learning session."""
        try:
            # Get due flashcards first
            due_cards = self.db.get_due_flashcards(limit=limit)
            
            # If we don't have enough due cards, get some random ones
            if len(due_cards) < limit:
                remaining = limit - len(due_cards)
                all_cards = self.db.get_flashcards(limit=remaining * 2)  # Get more to filter out due ones
                
                # Filter out cards that are already in due_cards
                due_ids = {card.id for card in due_cards if card.id}
                additional_cards = [card for card in all_cards if card.id not in due_ids]
                
                # Take only what we need
                additional_cards = additional_cards[:remaining]
                due_cards.extend(additional_cards)
            
            # Shuffle for random order
            random.shuffle(due_cards)
            
            logger.info(f"Retrieved {len(due_cards)} flashcards for learning session")
            return due_cards
            
        except Exception as e:
            logger.error(f"Error getting learning session flashcards: {e}")
            return []
    
    def format_question_for_bot(self, flashcard: FlashcardUnion) -> str:
        """Format a flashcard question for display in the Telegram bot."""
        try:
            if isinstance(flashcard, TwoSidedCard):
                return f"📝 *Two-sided Card*\n\n{flashcard.front}"
            
            elif isinstance(flashcard, FillInTheBlank):
                question = flashcard.get_question()
                blank_count = flashcard.get_blank_count()
                return (f"📝 *Fill in the Blank*\n\n{question}\n\n"
                       f"💡 *Hint:* Fill in {blank_count} blank{'s' if blank_count > 1 else ''}")
            
            elif isinstance(flashcard, MultipleChoice):
                question = flashcard.get_question()
                choice_type = "multiple answers" if flashcard.allow_multiple else "one answer"
                return f"📝 *Multiple Choice* (select {choice_type})\n\n{question}"
            
            else:
                return f"❓ Unknown flashcard type: {flashcard.type}"
                
        except Exception as e:
            logger.error(f"Error formatting question: {e}")
            return "❌ Error displaying question"
    
    def check_answer(self, flashcard: FlashcardUnion, user_input: str) -> Tuple[bool, str]:
        """
        Check if the user's answer is correct and return feedback.
        Returns (is_correct, feedback_message)
        """
        try:
            if isinstance(flashcard, TwoSidedCard):
                is_correct = flashcard.check_answer(user_input)
                feedback = f"✅ Correct!" if is_correct else f"❌ Incorrect. The answer is: {flashcard.back}"
                return is_correct, feedback
            
            elif isinstance(flashcard, FillInTheBlank):
                # Parse user input for multiple blanks
                user_answers = self._parse_fill_in_blank_answer(user_input, flashcard.get_blank_count())
                is_correct = flashcard.check_answer(user_answers)
                
                if is_correct:
                    feedback = "✅ Correct!"
                else:
                    correct_answers = ", ".join(flashcard.answers)
                    feedback = f"❌ Incorrect. The correct answers are: {correct_answers}"
                
                return is_correct, feedback
            
            elif isinstance(flashcard, MultipleChoice):
                # Parse user input for multiple choice
                selected_indices = self._parse_multiple_choice_answer(user_input, len(flashcard.options))
                is_correct = flashcard.check_answer(selected_indices)
                
                if is_correct:
                    feedback = "✅ Correct!"
                else:
                    correct_letters = flashcard.get_correct_letters()
                    correct_str = ", ".join(correct_letters)
                    feedback = f"❌ Incorrect. The correct answer{'s' if len(correct_letters) > 1 else ''}: {correct_str}"
                
                return is_correct, feedback
            
            else:
                return False, "❌ Unknown flashcard type"
                
        except Exception as e:
            logger.error(f"Error checking answer: {e}")
            return False, "❌ Error checking answer"
    
    def _parse_fill_in_blank_answer(self, user_input: str, expected_count: int) -> List[str]:
        """Parse user input for fill-in-the-blank questions."""
        # Split by common delimiters
        separators = [',', ';', '|', '\n']
        answers = [user_input.strip()]
        
        for sep in separators:
            if sep in user_input:
                answers = [ans.strip() for ans in user_input.split(sep)]
                break
        
        # Ensure we have the right number of answers
        while len(answers) < expected_count:
            answers.append("")
        
        return answers[:expected_count]
    
    def _parse_multiple_choice_answer(self, user_input: str, option_count: int) -> List[int]:
        """Parse user input for multiple choice questions."""
        user_input = user_input.upper().strip()
        selected_indices = []
        
        # Handle letter inputs (A, B, C, etc.)
        for char in user_input:
            if char.isalpha():
                index = ord(char) - ord('A')
                if 0 <= index < option_count and index not in selected_indices:
                    selected_indices.append(index)
        
        # Handle number inputs (1, 2, 3, etc.)
        if not selected_indices:
            for char in user_input:
                if char.isdigit():
                    index = int(char) - 1  # Convert to 0-based
                    if 0 <= index < option_count and index not in selected_indices:
                        selected_indices.append(index)
        
        return sorted(selected_indices)
    
    def update_flashcard_after_review(self, flashcard: FlashcardUnion, is_correct: bool) -> bool:
        """Update flashcard statistics and spaced repetition data after review."""
        try:
            if not flashcard.id:
                logger.error("Cannot update flashcard without ID")
                return False
            
            # Simple spaced repetition algorithm (simplified SM-2)
            new_ease_factor = flashcard.ease_factor
            new_interval = flashcard.interval_days
            
            if is_correct:
                if flashcard.repetition_count == 0:
                    new_interval = 1
                elif flashcard.repetition_count == 1:
                    new_interval = 6
                else:
                    new_interval = int(flashcard.interval_days * flashcard.ease_factor)
                
                new_ease_factor = max(1.3, flashcard.ease_factor + 0.1)
            else:
                new_interval = 1
                new_ease_factor = max(1.3, flashcard.ease_factor - 0.2)
            
            # Calculate new due date
            new_due_date = datetime.now()
            new_due_date = new_due_date.replace(
                hour=new_due_date.hour + (new_interval * 24)
            )
            
            # Update in database
            return self.db.update_flashcard_stats(
                flashcard.id,
                is_correct,
                new_due_date,
                new_interval,
                new_ease_factor
            )
            
        except Exception as e:
            logger.error(f"Error updating flashcard after review: {e}")
            return False
    
    def get_flashcard_stats(self) -> Dict[str, Any]:
        """Get statistics about the flashcard collection."""
        try:
            total_count = self.db.get_flashcard_count()
            two_sided_count = self.db.get_flashcard_count(FlashcardType.TWO_SIDED)
            fill_blank_count = self.db.get_flashcard_count(FlashcardType.FILL_IN_BLANK)
            multiple_choice_count = self.db.get_flashcard_count(FlashcardType.MULTIPLE_CHOICE)
            
            due_count = len(self.db.get_due_flashcards(limit=1000))  # Get a large number to count
            tags = self.db.get_tags()
            
            return {
                "total": total_count,
                "two_sided": two_sided_count,
                "fill_in_blank": fill_blank_count,
                "multiple_choice": multiple_choice_count,
                "due_for_review": due_count,
                "unique_tags": len(tags),
                "tags": tags[:10]  # Show first 10 tags
            }
            
        except Exception as e:
            logger.error(f"Error getting flashcard stats: {e}")
            return {}

# Global service instance
flashcard_service = FlashcardService()
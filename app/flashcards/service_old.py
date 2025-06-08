import logging
import random
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

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
    
    def format_question_for_bot(self, flashcard: FlashcardUnion) -> tuple[str, Optional[Any]]:
        """Format a flashcard question for display in the Telegram bot.
        Returns (question_text, optional_keyboard)"""
        try:
            if isinstance(flashcard, TwoSidedCard):
                text = f"📝 *Two-sided Card*\n\n{flashcard.front}"
                keyboard = self._create_edit_delete_keyboard(flashcard)
                return text, keyboard
            
            elif isinstance(flashcard, FillInTheBlank):
                question = flashcard.get_question()
                
                # Escape markdown special characters in the question
                escaped_question = self._escape_markdown(question)
                
                # Get the grammatical form hint from metadata
                form_hint = "the missing ending"
                if hasattr(flashcard, 'metadata') and flashcard.metadata:
                    grammatical_key = flashcard.metadata.get('grammatical_key', '')
                    dictionary_form = flashcard.metadata.get('dictionary_form', '')
                    if grammatical_key and dictionary_form:
                        form_hint = f"{grammatical_key} of '{dictionary_form}'"
                
                text = (f"📝 *Fill in the Blank*\n\n{escaped_question}\n\n"
                       f"💡 *Hint:* Complete the {form_hint}")
                
                # Create keyboard with edit/delete buttons
                keyboard = self._create_edit_delete_keyboard(flashcard)
                return text, keyboard
            
            elif isinstance(flashcard, MultipleChoice):
                question = flashcard.get_question()
                choice_type = "multiple answers" if flashcard.allow_multiple else "one answer"
                text = f"📝 *Multiple Choice* (select {choice_type})\n\n{question}"
                
                # Create inline keyboard with options and edit/delete buttons
                keyboard = self._create_multiple_choice_keyboard_with_controls(flashcard)
                return text, keyboard
            
            else:
                return f"❓ Unknown flashcard type: {flashcard.type}", None
                
        except Exception as e:
            logger.error(f"Error formatting question: {e}")
            return "❌ Error displaying question", None
    
    def _create_multiple_choice_keyboard(self, flashcard: MultipleChoice):
        """Create inline keyboard for multiple choice questions."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            buttons = []
            for i, option in enumerate(flashcard.options):
                # Create callback data with flashcard ID and option index
                callback_data = f"mc_{flashcard.id}_{i}"
                button = InlineKeyboardButton(
                    text=f"{chr(65 + i)}. {option}",  # A, B, C, etc.
                    callback_data=callback_data
                )
                buttons.append([button])  # Each button on its own row
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Error creating multiple choice keyboard: {e}")
            return None
    
    def _create_multiple_choice_keyboard_with_controls(self, flashcard: MultipleChoice):
        """Create inline keyboard for multiple choice questions with edit/delete controls."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            buttons = []
            
            # Add option buttons
            for i, option in enumerate(flashcard.options):
                callback_data = f"mc_{flashcard.id}_{i}"
                button = InlineKeyboardButton(
                    text=f"{chr(65 + i)}. {option}",  # A, B, C, etc.
                    callback_data=callback_data
                )
                buttons.append([button])  # Each button on its own row
            
            # Add control buttons row
            control_buttons = [
                InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{flashcard.id}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{flashcard.id}")
            ]
            buttons.append(control_buttons)
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Error creating multiple choice keyboard with controls: {e}")
            return None
    
    def _create_edit_delete_keyboard(self, flashcard):
        """Create inline keyboard with edit and delete buttons for non-multiple choice cards."""
        try:
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            
            buttons = [
                [
                    InlineKeyboardButton("✏️ Edit Card", callback_data=f"edit_{flashcard.id}"),
                    InlineKeyboardButton("🗑️ Delete Card", callback_data=f"delete_{flashcard.id}")
                ],
                [
                    InlineKeyboardButton("📝 Answer", callback_data=f"answer_{flashcard.id}")
                ]
            ]
            
            return InlineKeyboardMarkup(buttons)
            
        except Exception as e:
            logger.error(f"Error creating edit/delete keyboard: {e}")
            return None
    
    def _escape_markdown(self, text: str) -> str:
        """Escape markdown special characters to prevent parsing errors."""
        try:
            # Characters that need escaping in Telegram markdown
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            
            escaped_text = text
            for char in special_chars:
                escaped_text = escaped_text.replace(char, f'\\{char}')
            
            return escaped_text
        except Exception as e:
            logger.error(f"Error escaping markdown: {e}")
            # Return plain text if escaping fails
            return text
    
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
            new_due_date = datetime.now() + timedelta(days=new_interval)
            
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
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for the bot."""
        try:
            # Get basic dashboard stats
            dashboard_stats = self.db.get_dashboard_stats()
            
            # Get recent activity
            recent_activity = self.db.get_recent_activity_stats(days=7)
            
            # Combine data
            dashboard_data = {
                **dashboard_stats,
                **recent_activity
            }
            
            # Calculate additional metrics
            total = dashboard_data.get("total", 0)
            due_today = dashboard_data.get("due_today", 0)
            new_cards = dashboard_data.get("new", 0)
            
            # Progress percentage
            if total > 0:
                progress_percentage = ((total - new_cards) / total) * 100
                dashboard_data["progress_percentage"] = round(progress_percentage, 1)
            else:
                dashboard_data["progress_percentage"] = 0
            
            # Today's workload as percentage of total
            if total > 0:
                workload_percentage = (due_today / total) * 100
                dashboard_data["workload_percentage"] = round(workload_percentage, 1)
            else:
                dashboard_data["workload_percentage"] = 0
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}

# Global service instance
flashcard_service = FlashcardService()
"""Refactored flashcard service with modular components."""

import logging
import random
from typing import List, Optional, Tuple, Dict, Any

from app.flashcards.models import FlashcardUnion, FlashcardType
from app.flashcards.database import flashcard_db_v2
from app.flashcards.validators import AnswerValidator
from app.flashcards.formatters import QuestionFormatter
from app.flashcards.spaced_repetition import SpacedRepetitionAlgorithm, ReviewScheduler

logger = logging.getLogger(__name__)


class FlashcardService:
    """Service layer for handling flashcard operations in the bot."""
    
    def __init__(self):
        self.db = flashcard_db_v2
        self.answer_validator = AnswerValidator()
        self.question_formatter = QuestionFormatter()
        self.spaced_repetition = SpacedRepetitionAlgorithm()
        self.scheduler = ReviewScheduler()
    
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
            
            # Use scheduler to prioritize cards
            prioritized_cards = self.scheduler.prioritize_flashcards_for_session(due_cards, limit)
            
            logger.info(f"Retrieved {len(prioritized_cards)} flashcards for learning session")
            return prioritized_cards
            
        except Exception as e:
            logger.error(f"Error getting learning session flashcards: {e}")
            return []
    
    def format_question_for_bot(self, flashcard: FlashcardUnion) -> Tuple[str, Optional[Any]]:
        """Format a flashcard question for display in the Telegram bot."""
        return self.question_formatter.format_question_for_bot(flashcard)
    
    def check_answer(self, flashcard: FlashcardUnion, user_input: str) -> Tuple[bool, str]:
        """Check if the user's answer is correct and return feedback."""
        return self.answer_validator.check_answer(flashcard, user_input)
    
    def update_flashcard_after_review(self, flashcard: FlashcardUnion, is_correct: bool) -> bool:
        """Update flashcard statistics and spaced repetition data after review."""
        try:
            if not flashcard.id:
                logger.error("Cannot update flashcard without ID")
                return False
            
            # Calculate new spaced repetition values
            new_due_date, new_interval, new_ease_factor = self.spaced_repetition.calculate_next_review(
                flashcard, is_correct
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
    
    def get_session_statistics(self, flashcards: List[FlashcardUnion]) -> Dict[str, Any]:
        """Get statistics about a flashcard session."""
        return self.scheduler.get_session_statistics(flashcards)


# Global service instance
flashcard_service = FlashcardService()
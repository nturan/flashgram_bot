"""Spaced repetition algorithm implementation."""

import logging
from datetime import datetime, timedelta
from typing import Tuple
from app.flashcards.models import FlashcardUnion

logger = logging.getLogger(__name__)


class SpacedRepetitionAlgorithm:
    """Implements a simplified SM-2 spaced repetition algorithm."""
    
    def calculate_next_review(self, flashcard: FlashcardUnion, is_correct: bool) -> Tuple[datetime, int, float]:
        """
        Calculate the next review date, interval, and ease factor for a flashcard.
        
        Args:
            flashcard: The flashcard being reviewed
            is_correct: Whether the user answered correctly
            
        Returns:
            Tuple of (next_due_date, new_interval_days, new_ease_factor)
        """
        try:
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
            
            return new_due_date, new_interval, new_ease_factor
            
        except Exception as e:
            logger.error(f"Error calculating next review: {e}")
            # Fallback to default values
            default_due = datetime.now() + timedelta(days=1)
            return default_due, 1, 2.5
    
    def get_difficulty_adjustment(self, performance_score: float) -> float:
        """
        Get ease factor adjustment based on performance score.
        
        Args:
            performance_score: Score from 0.0 (worst) to 1.0 (perfect)
            
        Returns:
            Ease factor adjustment (-0.8 to +0.3)
        """
        if performance_score >= 0.9:
            return 0.3
        elif performance_score >= 0.8:
            return 0.15
        elif performance_score >= 0.7:
            return 0.0
        elif performance_score >= 0.6:
            return -0.15
        else:
            return -0.3
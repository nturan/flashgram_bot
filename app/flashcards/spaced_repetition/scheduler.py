"""Review scheduling utilities for spaced repetition."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.flashcards.models import FlashcardUnion, DifficultyLevel

logger = logging.getLogger(__name__)


class ReviewScheduler:
    """Manages scheduling and prioritization of flashcard reviews."""
    
    def prioritize_flashcards_for_session(self, flashcards: List[FlashcardUnion], target_count: int) -> List[FlashcardUnion]:
        """
        Prioritize flashcards for a learning session based on various factors.
        
        Args:
            flashcards: List of available flashcards
            target_count: Desired number of flashcards for the session
            
        Returns:
            Prioritized list of flashcards
        """
        try:
            # Sort by priority: overdue first, then by difficulty and repetition count
            sorted_flashcards = sorted(flashcards, key=self._get_priority_score, reverse=True)
            
            return sorted_flashcards[:target_count]
            
        except Exception as e:
            logger.error(f"Error prioritizing flashcards: {e}")
            return flashcards[:target_count]
    
    def _get_priority_score(self, flashcard: FlashcardUnion) -> float:
        """Calculate priority score for a flashcard."""
        try:
            score = 0.0
            now = datetime.now()
            
            # Overdue cards get highest priority
            if flashcard.due_date <= now:
                days_overdue = (now - flashcard.due_date).days
                score += 1000 + days_overdue * 10
            
            # Difficult cards get higher priority
            difficulty_weights = {
                DifficultyLevel.VERY_HARD: 100,
                DifficultyLevel.HARD: 75,
                DifficultyLevel.MEDIUM: 50,
                DifficultyLevel.EASY: 25,
                DifficultyLevel.VERY_EASY: 10
            }
            score += difficulty_weights.get(flashcard.difficulty, 50)
            
            # Cards with low ease factor need more practice
            if flashcard.ease_factor < 2.0:
                score += 50
            
            # New cards (never reviewed) get moderate priority
            if flashcard.repetition_count == 0:
                score += 30
            
            # Cards with poor performance history
            if flashcard.times_incorrect > flashcard.times_correct:
                score += 25
            
            return score
            
        except Exception as e:
            logger.error(f"Error calculating priority score: {e}")
            return 0.0
    
    def get_session_statistics(self, flashcards: List[FlashcardUnion]) -> Dict[str, Any]:
        """Get statistics about a set of flashcards for session planning."""
        try:
            now = datetime.now()
            
            stats = {
                "total": len(flashcards),
                "due_now": 0,
                "overdue": 0,
                "new": 0,
                "difficult": 0,
                "average_ease": 0.0,
                "difficulty_distribution": {}
            }
            
            if not flashcards:
                return stats
            
            ease_sum = 0.0
            difficulty_counts = {}
            
            for card in flashcards:
                # Count due and overdue cards
                if card.due_date <= now:
                    stats["due_now"] += 1
                    if (now - card.due_date).days > 0:
                        stats["overdue"] += 1
                
                # Count new cards
                if card.repetition_count == 0:
                    stats["new"] += 1
                
                # Count difficult cards
                if card.ease_factor < 2.0 or card.times_incorrect > card.times_correct:
                    stats["difficult"] += 1
                
                # Accumulate ease factor
                ease_sum += card.ease_factor
                
                # Count difficulty distribution
                difficulty = card.difficulty.value
                difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            
            stats["average_ease"] = ease_sum / len(flashcards)
            stats["difficulty_distribution"] = difficulty_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating session statistics: {e}")
            return {"total": len(flashcards), "error": str(e)}
"""Flashcard service using Beanie ODM."""

import logging
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime, timedelta
from beanie import PydanticObjectId

from app.models.flashcards import Flashcard, FlashcardType
from app.flashcards.validators import AnswerValidator
from app.flashcards.formatters import QuestionFormatter
from app.flashcards.spaced_repetition import SpacedRepetitionAlgorithm, ReviewScheduler

logger = logging.getLogger(__name__)


class FlashcardService:
    """Service for flashcard operations using Beanie ODM."""
    
    def __init__(self):
        self.answer_validator = AnswerValidator()
        self.question_formatter = QuestionFormatter()
        self.spaced_repetition = SpacedRepetitionAlgorithm()
        self.scheduler = ReviewScheduler()

    async def create_flashcard(self, flashcard: Flashcard) -> Optional[PydanticObjectId]:
        """Create a new flashcard."""
        try:
            await flashcard.insert()
            logger.info(f"Created flashcard with ID: {flashcard.id}")
            return flashcard.id
        except Exception as e:
            logger.error(f"Error creating flashcard: {e}")
            return None

    async def get_flashcard_by_id(self, flashcard_id: Union[str, PydanticObjectId], user_id: int) -> Optional[Flashcard]:
        """Get a flashcard by ID for a specific user."""
        try:
            # Convert string ID to PydanticObjectId if needed
            if isinstance(flashcard_id, str):
                flashcard_id = PydanticObjectId(flashcard_id)
            
            flashcard = await Flashcard.find_one(
                Flashcard.id == flashcard_id,
                Flashcard.user_id == user_id
            )
            return flashcard
        except Exception as e:
            logger.error(f"Error getting flashcard by ID: {e}")
            return None

    async def get_flashcards(
        self,
        user_id: int,
        flashcard_type: Optional[FlashcardType] = None,
        tags: Optional[List[str]] = None,
        due_before: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[Flashcard]:
        """Get flashcards for a user with optional filtering."""
        try:
            # Build query filters
            filters = [Flashcard.user_id == user_id]
            
            if flashcard_type:
                filters.append(Flashcard.type == flashcard_type)
            
            if tags:
                filters.append(Flashcard.tags.in_(tags))
            
            if due_before:
                filters.append(Flashcard.due_date <= due_before)
            
            # Execute query
            if len(filters) == 1:
                query = Flashcard.find(filters[0])
            else:
                query = Flashcard.find(*filters)
            
            # Sort by due date
            query = query.sort(Flashcard.due_date)
            
            if limit:
                query = query.limit(limit)
            
            flashcards = await query.to_list()
            
            logger.info(f"Retrieved {len(flashcards)} flashcards for user {user_id}")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error getting flashcards: {e}")
            return []

    async def update_flashcard(
        self, 
        flashcard_id: Union[str, PydanticObjectId], 
        user_id: int, 
        updates: Dict[str, Any]
    ) -> bool:
        """Update a flashcard."""
        try:
            flashcard = await self.get_flashcard_by_id(flashcard_id, user_id)
            if not flashcard:
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(flashcard, field):
                    setattr(flashcard, field, value)
            
            flashcard.updated_at = datetime.now()
            await flashcard.save()
            
            logger.info(f"Updated flashcard {flashcard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating flashcard: {e}")
            return False

    async def delete_flashcard(self, flashcard_id: Union[str, PydanticObjectId], user_id: int) -> bool:
        """Delete a flashcard."""
        try:
            flashcard = await self.get_flashcard_by_id(flashcard_id, user_id)
            if not flashcard:
                return False
            
            await flashcard.delete()
            logger.info(f"Deleted flashcard {flashcard_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting flashcard: {e}")
            return False

    async def get_flashcard_count(self, user_id: int, flashcard_type: Optional[FlashcardType] = None) -> int:
        """Get the total number of flashcards for a user."""
        try:
            filters = [Flashcard.user_id == user_id]
            
            if flashcard_type:
                filters.append(Flashcard.type == flashcard_type)
            
            if len(filters) == 1:
                total_count = await Flashcard.find(filters[0]).count()
            else:
                total_count = await Flashcard.find(*filters).count()
            
            logger.info(f"User {user_id} has {total_count} flashcards")
            return total_count
            
        except Exception as e:
            logger.error(f"Error counting flashcards: {e}")
            return 0

    async def get_due_flashcards(self, user_id: int, limit: int = 20) -> List[Flashcard]:
        """Get flashcards that are due for review."""
        now = datetime.now()
        return await self.get_flashcards(user_id=user_id, due_before=now, limit=limit)

    async def get_tags(self, user_id: int) -> List[str]:
        """Get all unique tags used by a user."""
        try:
            all_tags = set()
            
            # Get all flashcards for user
            flashcards = await Flashcard.find(Flashcard.user_id == user_id).to_list()
            for flashcard in flashcards:
                all_tags.update(flashcard.tags)
            
            tags = sorted(list(all_tags))
            logger.info(f"Found {len(tags)} unique tags for user {user_id}")
            return tags
            
        except Exception as e:
            logger.error(f"Error getting tags: {e}")
            return []

    async def update_flashcard_stats(
        self,
        flashcard_id: PydanticObjectId,
        user_id: int,
        is_correct: bool,
        new_due_date: datetime,
        new_interval: int,
        new_ease_factor: float,
    ) -> bool:
        """Update flashcard statistics after a review."""
        try:
            flashcard = await self.get_flashcard_by_id(flashcard_id, user_id)
            if not flashcard:
                return False
            
            # Update stats
            flashcard.due_date = new_due_date
            flashcard.interval_days = new_interval
            flashcard.ease_factor = new_ease_factor
            flashcard.repetition_count += 1
            flashcard.updated_at = datetime.now()
            
            if is_correct:
                flashcard.times_correct += 1
            else:
                flashcard.times_incorrect += 1
            
            await flashcard.save()
            return True
            
        except Exception as e:
            logger.error(f"Error updating flashcard stats: {e}")
            return False

    async def get_dashboard_stats(self, user_id: int) -> Dict[str, int]:
        """Get dashboard statistics for a user."""
        try:
            now = datetime.now()
            today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            week_end = now + timedelta(days=7)

            # Get total count
            total_count = await self.get_flashcard_count(user_id)

            # Due today
            due_today = await Flashcard.find(
                Flashcard.user_id == user_id,
                Flashcard.due_date <= today_end
            ).count()

            # Due this week
            due_this_week = await Flashcard.find(
                Flashcard.user_id == user_id,
                Flashcard.due_date <= week_end
            ).count()

            # New cards (never reviewed)
            new_cards = await Flashcard.find(
                Flashcard.user_id == user_id,
                Flashcard.repetition_count == 0
            ).count()

            # Mastered cards
            mastered_cards = await Flashcard.find(
                Flashcard.user_id == user_id,
                Flashcard.ease_factor >= 2.5,
                Flashcard.interval_days >= 30
            ).count()

            return {
                "total": total_count,
                "due_today": due_today,
                "due_this_week": due_this_week,
                "new": new_cards,
                "mastered": mastered_cards,
            }

        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {
                "total": 0,
                "due_today": 0,
                "due_this_week": 0,
                "new": 0,
                "mastered": 0,
            }

    async def get_learning_session_flashcards(self, user_id: int, limit: int = 20) -> List[Flashcard]:
        """Get flashcards for a learning session."""
        try:
            # Get due flashcards first
            due_cards = await self.get_due_flashcards(user_id=user_id, limit=limit)

            # If we don't have enough due cards, get some random ones
            if len(due_cards) < limit:
                remaining = limit - len(due_cards)
                all_cards = await self.get_flashcards(
                    user_id=user_id, limit=remaining * 2
                )  # Get more to filter out due ones

                # Filter out cards that are already in due_cards
                due_ids = {card.id for card in due_cards if card.id}
                additional_cards = [
                    card for card in all_cards if card.id not in due_ids
                ]

                # Take only what we need
                additional_cards = additional_cards[:remaining]
                due_cards.extend(additional_cards)

            # Use scheduler to prioritize cards
            prioritized_cards = self.scheduler.prioritize_flashcards_for_session(
                due_cards, limit
            )

            logger.info(
                f"Retrieved {len(prioritized_cards)} flashcards for learning session"
            )
            return prioritized_cards

        except Exception as e:
            logger.error(f"Error getting learning session flashcards: {e}")
            return []

    async def get_flashcard_stats(self, user_id: int) -> Dict[str, Any]:
        """Get statistics about the flashcard collection."""
        try:
            total_count = await self.get_flashcard_count(user_id)
            two_sided_count = await self.get_flashcard_count(user_id, FlashcardType.TWO_SIDED)
            fill_blank_count = await self.get_flashcard_count(user_id, FlashcardType.FILL_IN_BLANK)
            multiple_choice_count = await self.get_flashcard_count(
                user_id, FlashcardType.MULTIPLE_CHOICE
            )

            due_cards = await self.get_due_flashcards(user_id=user_id, limit=1000)
            due_count = len(due_cards)  # Get a large number to count
            tags = await self.get_tags(user_id)

            return {
                "total": total_count,
                "two_sided": two_sided_count,
                "fill_in_blank": fill_blank_count,
                "multiple_choice": multiple_choice_count,
                "due_for_review": due_count,
                "unique_tags": len(tags),
                "tags": tags[:10],  # Show first 10 tags
            }

        except Exception as e:
            logger.error(f"Error getting flashcard stats: {e}")
            return {}

    async def get_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for the bot."""
        try:
            # Get basic dashboard stats
            dashboard_stats = await self.get_dashboard_stats(user_id)

            # Get recent activity (using simplified version for now)
            recent_activity = {"completed_sessions": 0, "streak": 0}

            # Combine data
            dashboard_data = {**dashboard_stats, **recent_activity}

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

    def format_question_for_bot(
        self, flashcard: Flashcard
    ) -> Tuple[str, Optional[Any]]:
        """Format a flashcard question for display in the Telegram bot."""
        return self.question_formatter.format_question_for_bot(flashcard)

    def check_answer(
        self, flashcard: Flashcard, user_input: str
    ) -> Tuple[bool, str]:
        """Check if the user's answer is correct and return feedback."""
        return self.answer_validator.check_answer(flashcard, user_input)

    async def update_flashcard_after_review(
        self, user_id: int, flashcard: Flashcard, is_correct: bool
    ) -> bool:
        """Update flashcard statistics and spaced repetition data after review."""
        try:
            if not flashcard.id:
                logger.error("Cannot update flashcard without ID")
                return False

            # Calculate new spaced repetition values
            new_due_date, new_interval, new_ease_factor = (
                self.spaced_repetition.calculate_next_review(flashcard, is_correct)
            )

            # Update in database using Beanie
            updates = {
                "due_date": new_due_date,
                "interval": new_interval,
                "ease_factor": new_ease_factor,
                "updated_at": datetime.now()
            }
            
            # Add review statistics
            if is_correct:
                updates["correct_count"] = flashcard.correct_count + 1 if flashcard.correct_count else 1
            else:
                updates["incorrect_count"] = flashcard.incorrect_count + 1 if flashcard.incorrect_count else 1
            
            updates["total_reviews"] = flashcard.total_reviews + 1 if flashcard.total_reviews else 1

            return await self.update_flashcard(flashcard.id, user_id, updates)

        except Exception as e:
            logger.error(f"Error updating flashcard after review: {e}")
            return False


# Global service instance
flashcard_service = FlashcardService()
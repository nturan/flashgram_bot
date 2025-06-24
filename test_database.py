#!/usr/bin/env python3
"""Test script to initialize database and create sample data."""

import asyncio
import logging
from datetime import datetime

from app.database import init_database
from app.services.user_service import user_service
from app.services.flashcard_service import flashcard_service
from app.services.word_service import word_service
from app.models.flashcards import (
    create_two_sided_card,
    create_fill_in_blank_card,
    create_multiple_choice_card,
    FlashcardType,
    DifficultyLevel
)
from app.models.words import WordType

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database():
    """Test database initialization and operations."""
    try:
        # Initialize database
        logger.info("Initializing database...")
        client, database = await init_database()
        logger.info("Database initialized successfully!")
        
        # Test user creation
        logger.info("Creating test user...")
        user = await user_service.get_or_create_user(
            telegram_user_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        logger.info(f"Created user: {user.get_display_name()}")
        
        # Test word creation
        logger.info("Creating test words...")
        word1 = await word_service.get_or_create_word(
            dictionary_form="дом",
            word_type=WordType.NOUN,
            grammar_data={"gender": "masculine", "animacy": False},
            english_translation="house"
        )
        logger.info(f"Created word: {word1.dictionary_form}")
        
        word2 = await word_service.get_or_create_word(
            dictionary_form="читать",
            word_type=WordType.VERB,
            grammar_data={"aspect": "imperfective"},
            english_translation="to read"
        )
        logger.info(f"Created word: {word2.dictionary_form}")
        
        # Test flashcard creation
        logger.info("Creating test flashcards...")
        
        # Two-sided card
        two_sided = create_two_sided_card(
            user_id=user.telegram_user_id,
            front="What is the Russian word for 'house'?",
            back="дом",
            title="Russian Vocabulary - House",
            tags=["russian", "vocabulary", "nouns"]
        )
        flashcard_id1 = await flashcard_service.create_flashcard(two_sided)
        logger.info(f"Created two-sided card: {flashcard_id1}")
        
        # Fill in the blank
        fill_blank = create_fill_in_blank_card(
            user_id=user.telegram_user_id,
            text_with_blanks="В дом___ живет семья.",
            answers=["е"],
            case_sensitive=False,
            title="Russian Grammar - Prepositional Case",
            tags=["russian", "grammar", "cases", "prepositional"]
        )
        flashcard_id2 = await flashcard_service.create_flashcard(fill_blank)
        logger.info(f"Created fill-in-blank card: {flashcard_id2}")
        
        # Multiple choice
        multiple_choice = create_multiple_choice_card(
            user_id=user.telegram_user_id,
            question="What is the gender of the word 'дом'?",
            options=["Masculine", "Feminine", "Neuter"],
            correct_indices=[0],
            allow_multiple=False,
            title="Russian Grammar - Gender",
            tags=["russian", "grammar", "gender"]
        )
        flashcard_id3 = await flashcard_service.create_flashcard(multiple_choice)
        logger.info(f"Created multiple choice card: {flashcard_id3}")
        
        # Test retrieval
        logger.info("Testing data retrieval...")
        
        # Get user flashcards
        user_flashcards = await flashcard_service.get_flashcards(user.telegram_user_id)
        logger.info(f"User has {len(user_flashcards)} flashcards")
        
        # Get dashboard stats
        stats = await flashcard_service.get_dashboard_stats(user.telegram_user_id)
        logger.info(f"Dashboard stats: {stats}")
        
        # Get word stats
        word_stats = await word_service.get_word_count_by_type()
        logger.info(f"Word stats: {word_stats}")
        
        logger.info("✅ Database test completed successfully!")
        logger.info("📊 You should now see collections in MongoDB Compass:")
        logger.info("   - users (1 document)")
        logger.info("   - flashcards (3 documents)")
        logger.info("   - words (2 documents)")
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(test_database())
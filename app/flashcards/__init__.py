# Flashcard models and utilities

from app.models.flashcards import (
    Flashcard,
    FlashcardType,
    DifficultyLevel,
    create_two_sided_card,
    create_fill_in_blank_card,
    create_multiple_choice_card,
)
from .database import FlashcardDatabaseV2, flashcard_db_v2
from .service import FlashcardService as LegacyFlashcardService, flashcard_service as legacy_flashcard_service
from app.services.flashcard_service import FlashcardService, flashcard_service

__all__ = [
    # Models
    "Flashcard",
    "FlashcardType",
    "DifficultyLevel",
    "create_two_sided_card",
    "create_fill_in_blank_card",
    "create_multiple_choice_card",
    # Database (legacy - for migration)
    "FlashcardDatabaseV2",
    "flashcard_db_v2",
    # Services
    "FlashcardService",  # Modern Beanie service
    "flashcard_service",  # Modern Beanie service instance (from app.services)
    "LegacyFlashcardService",  # Legacy service
    "legacy_flashcard_service",  # Legacy service instance
]

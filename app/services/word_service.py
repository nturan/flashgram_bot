"""Word service using Beanie ODM."""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app.models.words import Word, WordType

logger = logging.getLogger(__name__)


class WordService:
    """Service for word operations using Beanie ODM."""

    async def get_word_by_dictionary_form(self, dictionary_form: str) -> Optional[Word]:
        """Get word by dictionary form."""
        try:
            word = await Word.find_one(Word.dictionary_form == dictionary_form.lower())
            return word
        except Exception as e:
            logger.error(f"Error getting word by dictionary form: {e}")
            return None

    async def create_word(
        self, 
        dictionary_form: str, 
        word_type: WordType,
        grammar_data: Dict[str, Any],
        english_translation: str = ""
    ) -> Optional[Word]:
        """Create a new word."""
        try:
            word = Word(
                dictionary_form=dictionary_form.lower(),
                word_type=word_type,
                grammar_data=grammar_data,
                english_translation=english_translation
            )
            await word.insert()
            logger.info(f"Created word: {dictionary_form} ({word_type})")
            return word
        except Exception as e:
            logger.error(f"Error creating word: {e}")
            return None

    async def get_or_create_word(
        self, 
        dictionary_form: str, 
        word_type: WordType,
        grammar_data: Dict[str, Any],
        english_translation: str = ""
    ) -> Optional[Word]:
        """Get existing word or create new one."""
        try:
            # Try to find existing word
            word = await self.get_word_by_dictionary_form(dictionary_form)
            
            if word:
                return word
            
            # Create new word
            return await self.create_word(dictionary_form, word_type, grammar_data, english_translation)
            
        except Exception as e:
            logger.error(f"Error in get_or_create_word: {e}")
            return None

    async def update_word_translation(self, dictionary_form: str, english_translation: str) -> bool:
        """Update word's English translation."""
        try:
            word = await self.get_word_by_dictionary_form(dictionary_form)
            if not word:
                return False
            
            word.english_translation = english_translation
            await word.save()
            
            logger.info(f"Updated translation for word {dictionary_form}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating word translation: {e}")
            return False

    async def get_words_by_type(self, word_type: WordType, limit: Optional[int] = None) -> List[Word]:
        """Get words by type."""
        try:
            query = Word.find(Word.word_type == word_type)
            
            if limit:
                words = await query.limit(limit).to_list()
            else:
                words = await query.to_list()
            
            logger.info(f"Retrieved {len(words)} words of type {word_type}")
            return words
            
        except Exception as e:
            logger.error(f"Error getting words by type: {e}")
            return []

    async def get_recent_words(self, days: int = 7, limit: int = 50) -> List[Word]:
        """Get recently analyzed words."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            words = await Word.find(
                Word.analyzed_at >= cutoff_date
            ).sort(-Word.analyzed_at).limit(limit).to_list()
            
            logger.info(f"Retrieved {len(words)} recent words")
            return words
            
        except Exception as e:
            logger.error(f"Error getting recent words: {e}")
            return []

    async def get_word_count_by_type(self) -> Dict[str, int]:
        """Get word count by type."""
        try:
            stats = {}
            for word_type in WordType:
                count = await Word.find(Word.word_type == word_type).count()
                stats[word_type.value] = count
            
            logger.info(f"Word count by type: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting word count by type: {e}")
            return {}

    async def search_words(self, query: str, limit: int = 20) -> List[Word]:
        """Search words by dictionary form."""
        try:
            # Use regex search for partial matches
            words = await Word.find(
                {"dictionary_form": {"$regex": query.lower(), "$options": "i"}}
            ).limit(limit).to_list()
            
            logger.info(f"Found {len(words)} words matching '{query}'")
            return words
            
        except Exception as e:
            logger.error(f"Error searching words: {e}")
            return []


# Global service instance
word_service = WordService()
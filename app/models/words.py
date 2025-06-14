"""Word models using Beanie documents for MongoDB integration."""

from beanie import Document, Indexed
from pydantic import Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class WordType(str, Enum):
    """Types of words that can be analyzed."""
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    PRONOUN = "pronoun"
    NUMBER = "number"
    ADVERB = "adverb"
    PREPOSITION = "preposition"


class Word(Document):
    """Document representing an analyzed Russian word."""
    
    # Identification - indexed for fast lookups
    dictionary_form: Indexed(str, unique=True) = Field(..., description="Dictionary/canonical form of the word")
    
    # Word properties
    word_type: WordType = Field(..., description="Type of word (noun, verb, etc.)")
    language: str = Field(default="russian", description="Language of the word")
    
    # Grammatical information (stored as JSON)
    grammar_data: Dict[str, Any] = Field(..., description="Grammatical analysis data")
    
    # Translations and definitions
    english_translation: str = Field(default="", description="Primary English translation")
    
    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="When the word was analyzed")

    class Settings:
        name = "words"

    @classmethod
    async def find_by_dictionary_form(cls, dictionary_form: str) -> Optional["Word"]:
        """Find word by dictionary form."""
        return await cls.find_one(cls.dictionary_form == dictionary_form)

    @classmethod
    async def get_or_create_word(cls, dictionary_form: str, word_type: WordType, 
                               grammar_data: Dict[str, Any]) -> "Word":
        """Get existing word or create new one."""
        word = await cls.find_by_dictionary_form(dictionary_form)
        if word:
            return word
        
        # Create new word
        word = cls(
            dictionary_form=dictionary_form,
            word_type=word_type,
            grammar_data=grammar_data
        )
        await word.insert()
        return word
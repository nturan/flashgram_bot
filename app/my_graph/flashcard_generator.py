"""Refactored flashcard generator with modular components."""

import logging
from typing import List, Any, Dict
from app.flashcards import flashcard_service
from app.grammar.russian import Noun, Adjective, Verb, Pronoun, Number
from app.my_graph.generators import (
    NounGenerator,
    AdjectiveGenerator,
    VerbGenerator,
    PronounGenerator,
    NumberGenerator,
)

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """Tool for generating flashcards from grammatical analysis results."""

    def __init__(self):
        self.service = flashcard_service
        self.noun_generator = NounGenerator()
        self.adjective_generator = AdjectiveGenerator()
        self.verb_generator = VerbGenerator()
        self.pronoun_generator = PronounGenerator()
        self.number_generator = NumberGenerator()

    def generate_flashcards_from_grammar(
        self,
        grammar_obj: Any,
        word_type: str,
        generated_sentences: Dict[str, str] = None,
        user_id: int = 1,
    ) -> List[Any]:
        """
        Generate flashcards from a grammar object (Noun, Adjective, Verb, Pronoun, or Number).

        Args:
            grammar_obj: The parsed grammar object (Noun, Adjective, Verb, Pronoun, or Number)
            word_type: Type of word ("noun", "adjective", "verb", "pronoun", "number")
            generated_sentences: Pre-generated sentences from the agent (optional)

        Returns:
            List of flashcards
        """
        flashcards = []

        try:
            if isinstance(grammar_obj, Noun):
                flashcards = self.noun_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type, generated_sentences, user_id
                )
            elif isinstance(grammar_obj, Adjective):
                flashcards = self.adjective_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type, generated_sentences, user_id
                )
            elif isinstance(grammar_obj, Verb):
                flashcards = self.verb_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type, generated_sentences, user_id
                )
            elif isinstance(grammar_obj, Pronoun):
                flashcards = self.pronoun_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type, generated_sentences, user_id
                )
            elif isinstance(grammar_obj, Number):
                flashcards = self.number_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type, generated_sentences, user_id
                )
            else:
                logger.warning(f"Unknown grammar object type: {type(grammar_obj)}")

        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")

        return flashcards

    def save_flashcards_to_database(self, user_id: int, flashcards: List[Any]) -> int:
        """
        Save generated flashcards to the database.

        Args:
            flashcards: List of flashcards to save

        Returns:
            Number of flashcards successfully saved
        """
        saved_count = 0

        for flashcard in flashcards:
            try:
                # Set user_id on the flashcard
                flashcard.user_id = user_id
                
                flashcard_id = self.service.db.add_flashcard(flashcard)
                if flashcard_id:
                    saved_count += 1
                    logger.info(f"Saved flashcard: {flashcard.title}")
                else:
                    logger.warning(f"Failed to save flashcard: {flashcard.title}")

            except Exception as e:
                logger.error(f"Error saving flashcard '{flashcard.title}': {e}")

        logger.info(f"Successfully saved {saved_count}/{len(flashcards)} flashcards")
        return saved_count


# Global instance
flashcard_generator = FlashcardGenerator()

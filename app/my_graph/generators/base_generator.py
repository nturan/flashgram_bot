"""Base flashcard generator with common functionality."""

import logging
from typing import List, Any
from beanie import PydanticObjectId
from app.models.flashcards import (
    Flashcard,
    create_fill_in_blank_card,
    create_two_sided_card,
    create_multiple_choice_card
)
from app.my_graph.utils import SuffixExtractor, FormAnalyzer

logger = logging.getLogger(__name__)


class BaseGenerator:
    """Base class for word-type specific flashcard generators."""

    def __init__(self):
        self.suffix_extractor = SuffixExtractor()
        self.form_analyzer = FormAnalyzer()

    def create_fill_in_gap_card(
        self,
        dictionary_form: str,
        target_form: str,
        form_description: str,
        word_type: str,
        tags: List[str],
        user_id: str,
        grammatical_key: str = None,
        pre_generated_sentence: str = None,
    ) -> Flashcard:
        """Create a fill-in-the-gap flashcard for a grammatical form."""
        
        # Only create cards if we have a pre-generated sentence
        # LLM sentence generation has been removed from grammar analysis
        if not pre_generated_sentence:
            logger.warning(f"No pre-generated sentence available for {dictionary_form} - {form_description}")
            # Create a simple template sentence as fallback
            sentence = f"Пример с {target_form}."
        else:
            sentence = pre_generated_sentence

        # Extract stem and suffix
        stem, suffix = self.suffix_extractor.extract_suffix(
            dictionary_form, target_form
        )

        # Create the sentence with masked suffix - simple text replacement
        sentence_with_blank = sentence.replace(target_form, f"{stem}___")

        return create_fill_in_blank_card(
            telegram_user_id=user_id,
            text_with_blanks=sentence_with_blank,
            answers=[suffix],
            case_sensitive=False,
            tags=tags + ["fill_in_gap", "suffix"],
            title=f"{dictionary_form} - {form_description} (gap fill)",
            # Store the grammatical key for the hint
            metadata={
                "form_description": form_description,
                "dictionary_form": dictionary_form,
                "grammatical_key": grammatical_key or form_description,
            },
        )

    def create_two_sided_card(
        self, front: str, back: str, tags: List[str], title: str, user_id: str
    ) -> Flashcard:
        """Create a two-sided flashcard."""
        return create_two_sided_card(telegram_user_id=user_id, front=front, back=back, tags=tags, title=title)

    def create_multiple_choice_card(
        self,
        question: str,
        options: List[str],
        correct_indices: List[int],
        tags: List[str],
        title: str,
        user_id: str,
        allow_multiple: bool = False,
    ) -> Flashcard:
        """Create a multiple choice flashcard."""
        return create_multiple_choice_card(
            telegram_user_id=user_id,
            question=question,
            options=options,
            correct_indices=correct_indices,
            allow_multiple=allow_multiple,
            tags=tags,
            title=title,
        )

    def should_create_flashcard(self, form: str, dictionary_form: str) -> bool:
        """Determine if a flashcard should be created for this form."""
        return form and form.strip() and form.lower() != dictionary_form.lower()

    def generate_flashcards_from_grammar(
        self, grammar_obj: Any, word_type: str
    ) -> List[Any]:
        """Generate flashcards from a grammar object. To be implemented by subclasses."""
        raise NotImplementedError(
            "Subclasses must implement generate_flashcards_from_grammar"
        )

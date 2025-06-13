"""Noun-specific flashcard generator."""

import logging
from typing import List, Any, Dict
from app.grammar.russian import Noun
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class NounGenerator(BaseGenerator):
    """Generates flashcards specifically for Russian nouns."""

    def generate_flashcards_from_grammar(
        self,
        noun: Noun,
        word_type: str = "noun",
        generated_sentences: Dict[str, str] = None,
    ) -> List[Any]:
        """Generate flashcards for a Russian noun."""
        flashcards = []
        dictionary_form = noun.dictionary_form

        # Initialize generated_sentences if None
        if generated_sentences is None:
            generated_sentences = {}

        # Generate fill-in-the-gap flashcards for singular forms
        flashcards.extend(
            self._generate_singular_forms(noun, dictionary_form, generated_sentences)
        )

        # Generate fill-in-the-gap flashcards for plural forms
        flashcards.extend(
            self._generate_plural_forms(noun, dictionary_form, generated_sentences)
        )

        # Generate gender and animacy flashcards
        flashcards.extend(self._generate_property_flashcards(noun, dictionary_form))

        return flashcards

    def _generate_singular_forms(
        self, noun: Noun, dictionary_form: str, generated_sentences: Dict[str, str]
    ) -> List[Any]:
        """Generate flashcards for singular noun forms."""
        flashcards = []

        for case, form in noun.singular.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"{case.upper()} singular"

                # Look for pre-generated sentence for this form
                sentence_key = f"{case}_singular"
                pre_generated_sentence = generated_sentences.get(sentence_key)

                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} singular",
                    word_type="noun",
                    tags=["russian", "noun", "singular", case, "grammar"],
                    grammatical_key=grammatical_key,
                    pre_generated_sentence=pre_generated_sentence,
                )
                flashcards.append(flashcard)

        return flashcards

    def _generate_plural_forms(
        self, noun: Noun, dictionary_form: str, generated_sentences: Dict[str, str]
    ) -> List[Any]:
        """Generate flashcards for plural noun forms."""
        flashcards = []

        for case, form in noun.plural.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"{case.upper()} plural"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} plural",
                    word_type="noun",
                    tags=["russian", "noun", "plural", case, "grammar"],
                    grammatical_key=grammatical_key,
                )
                flashcards.append(flashcard)

        return flashcards

    def _generate_property_flashcards(
        self, noun: Noun, dictionary_form: str
    ) -> List[Any]:
        """Generate flashcards for noun properties (gender, animacy)."""
        flashcards = []

        # Gender flashcard
        gender_flashcard = self.create_two_sided_card(
            front=f"What is the gender of '{dictionary_form}'?",
            back=noun.gender,
            tags=["russian", "noun", "gender", "grammar"],
            title=f"{dictionary_form} - gender",
        )
        flashcards.append(gender_flashcard)

        # Animacy flashcard
        animacy_text = "animate" if noun.animacy else "inanimate"
        animacy_flashcard = self.create_two_sided_card(
            front=f"Is '{dictionary_form}' animate or inanimate?",
            back=animacy_text,
            tags=["russian", "noun", "animacy", "grammar"],
            title=f"{dictionary_form} - animacy",
        )
        flashcards.append(animacy_flashcard)

        return flashcards

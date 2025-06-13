"""Pronoun-specific flashcard generator."""

import logging
from typing import List, Any, Dict
from app.grammar.russian import Pronoun
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class PronounGenerator(BaseGenerator):
    """Generates flashcards specifically for Russian pronouns."""

    def generate_flashcards_from_grammar(
        self,
        pronoun: Pronoun,
        word_type: str = "pronoun",
        generated_sentences: Dict[str, str] = None,
    ) -> List[Any]:
        """Generate flashcards for a Russian pronoun."""
        if generated_sentences is None:
            generated_sentences = {}
        flashcards = []
        dictionary_form = pronoun.dictionary_form

        # Determine declension pattern based on available fields
        if pronoun.singular is not None or pronoun.plural is not None:
            # Has noun-like declension (personal pronouns)
            flashcards.extend(self._generate_noun_like_forms(pronoun, dictionary_form))
        elif (
            pronoun.masculine is not None
            or pronoun.feminine is not None
            or pronoun.neuter is not None
        ):
            # Has adjective-like declension (demonstrative, possessive pronouns)
            flashcards.extend(
                self._generate_adjective_like_forms(pronoun, dictionary_form)
            )
        else:
            # Special/irregular declension
            flashcards.extend(self._generate_special_forms(pronoun, dictionary_form))

        # Generate basic property flashcards
        flashcards.extend(self._generate_property_flashcards(pronoun, dictionary_form))

        return flashcards

    def _generate_noun_like_forms(
        self, pronoun: Pronoun, dictionary_form: str
    ) -> List[Any]:
        """Generate flashcards for noun-like pronouns (personal pronouns)."""
        flashcards = []

        # Generate singular forms if available
        if pronoun.singular:
            for case, form in pronoun.singular.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} singular"
                    grammatical_key = f"{case.upper()} case"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "personal", case, "singular"],
                        grammatical_key=grammatical_key,
                    )
                    flashcards.append(flashcard)

        # Generate plural forms if available
        if pronoun.plural:
            for case, form in pronoun.plural.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} plural"
                    grammatical_key = f"{case.upper()} case"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "personal", case, "plural"],
                        grammatical_key=grammatical_key,
                    )
                    flashcards.append(flashcard)

        return flashcards

    def _generate_adjective_like_forms(
        self, pronoun: Pronoun, dictionary_form: str
    ) -> List[Any]:
        """Generate flashcards for adjective-like pronouns (demonstrative, possessive)."""
        flashcards = []

        # Generate masculine forms
        if pronoun.masculine:
            for case, form in pronoun.masculine.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} masculine"
                    grammatical_key = f"{case.upper()} masculine"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "demonstrative", case, "masculine"],
                        grammatical_key=grammatical_key,
                    )
                    flashcards.append(flashcard)

        # Generate feminine forms
        if pronoun.feminine:
            for case, form in pronoun.feminine.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} feminine"
                    grammatical_key = f"{case.upper()} feminine"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "demonstrative", case, "feminine"],
                        grammatical_key=grammatical_key,
                    )
                    flashcards.append(flashcard)

        # Generate neuter forms
        if pronoun.neuter:
            for case, form in pronoun.neuter.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} neuter"
                    grammatical_key = f"{case.upper()} neuter"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "demonstrative", case, "neuter"],
                        grammatical_key=grammatical_key,
                    )
                    flashcards.append(flashcard)

        # Generate plural forms
        if pronoun.plural_adjective_like:
            for case, form in pronoun.plural_adjective_like.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} plural"
                    grammatical_key = f"{case.upper()} plural"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "demonstrative", case, "plural"],
                        grammatical_key=grammatical_key,
                    )
                    flashcards.append(flashcard)

        return flashcards

    def _generate_special_forms(
        self, pronoun: Pronoun, dictionary_form: str
    ) -> List[Any]:
        """Generate flashcards for pronouns with special declension patterns."""
        flashcards = []

        # For special pronouns, try to handle available forms intelligently
        # Check which form fields are available and process them

        if pronoun.singular:
            # Treat as noun-like if singular is available
            flashcards.extend(self._generate_noun_like_forms(pronoun, dictionary_form))
        elif pronoun.masculine:
            # Treat as adjective-like if gender forms are available
            flashcards.extend(
                self._generate_adjective_like_forms(pronoun, dictionary_form)
            )
        else:
            # Create a basic two-sided card for very irregular pronouns
            flashcard = self.create_two_sided_card(
                front=f"What is the English meaning of '{dictionary_form}'?",
                back=pronoun.english_translation,
                tags=["russian", "pronoun", "special", "translation"],
                title=f"{dictionary_form} - meaning",
            )
            flashcards.append(flashcard)

        return flashcards

    def _generate_property_flashcards(
        self, pronoun: Pronoun, dictionary_form: str
    ) -> List[Any]:
        """Generate flashcards for pronoun properties and characteristics."""
        flashcards = []

        # Translation flashcard
        flashcard = self.create_two_sided_card(
            front=f"What does '{dictionary_form}' mean in English?",
            back=pronoun.english_translation,
            tags=["russian", "pronoun", "translation"],
            title=f"{dictionary_form} - translation",
        )
        flashcards.append(flashcard)

        # Add notes flashcard if available
        if pronoun.notes and pronoun.notes.strip():
            flashcard = self.create_two_sided_card(
                front=f"What are the special notes for '{dictionary_form}'?",
                back=pronoun.notes,
                tags=["russian", "pronoun", "notes", "grammar"],
                title=f"{dictionary_form} - special notes",
            )
            flashcards.append(flashcard)

        return flashcards

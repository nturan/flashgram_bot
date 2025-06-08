"""Pronoun-specific flashcard generator."""

import logging
from typing import List, Any
from app.grammar.russian import Pronoun
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class PronounGenerator(BaseGenerator):
    """Generates flashcards specifically for Russian pronouns."""
    
    def generate_flashcards_from_grammar(self, pronoun: Pronoun, word_type: str = "pronoun") -> List[Any]:
        """Generate flashcards for a Russian pronoun."""
        flashcards = []
        dictionary_form = pronoun.dictionary_form
        
        # Generate flashcards based on declension pattern
        if pronoun.declension_pattern == "noun_like":
            flashcards.extend(self._generate_noun_like_forms(pronoun, dictionary_form))
        elif pronoun.declension_pattern == "adjective_like":
            flashcards.extend(self._generate_adjective_like_forms(pronoun, dictionary_form))
        else:  # special
            flashcards.extend(self._generate_special_forms(pronoun, dictionary_form))
        
        # Generate pronoun type and property flashcards
        flashcards.extend(self._generate_property_flashcards(pronoun, dictionary_form))
        
        return flashcards
    
    def _generate_noun_like_forms(self, pronoun: Pronoun, dictionary_form: str) -> List[Any]:
        """Generate flashcards for noun-like pronouns (personal pronouns)."""
        flashcards = []
        
        # Generate singular forms if available
        if pronoun.singular:
            for case, form in pronoun.singular.items():
                if self.should_create_flashcard(form, dictionary_form):
                    # Create descriptive form name
                    person_desc = f"{pronoun.person} person" if pronoun.person else ""
                    gender_desc = f"{pronoun.gender}" if pronoun.gender else ""
                    
                    if person_desc and gender_desc:
                        form_description = f"{case.upper()} ({person_desc}, {gender_desc})"
                    elif person_desc:
                        form_description = f"{case.upper()} ({person_desc})"
                    else:
                        form_description = f"{case.upper()} singular"
                    
                    grammatical_key = f"{case.upper()} case"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "personal", case, "singular"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        # Generate plural forms if available
        if pronoun.plural:
            for case, form in pronoun.plural.items():
                if self.should_create_flashcard(form, dictionary_form):
                    person_desc = f"{pronoun.person} person" if pronoun.person else ""
                    form_description = f"{case.upper()} ({person_desc})" if person_desc else f"{case.upper()} plural"
                    
                    grammatical_key = f"{case.upper()} case"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="pronoun",
                        tags=["russian", "pronoun", "personal", case, "plural"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_adjective_like_forms(self, pronoun: Pronoun, dictionary_form: str) -> List[Any]:
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
                        tags=["russian", "pronoun", pronoun.pronoun_type, case, "masculine"],
                        grammatical_key=grammatical_key
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
                        tags=["russian", "pronoun", pronoun.pronoun_type, case, "feminine"],
                        grammatical_key=grammatical_key
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
                        tags=["russian", "pronoun", pronoun.pronoun_type, case, "neuter"],
                        grammatical_key=grammatical_key
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
                        tags=["russian", "pronoun", pronoun.pronoun_type, case, "plural"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_special_forms(self, pronoun: Pronoun, dictionary_form: str) -> List[Any]:
        """Generate flashcards for pronouns with special declension patterns."""
        flashcards = []
        
        # For special pronouns, try to handle available forms intelligently
        # Check which form fields are available and process them
        
        if pronoun.singular:
            # Treat as noun-like if singular is available
            flashcards.extend(self._generate_noun_like_forms(pronoun, dictionary_form))
        elif pronoun.masculine:
            # Treat as adjective-like if gender forms are available
            flashcards.extend(self._generate_adjective_like_forms(pronoun, dictionary_form))
        else:
            # Create a basic two-sided card for very irregular pronouns
            flashcard = self.create_two_sided_card(
                front=f"What is the English meaning of '{dictionary_form}'?",
                back=pronoun.english_translation,
                tags=["russian", "pronoun", pronoun.pronoun_type, "translation"],
                title=f"{dictionary_form} - meaning"
            )
            flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_property_flashcards(self, pronoun: Pronoun, dictionary_form: str) -> List[Any]:
        """Generate flashcards for pronoun properties and characteristics."""
        flashcards = []
        
        # Pronoun type flashcard
        flashcard = self.create_two_sided_card(
            front=f"What type of pronoun is '{dictionary_form}'?",
            back=pronoun.pronoun_type.title(),
            tags=["russian", "pronoun", "type", "grammar"],
            title=f"{dictionary_form} - pronoun type"
        )
        flashcards.append(flashcard)
        
        # Translation flashcard
        flashcard = self.create_two_sided_card(
            front=f"What does '{dictionary_form}' mean in English?",
            back=pronoun.english_translation,
            tags=["russian", "pronoun", "translation"],
            title=f"{dictionary_form} - translation"
        )
        flashcards.append(flashcard)
        
        # Declension pattern flashcard
        pattern_descriptions = {
            "noun_like": "Declines like a noun (personal pronouns)",
            "adjective_like": "Declines like an adjective (demonstrative, possessive pronouns)",
            "special": "Has a special/irregular declension pattern"
        }
        
        flashcard = self.create_two_sided_card(
            front=f"How does '{dictionary_form}' decline?",
            back=pattern_descriptions.get(pronoun.declension_pattern, pronoun.declension_pattern),
            tags=["russian", "pronoun", "declension", "grammar"],
            title=f"{dictionary_form} - declension pattern"
        )
        flashcards.append(flashcard)
        
        # Person and number for personal pronouns
        if pronoun.person and pronoun.number:
            flashcard = self.create_two_sided_card(
                front=f"What person and number is '{dictionary_form}'?",
                back=f"{pronoun.person.title()} person, {pronoun.number}",
                tags=["russian", "pronoun", "personal", "grammar"],
                title=f"{dictionary_form} - person and number"
            )
            flashcards.append(flashcard)
        
        # Gender for pronouns that have it
        if pronoun.gender:
            flashcard = self.create_two_sided_card(
                front=f"What gender is '{dictionary_form}'?",
                back=pronoun.gender.title(),
                tags=["russian", "pronoun", "gender", "grammar"],
                title=f"{dictionary_form} - gender"
            )
            flashcards.append(flashcard)
        
        return flashcards
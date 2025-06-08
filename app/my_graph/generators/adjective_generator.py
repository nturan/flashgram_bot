"""Adjective-specific flashcard generator."""

import logging
from typing import List, Any
from app.grammar.russian import Adjective
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class AdjectiveGenerator(BaseGenerator):
    """Generates flashcards specifically for Russian adjectives."""
    
    def generate_flashcards_from_grammar(self, adjective: Adjective, word_type: str = "adjective") -> List[Any]:
        """Generate flashcards for a Russian adjective."""
        flashcards = []
        dictionary_form = adjective.dictionary_form
        
        # Generate fill-in-the-gap flashcards for different forms
        flashcards.extend(self._generate_masculine_forms(adjective, dictionary_form))
        flashcards.extend(self._generate_feminine_forms(adjective, dictionary_form))
        flashcards.extend(self._generate_neuter_forms(adjective, dictionary_form))
        flashcards.extend(self._generate_plural_forms(adjective, dictionary_form))
        flashcards.extend(self._generate_short_forms(adjective, dictionary_form))
        
        # Generate comparative and superlative flashcards
        flashcards.extend(self._generate_comparison_flashcards(adjective, dictionary_form))
        
        return flashcards
    
    def _generate_masculine_forms(self, adjective: Adjective, dictionary_form: str) -> List[Any]:
        """Generate flashcards for masculine adjective forms."""
        flashcards = []
        
        for case, form in adjective.masculine.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"{case.upper()} masculine"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} masculine",
                    word_type="adjective",
                    tags=["russian", "adjective", "masculine", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_feminine_forms(self, adjective: Adjective, dictionary_form: str) -> List[Any]:
        """Generate flashcards for feminine adjective forms."""
        flashcards = []
        
        for case, form in adjective.feminine.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"{case.upper()} feminine"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} feminine",
                    word_type="adjective",
                    tags=["russian", "adjective", "feminine", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_neuter_forms(self, adjective: Adjective, dictionary_form: str) -> List[Any]:
        """Generate flashcards for neuter adjective forms."""
        flashcards = []
        
        for case, form in adjective.neuter.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"{case.upper()} neuter"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} neuter",
                    word_type="adjective",
                    tags=["russian", "adjective", "neuter", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_plural_forms(self, adjective: Adjective, dictionary_form: str) -> List[Any]:
        """Generate flashcards for plural adjective forms."""
        flashcards = []
        
        for case, form in adjective.plural.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"{case.upper()} plural"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} plural",
                    word_type="adjective",
                    tags=["russian", "adjective", "plural", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_short_forms(self, adjective: Adjective, dictionary_form: str) -> List[Any]:
        """Generate flashcards for short adjective forms."""
        flashcards = []
        
        short_forms = {
            "masculine": adjective.short_form_masculine,
            "feminine": adjective.short_form_feminine,
            "neuter": adjective.short_form_neuter,
            "plural": adjective.short_form_plural
        }
        
        for gender, form in short_forms.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"short {gender}"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"short {gender}",
                    word_type="adjective",
                    tags=["russian", "adjective", "short_form", gender, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_comparison_flashcards(self, adjective: Adjective, dictionary_form: str) -> List[Any]:
        """Generate flashcards for comparative and superlative forms."""
        flashcards = []
        
        # Comparative flashcard
        if adjective.comparative and adjective.comparative.strip():
            comparative_flashcard = self.create_two_sided_card(
                front=f"What is the comparative form of '{dictionary_form}'?",
                back=adjective.comparative,
                tags=["russian", "adjective", "comparative", "grammar"],
                title=f"{dictionary_form} - comparative"
            )
            flashcards.append(comparative_flashcard)
        
        # Superlative flashcard
        if adjective.superlative and adjective.superlative.strip():
            superlative_flashcard = self.create_two_sided_card(
                front=f"What is the superlative form of '{dictionary_form}'?",
                back=adjective.superlative,
                tags=["russian", "adjective", "superlative", "grammar"],
                title=f"{dictionary_form} - superlative"
            )
            flashcards.append(superlative_flashcard)
        
        return flashcards
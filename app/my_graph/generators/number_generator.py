"""Number-specific flashcard generator."""

import logging
from typing import List, Any, Dict
from app.grammar.russian import Number
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class NumberGenerator(BaseGenerator):
    """Generates flashcards specifically for Russian numbers."""
    
    def generate_flashcards_from_grammar(self, number: Number, word_type: str = "number", generated_sentences: Dict[str, str] = None) -> List[Any]:
        """Generate flashcards for a Russian number."""
        if generated_sentences is None:
            generated_sentences = {}
        flashcards = []
        dictionary_form = number.dictionary_form
        
        # Generate flashcards based on number category
        if number.number_category == "one":
            flashcards.extend(self._generate_one_type_forms(number, dictionary_form))
        elif number.number_category in ["two_three_four", "five_twenty", "tens", "hundreds"]:
            flashcards.extend(self._generate_simple_case_forms(number, dictionary_form))
        elif number.number_category == "thousands":
            flashcards.extend(self._generate_thousands_forms(number, dictionary_form))
        elif number.number_category == "compound":
            flashcards.extend(self._generate_compound_forms(number, dictionary_form))
        else:  # special
            flashcards.extend(self._generate_special_forms(number, dictionary_form))
        
        # Generate number property and usage flashcards
        flashcards.extend(self._generate_property_flashcards(number, dictionary_form))
        
        return flashcards
    
    def _generate_one_type_forms(self, number: Number, dictionary_form: str) -> List[Any]:
        """Generate flashcards for 'one' type numbers (один/одна/одно)."""
        flashcards = []
        
        # Generate masculine forms
        if number.masculine:
            for case, form in number.masculine.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} masculine"
                    grammatical_key = f"{case.upper()} masculine"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", "one", case, "masculine"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        # Generate feminine forms
        if number.feminine:
            for case, form in number.feminine.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} feminine"
                    grammatical_key = f"{case.upper()} feminine"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", "one", case, "feminine"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        # Generate neuter forms
        if number.neuter:
            for case, form in number.neuter.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} neuter"
                    grammatical_key = f"{case.upper()} neuter"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", "one", case, "neuter"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_simple_case_forms(self, number: Number, dictionary_form: str) -> List[Any]:
        """Generate flashcards for numbers with simple case declension."""
        flashcards = []
        
        if number.singular:
            for case, form in number.singular.items():
                if self.should_create_flashcard(form, dictionary_form):
                    # Create descriptive form name based on category
                    category_desc = {
                        "two_three_four": "2-4 pattern",
                        "five_twenty": "5-20 pattern", 
                        "tens": "tens",
                        "hundreds": "hundreds"
                    }.get(number.number_category, "")
                    
                    form_description = f"{case.upper()} ({category_desc})"
                    grammatical_key = f"{case.upper()} case"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", number.number_category, case],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_thousands_forms(self, number: Number, dictionary_form: str) -> List[Any]:
        """Generate flashcards for thousands-type numbers (тысяча, миллион)."""
        flashcards = []
        
        # Generate singular forms
        if number.singular:
            for case, form in number.singular.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} singular"
                    grammatical_key = f"{case.upper()} singular"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", "thousands", case, "singular"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        # Generate plural forms
        if number.plural:
            for case, form in number.plural.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case.upper()} plural"
                    grammatical_key = f"{case.upper()} plural"
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", "thousands", case, "plural"],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_compound_forms(self, number: Number, dictionary_form: str) -> List[Any]:
        """Generate flashcards for compound numbers (двадцать один, etc.)."""
        flashcards = []
        
        if number.compound_forms:
            for case_form, form in number.compound_forms.items():
                if self.should_create_flashcard(form, dictionary_form):
                    form_description = f"{case_form} (compound)"
                    grammatical_key = case_form
                    flashcard = self.create_fill_in_gap_card(
                        dictionary_form=dictionary_form,
                        target_form=form,
                        form_description=form_description,
                        word_type="number",
                        tags=["russian", "number", "compound", case_form],
                        grammatical_key=grammatical_key
                    )
                    flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_special_forms(self, number: Number, dictionary_form: str) -> List[Any]:
        """Generate flashcards for special/irregular numbers."""
        flashcards = []
        
        # For special numbers, try to handle available forms intelligently
        if number.singular:
            flashcards.extend(self._generate_simple_case_forms(number, dictionary_form))
        elif number.masculine:
            flashcards.extend(self._generate_one_type_forms(number, dictionary_form))
        else:
            # Create a basic translation card for very irregular numbers
            flashcard = self.create_two_sided_card(
                front=f"What is the English meaning of '{dictionary_form}'?",
                back=number.english_translation,
                tags=["russian", "number", "special", "translation"],
                title=f"{dictionary_form} - meaning"
            )
            flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_property_flashcards(self, number: Number, dictionary_form: str) -> List[Any]:
        """Generate flashcards for number properties and usage patterns."""
        flashcards = []
        
        # Number value flashcard
        flashcard = self.create_two_sided_card(
            front=f"What is the numeric value of '{dictionary_form}'?",
            back=str(number.numeric_value),
            tags=["russian", "number", "value"],
            title=f"{dictionary_form} - numeric value"
        )
        flashcards.append(flashcard)
        
        # Translation flashcard
        flashcard = self.create_two_sided_card(
            front=f"What does '{dictionary_form}' mean in English?",
            back=number.english_translation,
            tags=["russian", "number", "translation"],
            title=f"{dictionary_form} - translation"
        )
        flashcards.append(flashcard)
        
        # Number type flashcard
        type_descriptions = {
            "cardinal": "Cardinal number (один, два, три...)",
            "ordinal": "Ordinal number (первый, второй, третий...)",
            "collective": "Collective number (двое, трое, четверо...)"
        }
        
        flashcard = self.create_two_sided_card(
            front=f"What type of number is '{dictionary_form}'?",
            back=type_descriptions.get(number.number_type, number.number_type),
            tags=["russian", "number", "type", "grammar"],
            title=f"{dictionary_form} - number type"
        )
        flashcards.append(flashcard)
        
        # Number category flashcard
        category_descriptions = {
            "one": "Special pattern like adjectives (один/одна/одно)",
            "two_three_four": "Special pattern for 2-4 (два, три, четыре)",
            "five_twenty": "Pattern like feminine nouns in -ь (пять-двадцать)",
            "tens": "Tens pattern (тридцать, сорок, пятьдесят...)",
            "hundreds": "Hundreds pattern (сто, двести, триста...)",
            "thousands": "Large numbers (тысяча, миллион...)",
            "compound": "Compound numbers (двадцать один...)",
            "special": "Irregular declension pattern"
        }
        
        flashcard = self.create_two_sided_card(
            front=f"What declension category is '{dictionary_form}'?",
            back=category_descriptions.get(number.number_category, number.number_category),
            tags=["russian", "number", "category", "grammar"],
            title=f"{dictionary_form} - declension category"
        )
        flashcards.append(flashcard)
        
        # Noun agreement pattern flashcard
        if number.noun_agreement:
            agreement_text = "; ".join([f"{case}: {pattern}" for case, pattern in number.noun_agreement.items()])
            flashcard = self.create_two_sided_card(
                front=f"How do nouns agree with '{dictionary_form}' in different cases?",
                back=agreement_text,
                tags=["russian", "number", "agreement", "grammar"],
                title=f"{dictionary_form} - noun agreement"
            )
            flashcards.append(flashcard)
        
        # Usage notes flashcard
        if number.usage_notes:
            flashcard = self.create_two_sided_card(
                front=f"What are the special usage notes for '{dictionary_form}'?",
                back=number.usage_notes,
                tags=["russian", "number", "usage", "grammar"],
                title=f"{dictionary_form} - usage notes"
            )
            flashcards.append(flashcard)
        
        return flashcards
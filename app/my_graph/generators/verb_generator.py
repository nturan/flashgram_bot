"""Verb-specific flashcard generator."""

import logging
from typing import List, Any, Dict
from app.grammar.russian import Verb
from app.flashcards.models import MultipleChoice
from .base_generator import BaseGenerator

logger = logging.getLogger(__name__)


class VerbGenerator(BaseGenerator):
    """Generates flashcards specifically for Russian verbs."""
    
    def generate_flashcards_from_grammar(self, verb: Verb, word_type: str = "verb", generated_sentences: Dict[str, str] = None) -> List[Any]:
        """Generate flashcards for a Russian verb."""
        if generated_sentences is None:
            generated_sentences = {}
        flashcards = []
        dictionary_form = verb.dictionary_form
        
        # Generate aspect and conjugation flashcards
        flashcards.extend(self._generate_aspect_flashcards(verb, dictionary_form))
        flashcards.extend(self._generate_conjugation_flashcards(verb, dictionary_form))
        
        # Generate tense-specific flashcards
        flashcards.extend(self._generate_present_tense_flashcards(verb, dictionary_form))
        flashcards.extend(self._generate_past_tense_flashcards(verb, dictionary_form))
        flashcards.extend(self._generate_future_tense_flashcards(verb, dictionary_form))
        flashcards.extend(self._generate_imperative_flashcards(verb, dictionary_form))
        
        return flashcards
    
    def _generate_aspect_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for verb aspect."""
        flashcards = []
        
        # Generate aspect multiple choice flashcard
        aspect_options = ["perfective", "imperfective"]
        correct_aspect_index = aspect_options.index(verb.aspect.lower())
        
        aspect_flashcard = MultipleChoice(
            question=f"What is the aspect of '{dictionary_form}'?",
            options=aspect_options,
            correct_indices=[correct_aspect_index],
            tags=["russian", "verb", "aspect", "grammar", "multiple_choice"],
            title=f"{dictionary_form} - aspect (multiple choice)"
        )
        flashcards.append(aspect_flashcard)
        
        # Generate aspect pair flashcards if available
        if verb.aspect_pair and verb.aspect_pair.strip():
            flashcards.extend(self._generate_aspect_pair_flashcards(verb, dictionary_form))
        
        return flashcards
    
    def _generate_aspect_pair_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for aspect pairs."""
        flashcards = []
        
        # Create multiple choice for which verb is perfective
        if verb.aspect.lower() == "perfective":
            question = f"Which verb is the PERFECTIVE form?"
            options = [dictionary_form, verb.aspect_pair]
            correct_index = 0
        else:
            question = f"Which verb is the PERFECTIVE form?"
            options = [verb.aspect_pair, dictionary_form]
            correct_index = 0
        
        aspect_pair_flashcard = MultipleChoice(
            question=question,
            options=options,
            correct_indices=[correct_index],
            tags=["russian", "verb", "aspect_pair", "grammar", "multiple_choice"],
            title=f"{dictionary_form} - aspect pair comparison"
        )
        flashcards.append(aspect_pair_flashcard)
        
        # Also create the opposite question (which is imperfective)
        if verb.aspect.lower() == "perfective":
            question_imp = f"Which verb is the IMPERFECTIVE form?"
            options_imp = [dictionary_form, verb.aspect_pair]
            correct_index_imp = 1
        else:
            question_imp = f"Which verb is the IMPERFECTIVE form?"
            options_imp = [verb.aspect_pair, dictionary_form]
            correct_index_imp = 1
        
        aspect_pair_flashcard_imp = MultipleChoice(
            question=question_imp,
            options=options_imp,
            correct_indices=[correct_index_imp],
            tags=["russian", "verb", "aspect_pair", "grammar", "multiple_choice"],
            title=f"{dictionary_form} - aspect pair comparison (imperfective)"
        )
        flashcards.append(aspect_pair_flashcard_imp)
        
        return flashcards
    
    def _generate_conjugation_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for verb conjugation type."""
        flashcards = []
        
        # Generate conjugation flashcard (keep as two-sided)
        flashcard = self.create_two_sided_card(
            front=f"What conjugation type is '{dictionary_form}'?",
            back=verb.conjugation,
            tags=["russian", "verb", "conjugation", "grammar"],
            title=f"{dictionary_form} - conjugation"
        )
        flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_present_tense_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for present tense forms."""
        flashcards = []
        
        present_forms = {
            "я": ("first person singular", verb.present_first_singular),
            "ты": ("second person singular", verb.present_second_singular),
            "он/она/оно": ("third person singular", verb.present_third_singular),
            "мы": ("first person plural", verb.present_first_plural),
            "вы": ("second person plural", verb.present_second_plural),
            "они": ("third person plural", verb.present_third_plural)
        }
        
        for pronoun, (person_desc, form) in present_forms.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"present {person_desc}"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"present tense for {pronoun}",
                    word_type="verb",
                    tags=["russian", "verb", "present", "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_past_tense_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for past tense forms."""
        flashcards = []
        
        past_forms = {
            "он": ("masculine", verb.past_masculine),
            "она": ("feminine", verb.past_feminine),
            "оно": ("neuter", verb.past_neuter),
            "они": ("plural", verb.past_plural)
        }
        
        for pronoun, (gender_desc, form) in past_forms.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"past {gender_desc}"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"past tense for {pronoun}",
                    word_type="verb",
                    tags=["russian", "verb", "past", "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_future_tense_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for future tense forms."""
        flashcards = []
        
        future_forms = {
            "я": ("first person singular", verb.future_first_singular),
            "ты": ("second person singular", verb.future_second_singular),
            "он/она/оно": ("third person singular", verb.future_third_singular),
            "мы": ("first person plural", verb.future_first_plural),
            "вы": ("second person plural", verb.future_second_plural),
            "они": ("third person plural", verb.future_third_plural)
        }
        
        for pronoun, (person_desc, form) in future_forms.items():
            if self.should_create_flashcard(form, dictionary_form):
                grammatical_key = f"future {person_desc}"
                flashcard = self.create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"future tense for {pronoun}",
                    word_type="verb",
                    tags=["russian", "verb", "future", "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_imperative_flashcards(self, verb: Verb, dictionary_form: str) -> List[Any]:
        """Generate flashcards for imperative forms."""
        flashcards = []
        
        # Singular imperative
        if verb.imperative_singular and self.should_create_flashcard(verb.imperative_singular, dictionary_form):
            grammatical_key = "imperative singular"
            flashcard = self.create_fill_in_gap_card(
                dictionary_form=dictionary_form,
                target_form=verb.imperative_singular,
                form_description="singular imperative",
                word_type="verb",
                tags=["russian", "verb", "imperative", "grammar"],
                grammatical_key=grammatical_key
            )
            flashcards.append(flashcard)
        
        # Plural imperative
        if verb.imperative_plural and self.should_create_flashcard(verb.imperative_plural, dictionary_form):
            grammatical_key = "imperative plural"
            flashcard = self.create_fill_in_gap_card(
                dictionary_form=dictionary_form,
                target_form=verb.imperative_plural,
                form_description="plural imperative",
                word_type="verb",
                tags=["russian", "verb", "imperative", "grammar"],
                grammatical_key=grammatical_key
            )
            flashcards.append(flashcard)
        
        return flashcards
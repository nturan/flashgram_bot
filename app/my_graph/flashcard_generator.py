import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.flashcards import TwoSidedCard, flashcard_service
from app.grammar.russian import Noun, Adjective, Verb

logger = logging.getLogger(__name__)

class FlashcardGenerator:
    """Tool for generating flashcards from grammatical analysis results."""
    
    def __init__(self):
        self.service = flashcard_service
    
    def generate_flashcards_from_grammar(self, grammar_obj: Any, word_type: str) -> List[TwoSidedCard]:
        """
        Generate flashcards from a grammar object (Noun, Adjective, or Verb).
        
        Args:
            grammar_obj: The parsed grammar object (Noun, Adjective, or Verb)
            word_type: Type of word ("noun", "adjective", "verb")
            
        Returns:
            List of TwoSidedCard flashcards
        """
        flashcards = []
        
        try:
            if isinstance(grammar_obj, Noun):
                flashcards = self._generate_noun_flashcards(grammar_obj)
            elif isinstance(grammar_obj, Adjective):
                flashcards = self._generate_adjective_flashcards(grammar_obj)
            elif isinstance(grammar_obj, Verb):
                flashcards = self._generate_verb_flashcards(grammar_obj)
            else:
                logger.warning(f"Unknown grammar object type: {type(grammar_obj)}")
                
        except Exception as e:
            logger.error(f"Error generating flashcards: {e}")
            
        return flashcards
    
    def _generate_noun_flashcards(self, noun: Noun) -> List[TwoSidedCard]:
        """Generate flashcards for a Russian noun."""
        flashcards = []
        dictionary_form = noun.dictionary_form
        
        # Generate flashcards for singular forms
        for case, form in noun.singular.items():
            if form and form.strip():  # Only create if form exists
                flashcard = TwoSidedCard(
                    front=f"What is the {case.upper()} singular form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "noun", "singular", case, "grammar"],
                    title=f"{dictionary_form} - {case.upper()} singular"
                )
                flashcards.append(flashcard)
        
        # Generate flashcards for plural forms
        for case, form in noun.plural.items():
            if form and form.strip():  # Only create if form exists
                flashcard = TwoSidedCard(
                    front=f"What is the {case.upper()} plural form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "noun", "plural", case, "grammar"],
                    title=f"{dictionary_form} - {case.upper()} plural"
                )
                flashcards.append(flashcard)
        
        # Generate gender flashcard
        flashcard = TwoSidedCard(
            front=f"What is the gender of '{dictionary_form}'?",
            back=noun.gender,
            tags=["russian", "noun", "gender", "grammar"],
            title=f"{dictionary_form} - gender"
        )
        flashcards.append(flashcard)
        
        # Generate animacy flashcard
        animacy_text = "animate" if noun.animacy else "inanimate"
        flashcard = TwoSidedCard(
            front=f"Is '{dictionary_form}' animate or inanimate?",
            back=animacy_text,
            tags=["russian", "noun", "animacy", "grammar"],
            title=f"{dictionary_form} - animacy"
        )
        flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_adjective_flashcards(self, adjective: Adjective) -> List[TwoSidedCard]:
        """Generate flashcards for a Russian adjective."""
        flashcards = []
        dictionary_form = adjective.dictionary_form
        
        # Generate flashcards for masculine forms
        for case, form in adjective.masculine.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the {case.upper()} masculine form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "adjective", "masculine", case, "grammar"],
                    title=f"{dictionary_form} - {case.upper()} masculine"
                )
                flashcards.append(flashcard)
        
        # Generate flashcards for feminine forms
        for case, form in adjective.feminine.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the {case.upper()} feminine form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "adjective", "feminine", case, "grammar"],
                    title=f"{dictionary_form} - {case.upper()} feminine"
                )
                flashcards.append(flashcard)
        
        # Generate flashcards for neuter forms
        for case, form in adjective.neuter.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the {case.upper()} neuter form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "adjective", "neuter", case, "grammar"],
                    title=f"{dictionary_form} - {case.upper()} neuter"
                )
                flashcards.append(flashcard)
        
        # Generate flashcards for plural forms
        for case, form in adjective.plural.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the {case.upper()} plural form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "adjective", "plural", case, "grammar"],
                    title=f"{dictionary_form} - {case.upper()} plural"
                )
                flashcards.append(flashcard)
        
        # Generate flashcards for short forms if they exist
        short_forms = {
            "masculine": adjective.short_form_masculine,
            "feminine": adjective.short_form_feminine,
            "neuter": adjective.short_form_neuter,
            "plural": adjective.short_form_plural
        }
        
        for gender, form in short_forms.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the short {gender} form of '{dictionary_form}'?",
                    back=form,
                    tags=["russian", "adjective", "short_form", gender, "grammar"],
                    title=f"{dictionary_form} - short {gender}"
                )
                flashcards.append(flashcard)
        
        # Generate comparative flashcard if it exists
        if adjective.comparative and adjective.comparative.strip():
            flashcard = TwoSidedCard(
                front=f"What is the comparative form of '{dictionary_form}'?",
                back=adjective.comparative,
                tags=["russian", "adjective", "comparative", "grammar"],
                title=f"{dictionary_form} - comparative"
            )
            flashcards.append(flashcard)
        
        # Generate superlative flashcard if it exists
        if adjective.superlative and adjective.superlative.strip():
            flashcard = TwoSidedCard(
                front=f"What is the superlative form of '{dictionary_form}'?",
                back=adjective.superlative,
                tags=["russian", "adjective", "superlative", "grammar"],
                title=f"{dictionary_form} - superlative"
            )
            flashcards.append(flashcard)
        
        return flashcards
    
    def _generate_verb_flashcards(self, verb: Verb) -> List[TwoSidedCard]:
        """Generate flashcards for a Russian verb."""
        flashcards = []
        dictionary_form = verb.dictionary_form
        
        # Generate aspect flashcard
        flashcard = TwoSidedCard(
            front=f"What is the aspect of '{dictionary_form}'?",
            back=verb.aspect,
            tags=["russian", "verb", "aspect", "grammar"],
            title=f"{dictionary_form} - aspect"
        )
        flashcards.append(flashcard)
        
        # Generate conjugation flashcard
        flashcard = TwoSidedCard(
            front=f"What conjugation type is '{dictionary_form}'?",
            back=verb.conjugation,
            tags=["russian", "verb", "conjugation", "grammar"],
            title=f"{dictionary_form} - conjugation"
        )
        flashcards.append(flashcard)
        
        # Generate aspect pair flashcard if it exists
        if verb.aspect_pair and verb.aspect_pair.strip():
            flashcard = TwoSidedCard(
                front=f"What is the aspect pair of '{dictionary_form}'?",
                back=verb.aspect_pair,
                tags=["russian", "verb", "aspect_pair", "grammar"],
                title=f"{dictionary_form} - aspect pair"
            )
            flashcards.append(flashcard)
        
        # Generate present tense flashcards (for imperfective verbs)
        present_forms = {
            "я": verb.present_first_singular,
            "ты": verb.present_second_singular,
            "он/она/оно": verb.present_third_singular,
            "мы": verb.present_first_plural,
            "вы": verb.present_second_plural,
            "они": verb.present_third_plural
        }
        
        for pronoun, form in present_forms.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the present tense form of '{dictionary_form}' for '{pronoun}'?",
                    back=form,
                    tags=["russian", "verb", "present", "grammar"],
                    title=f"{dictionary_form} - present {pronoun}"
                )
                flashcards.append(flashcard)
        
        # Generate past tense flashcards
        past_forms = {
            "он": verb.past_masculine,
            "она": verb.past_feminine,
            "оно": verb.past_neuter,
            "они": verb.past_plural
        }
        
        for pronoun, form in past_forms.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the past tense form of '{dictionary_form}' for '{pronoun}'?",
                    back=form,
                    tags=["russian", "verb", "past", "grammar"],
                    title=f"{dictionary_form} - past {pronoun}"
                )
                flashcards.append(flashcard)
        
        # Generate future tense flashcards if they exist
        future_forms = {
            "я": verb.future_first_singular,
            "ты": verb.future_second_singular,
            "он/она/оно": verb.future_third_singular,
            "мы": verb.future_first_plural,
            "вы": verb.future_second_plural,
            "они": verb.future_third_plural
        }
        
        for pronoun, form in future_forms.items():
            if form and form.strip():
                flashcard = TwoSidedCard(
                    front=f"What is the future tense form of '{dictionary_form}' for '{pronoun}'?",
                    back=form,
                    tags=["russian", "verb", "future", "grammar"],
                    title=f"{dictionary_form} - future {pronoun}"
                )
                flashcards.append(flashcard)
        
        # Generate imperative flashcards if they exist
        if verb.imperative_singular and verb.imperative_singular.strip():
            flashcard = TwoSidedCard(
                front=f"What is the singular imperative form of '{dictionary_form}'?",
                back=verb.imperative_singular,
                tags=["russian", "verb", "imperative", "grammar"],
                title=f"{dictionary_form} - imperative singular"
            )
            flashcards.append(flashcard)
        
        if verb.imperative_plural and verb.imperative_plural.strip():
            flashcard = TwoSidedCard(
                front=f"What is the plural imperative form of '{dictionary_form}'?",
                back=verb.imperative_plural,
                tags=["russian", "verb", "imperative", "grammar"],
                title=f"{dictionary_form} - imperative plural"
            )
            flashcards.append(flashcard)
        
        return flashcards
    
    def save_flashcards_to_database(self, flashcards: List[TwoSidedCard]) -> int:
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
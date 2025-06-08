import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.flashcards import TwoSidedCard, MultipleChoice, FillInTheBlank, flashcard_service
from app.grammar.russian import Noun, Adjective, Verb
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class FlashcardGenerator:
    """Tool for generating flashcards from grammatical analysis results."""
    
    def __init__(self):
        self.service = flashcard_service
        # Initialize LLM for sentence generation (use same config as main tutor)
        from app.config import settings
        from pydantic import SecretStr
        self.llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
    
    def generate_flashcards_from_grammar(self, grammar_obj: Any, word_type: str) -> List[Any]:
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
    
    def _generate_noun_flashcards(self, noun: Noun) -> List[Any]:
        """Generate flashcards for a Russian noun."""
        flashcards = []
        dictionary_form = noun.dictionary_form
        
        # Generate fill-in-the-gap flashcards for singular forms
        for case, form in noun.singular.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():  # Only create if form exists and is different
                grammatical_key = f"{case.upper()} singular"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} singular",
                    word_type="noun",
                    tags=["russian", "noun", "singular", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for plural forms
        for case, form in noun.plural.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():  # Only create if form exists and is different
                grammatical_key = f"{case.upper()} plural"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} plural",
                    word_type="noun",
                    tags=["russian", "noun", "plural", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Keep gender and animacy as two-sided cards (they don't involve suffix changes)
        gender_flashcard = TwoSidedCard(
            front=f"What is the gender of '{dictionary_form}'?",
            back=noun.gender,
            tags=["russian", "noun", "gender", "grammar"],
            title=f"{dictionary_form} - gender"
        )
        flashcards.append(gender_flashcard)
        
        animacy_text = "animate" if noun.animacy else "inanimate"
        animacy_flashcard = TwoSidedCard(
            front=f"Is '{dictionary_form}' animate or inanimate?",
            back=animacy_text,
            tags=["russian", "noun", "animacy", "grammar"],
            title=f"{dictionary_form} - animacy"
        )
        flashcards.append(animacy_flashcard)
        
        return flashcards
    
    def _generate_adjective_flashcards(self, adjective: Adjective) -> List[Any]:
        """Generate flashcards for a Russian adjective."""
        flashcards = []
        dictionary_form = adjective.dictionary_form
        
        # Generate fill-in-the-gap flashcards for masculine forms
        for case, form in adjective.masculine.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"{case.upper()} masculine"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} masculine",
                    word_type="adjective",
                    tags=["russian", "adjective", "masculine", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for feminine forms
        for case, form in adjective.feminine.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"{case.upper()} feminine"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} feminine",
                    word_type="adjective",
                    tags=["russian", "adjective", "feminine", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for neuter forms
        for case, form in adjective.neuter.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"{case.upper()} neuter"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} neuter",
                    word_type="adjective",
                    tags=["russian", "adjective", "neuter", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for plural forms
        for case, form in adjective.plural.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"{case.upper()} plural"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"{case.upper()} plural",
                    word_type="adjective",
                    tags=["russian", "adjective", "plural", case, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for short forms if they exist
        short_forms = {
            "masculine": adjective.short_form_masculine,
            "feminine": adjective.short_form_feminine,
            "neuter": adjective.short_form_neuter,
            "plural": adjective.short_form_plural
        }
        
        for gender, form in short_forms.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"short {gender}"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"short {gender}",
                    word_type="adjective",
                    tags=["russian", "adjective", "short_form", gender, "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Keep comparative and superlative as two-sided cards (they're often quite different)
        if adjective.comparative and adjective.comparative.strip():
            comparative_flashcard = TwoSidedCard(
                front=f"What is the comparative form of '{dictionary_form}'?",
                back=adjective.comparative,
                tags=["russian", "adjective", "comparative", "grammar"],
                title=f"{dictionary_form} - comparative"
            )
            flashcards.append(comparative_flashcard)
        
        if adjective.superlative and adjective.superlative.strip():
            superlative_flashcard = TwoSidedCard(
                front=f"What is the superlative form of '{dictionary_form}'?",
                back=adjective.superlative,
                tags=["russian", "adjective", "superlative", "grammar"],
                title=f"{dictionary_form} - superlative"
            )
            flashcards.append(superlative_flashcard)
        
        return flashcards
    
    def _generate_verb_flashcards(self, verb: Verb) -> List[Any]:
        """Generate flashcards for a Russian verb."""
        flashcards = []
        dictionary_form = verb.dictionary_form
        
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
        
        # Generate aspect pair multiple choice flashcard if it exists
        if verb.aspect_pair and verb.aspect_pair.strip():
            # Create multiple choice for which verb is perfective/imperfective
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
        
        # Generate conjugation flashcard (keep as two-sided)
        flashcard = TwoSidedCard(
            front=f"What conjugation type is '{dictionary_form}'?",
            back=verb.conjugation,
            tags=["russian", "verb", "conjugation", "grammar"],
            title=f"{dictionary_form} - conjugation"
        )
        flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for present tense (for imperfective verbs)
        present_forms = {
            "я": ("first person singular", verb.present_first_singular),
            "ты": ("second person singular", verb.present_second_singular),
            "он/она/оно": ("third person singular", verb.present_third_singular),
            "мы": ("first person plural", verb.present_first_plural),
            "вы": ("second person plural", verb.present_second_plural),
            "они": ("third person plural", verb.present_third_plural)
        }
        
        for pronoun, (person_desc, form) in present_forms.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"present {person_desc}"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"present tense for {pronoun}",
                    word_type="verb",
                    tags=["russian", "verb", "present", "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for past tense
        past_forms = {
            "он": ("masculine", verb.past_masculine),
            "она": ("feminine", verb.past_feminine),
            "оно": ("neuter", verb.past_neuter),
            "они": ("plural", verb.past_plural)
        }
        
        for pronoun, (gender_desc, form) in past_forms.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"past {gender_desc}"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"past tense for {pronoun}",
                    word_type="verb",
                    tags=["russian", "verb", "past", "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for future tense if they exist
        future_forms = {
            "я": ("first person singular", verb.future_first_singular),
            "ты": ("second person singular", verb.future_second_singular),
            "он/она/оно": ("third person singular", verb.future_third_singular),
            "мы": ("first person plural", verb.future_first_plural),
            "вы": ("second person plural", verb.future_second_plural),
            "они": ("third person plural", verb.future_third_plural)
        }
        
        for pronoun, (person_desc, form) in future_forms.items():
            if form and form.strip() and form.lower() != dictionary_form.lower():
                grammatical_key = f"future {person_desc}"
                flashcard = self._create_fill_in_gap_card(
                    dictionary_form=dictionary_form,
                    target_form=form,
                    form_description=f"future tense for {pronoun}",
                    word_type="verb",
                    tags=["russian", "verb", "future", "grammar"],
                    grammatical_key=grammatical_key
                )
                flashcards.append(flashcard)
        
        # Generate fill-in-the-gap flashcards for imperative forms if they exist
        if verb.imperative_singular and verb.imperative_singular.strip() and verb.imperative_singular.lower() != dictionary_form.lower():
            grammatical_key = "imperative singular"
            flashcard = self._create_fill_in_gap_card(
                dictionary_form=dictionary_form,
                target_form=verb.imperative_singular,
                form_description="singular imperative",
                word_type="verb",
                tags=["russian", "verb", "imperative", "grammar"],
                grammatical_key=grammatical_key
            )
            flashcards.append(flashcard)
        
        if verb.imperative_plural and verb.imperative_plural.strip() and verb.imperative_plural.lower() != dictionary_form.lower():
            grammatical_key = "imperative plural"
            flashcard = self._create_fill_in_gap_card(
                dictionary_form=dictionary_form,
                target_form=verb.imperative_plural,
                form_description="plural imperative",
                word_type="verb",
                tags=["russian", "verb", "imperative", "grammar"],
                grammatical_key=grammatical_key
            )
            flashcards.append(flashcard)
        
        return flashcards
    
    def save_flashcards_to_database(self, flashcards: List[Any]) -> int:
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
    
    def _generate_example_sentence(self, word: str, form: str, case_or_form_description: str, word_type: str) -> str:
        """Generate an example sentence using the LLM for a specific grammatical form."""
        try:
            prompt = f"""Generate a simple, natural Russian sentence that uses the word "{form}" ({case_or_form_description} form of "{word}").

Requirements:
- The sentence should be 6-12 words long
- Use everyday, conversational Russian
- The context should make the grammatical form clear
- Focus on common, practical usage
- Avoid special punctuation (no quotes, parentheses, asterisks, underscores)
- Use only basic punctuation: periods, commas, exclamation marks, question marks
- Return ONLY the Russian sentence, nothing else

Example format: "Я читаю интересную книгу в библиотеке."
"""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            sentence = response.content.strip()
            
            # Clean the sentence of problematic characters
            sentence = self._clean_sentence_for_telegram(sentence)
            
            # Basic validation - ensure the target form appears in the sentence
            if form.lower() in sentence.lower():
                return sentence
            else:
                # Fallback if LLM didn't include the form
                return f"В этом предложении используется слово {form}."
                
        except Exception as e:
            logger.error(f"Error generating example sentence: {e}")
            # Fallback sentence
            return f"Пример использования: {form}."
    
    def _extract_suffix(self, dictionary_form: str, inflected_form: str) -> tuple[str, str]:
        """Extract the suffix from an inflected form.
        Returns (stem, suffix) where stem + suffix = inflected_form"""
        try:
            # Find the common prefix (stem)
            dict_lower = dictionary_form.lower()
            inflected_lower = inflected_form.lower()
            
            # Find longest common prefix
            common_length = 0
            min_length = min(len(dict_lower), len(inflected_lower))
            
            for i in range(min_length):
                if dict_lower[i] == inflected_lower[i]:
                    common_length += 1
                else:
                    break
            
            # If no common prefix or very short, use a safe minimum
            if common_length < 2:
                # For very different forms, take at least 2 characters as stem
                safe_stem_length = min(2, len(inflected_form) - 1)
                stem = inflected_form[:safe_stem_length]
                suffix = inflected_form[safe_stem_length:]
            else:
                # Use the common prefix as stem, but ensure we don't go too far
                # Leave at least 1 character for the suffix if possible
                if common_length >= len(inflected_form):
                    stem = inflected_form[:-1] if len(inflected_form) > 1 else inflected_form
                    suffix = inflected_form[-1:] if len(inflected_form) > 1 else ""
                else:
                    stem = inflected_form[:common_length]
                    suffix = inflected_form[common_length:]
            
            return stem, suffix
            
        except Exception as e:
            logger.error(f"Error extracting suffix from '{dictionary_form}' -> '{inflected_form}': {e}")
            # Fallback: take first half as stem, second half as suffix
            mid_point = len(inflected_form) // 2
            return inflected_form[:mid_point], inflected_form[mid_point:]
    
    def _clean_sentence_for_telegram(self, sentence: str) -> str:
        """Clean sentence to avoid Telegram markdown parsing issues."""
        try:
            # Remove or replace problematic characters that can break markdown
            problematic_chars = {
                '"': '',  # Remove quotes
                "'": '',  # Remove single quotes
                '«': '',  # Remove Russian quotes
                '»': '',  # Remove Russian quotes
                '_': ' ',  # Replace underscores with spaces
                '*': '',  # Remove asterisks
                '`': '',  # Remove backticks
                '[': '(',  # Replace square brackets
                ']': ')',
                '{': '(',  # Replace curly brackets  
                '}': ')',
                '|': ' ',  # Replace pipes with spaces
                '\\': '',  # Remove backslashes
            }
            
            cleaned = sentence
            for char, replacement in problematic_chars.items():
                cleaned = cleaned.replace(char, replacement)
            
            # Clean up multiple spaces
            while '  ' in cleaned:
                cleaned = cleaned.replace('  ', ' ')
            
            return cleaned.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning sentence: {e}")
            return sentence
    
    def _create_fill_in_gap_card(self, dictionary_form: str, target_form: str, form_description: str, word_type: str, tags: List[str], grammatical_key: str = None) -> FillInTheBlank:
        """Create a fill-in-the-gap flashcard for a grammatical form."""
        
        # Generate example sentence
        sentence = self._generate_example_sentence(dictionary_form, target_form, form_description, word_type)
        
        # Extract stem and suffix
        stem, suffix = self._extract_suffix(dictionary_form, target_form)
        
        # Create the sentence with masked suffix
        masked_word = f"{stem}{{blank}}"
        sentence_with_blank = sentence.replace(target_form, masked_word)
        
        # If replacement didn't work (case differences, etc.), try case-insensitive
        if "{blank}" not in sentence_with_blank:
            # Try to find the word with different cases
            words = sentence.split()
            for i, word in enumerate(words):
                if word.lower().replace(".", "").replace(",", "").replace("!", "").replace("?", "") == target_form.lower():
                    # Replace this word with the masked version
                    punctuation = ""
                    clean_word = word
                    for punct in ".,!?":
                        if word.endswith(punct):
                            punctuation = punct
                            clean_word = word[:-1]
                            break
                    
                    words[i] = f"{stem}{{blank}}{punctuation}"
                    sentence_with_blank = " ".join(words)
                    break
            
            # If still no blank, add it at the end
            if "{blank}" not in sentence_with_blank:
                sentence_with_blank = f"{sentence} ({stem}{{blank}})"
        
        return FillInTheBlank(
            text_with_blanks=sentence_with_blank,
            answers=[suffix],
            case_sensitive=False,
            tags=tags + ["fill_in_gap", "suffix"],
            title=f"{dictionary_form} - {form_description} (gap fill)",
            # Store the grammatical key for the hint
            metadata={
                "form_description": form_description, 
                "dictionary_form": dictionary_form,
                "grammatical_key": grammatical_key or form_description
            }
        )

# Global instance
flashcard_generator = FlashcardGenerator()
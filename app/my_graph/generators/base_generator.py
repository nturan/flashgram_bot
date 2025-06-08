"""Base flashcard generator with common functionality."""

import logging
from typing import List, Any
from app.flashcards.models import FillInTheBlank, TwoSidedCard
from app.my_graph.sentence_generation import LLMSentenceGenerator, TextProcessor
from app.my_graph.utils import SuffixExtractor, FormAnalyzer

logger = logging.getLogger(__name__)


class BaseGenerator:
    """Base class for word-type specific flashcard generators."""
    
    def __init__(self):
        self.sentence_generator = LLMSentenceGenerator()
        self.text_processor = TextProcessor()
        self.suffix_extractor = SuffixExtractor()
        self.form_analyzer = FormAnalyzer()
    
    def create_fill_in_gap_card(self, dictionary_form: str, target_form: str, 
                               form_description: str, word_type: str, 
                               tags: List[str], grammatical_key: str = None) -> FillInTheBlank:
        """Create a fill-in-the-gap flashcard for a grammatical form."""
        
        # Generate example sentence
        sentence = self.sentence_generator.generate_example_sentence(
            dictionary_form, target_form, form_description, word_type
        )
        
        # Extract stem and suffix
        stem, suffix = self.suffix_extractor.extract_suffix(dictionary_form, target_form)
        
        # Create the sentence with masked suffix
        sentence_with_blank = self.text_processor.create_sentence_with_blank(
            sentence, target_form, stem
        )
        
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
    
    def create_two_sided_card(self, front: str, back: str, tags: List[str], title: str) -> TwoSidedCard:
        """Create a two-sided flashcard."""
        return TwoSidedCard(
            front=front,
            back=back,
            tags=tags,
            title=title
        )
    
    def should_create_flashcard(self, form: str, dictionary_form: str) -> bool:
        """Determine if a flashcard should be created for this form."""
        return (form and 
                form.strip() and 
                form.lower() != dictionary_form.lower())
    
    def generate_flashcards_from_grammar(self, grammar_obj: Any, word_type: str) -> List[Any]:
        """Generate flashcards from a grammar object. To be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement generate_flashcards_from_grammar")
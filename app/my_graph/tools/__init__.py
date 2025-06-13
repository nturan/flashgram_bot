"""Tool implementations for the Conversational Russian Tutor chatbot."""

from .grammar_analysis import analyze_russian_grammar_impl
from .text_correction import correct_multilingual_mistakes_impl
from .flashcard_generation import generate_flashcards_from_analysis_impl
from .translation import translate_phrase_impl
from .sentence_generation import generate_example_sentences_impl
from .bulk_processing import (
    process_bulk_text_for_flashcards_impl,
    check_bulk_processing_status_impl,
)

__all__ = [
    "analyze_russian_grammar_impl",
    "correct_multilingual_mistakes_impl",
    "generate_flashcards_from_analysis_impl",
    "translate_phrase_impl",
    "generate_example_sentences_impl",
    "process_bulk_text_for_flashcards_impl",
    "check_bulk_processing_status_impl",
]
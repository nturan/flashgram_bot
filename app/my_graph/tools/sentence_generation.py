"""Sentence generation tool implementation."""

import logging
from typing import Dict, Any, Optional

from app.my_graph.sentence_generation import LLMSentenceGenerator

logger = logging.getLogger(__name__)


def generate_example_sentences_impl(
    word: str, grammatical_context: str, theme: Optional[str] = None
) -> Dict[str, Any]:
    """Implementation for example sentence generation tool."""
    try:
        sentence_generator = LLMSentenceGenerator()

        examples = []

        # Generate 2-3 example sentences
        for i in range(3):
            if theme:
                sentence = sentence_generator.generate_contextual_sentence(
                    word, word, grammatical_context, theme
                )
            else:
                sentence = sentence_generator.generate_example_sentence(
                    word, word, grammatical_context, "word"
                )
            examples.append(sentence)

        return {
            "word": word,
            "context": grammatical_context,
            "theme": theme,
            "examples": examples,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error generating example sentences: {e}")
        return {"word": word, "error": str(e), "success": False}
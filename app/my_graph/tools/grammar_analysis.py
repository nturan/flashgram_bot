"""Grammar analysis tool implementation using PyMorphy2."""

import logging
from typing import Dict, Any

from app.my_graph.utils.pymorphy2_analyzer import pymorphy2_analyze_russian_grammar_impl

logger = logging.getLogger(__name__)


def analyze_russian_grammar_impl(russian_word: str) -> Dict[str, Any]:
    """Implementation for grammar analysis tool using PyMorphy2."""
    try:
        logger.info(f"[PYMORPHY2-ONLY] Analyzing Russian word '{russian_word}' with PyMorphy2")
        
        # Use pymorphy2 for morphological analysis
        result = pymorphy2_analyze_russian_grammar_impl(russian_word)
        
        if result.get("success"):
            logger.info(f"[PYMORPHY2-SUCCESS] PyMorphy2 analysis successful for '{russian_word}'")
            return {"word": russian_word, "analysis": result, "success": True}
        else:
            logger.warning(f"[PYMORPHY2-FAILED] PyMorphy2 analysis failed for '{russian_word}': {result.get('message', 'Unknown error')}")
            return {"word": russian_word, "analysis": result, "success": False}

    except Exception as e:
        logger.error(f"[PYMORPHY2-ERROR] Error in grammar analysis for '{russian_word}': {e}")
        return {"word": russian_word, "error": str(e), "success": False}
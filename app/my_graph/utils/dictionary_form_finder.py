"""Unified dictionary form finder combining Hunspell and LLM analysis."""

import logging
from typing import Optional, Dict, Any, List
from app.my_graph.utils.hunspell_analyzer import get_hunspell_analyzer

logger = logging.getLogger(__name__)


def find_best_dictionary_form(word: str, grammar_analysis: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """Find the best dictionary form for a Russian word using multiple methods.
    
    Priority order:
    1. Hunspell dictionary form (most reliable)
    2. Grammar analysis dictionary_form field
    3. Original word (fallback)
    
    Args:
        word: The Russian word to find dictionary form for
        grammar_analysis: Optional grammar analysis result from analyze_russian_grammar_impl
        
    Returns:
        Best dictionary form found, or None if no reliable form found
    """
    # Method 1: Try Hunspell first (most reliable)
    analyzer = get_hunspell_analyzer()
    if analyzer.is_available():
        hunspell_form = analyzer.find_dictionary_form(word)
        if hunspell_form:
            logger.info(f"Found Hunspell dictionary form for '{word}': '{hunspell_form}'")
            return hunspell_form
    
    # Method 2: Use grammar analysis if available
    if grammar_analysis and grammar_analysis.get("success", False):
        analysis = grammar_analysis.get("analysis", {})
        
        # Check each grammar type for dictionary_form
        for grammar_type in ["noun_grammar", "adjective_grammar", "verb_grammar", "pronoun_grammar", "number_grammar"]:
            grammar_obj = analysis.get(grammar_type)
            if grammar_obj and hasattr(grammar_obj, 'dictionary_form'):
                llm_form = grammar_obj.dictionary_form
                if llm_form and llm_form.strip():
                    logger.info(f"Found LLM dictionary form for '{word}': '{llm_form}'")
                    return llm_form.strip()
    
    # Method 3: Fallback to original word
    logger.warning(f"No dictionary form found for '{word}', using original word")
    return word


def get_word_validity_info(word: str) -> Dict[str, Any]:
    """Get information about word validity and suggestions.
    
    Args:
        word: Russian word to check
        
    Returns:
        Dictionary with validity information
    """
    analyzer = get_hunspell_analyzer()
    
    if not analyzer.is_available():
        return {
            "is_valid": None,
            "suggestions": [],
            "hunspell_available": False,
            "message": "Hunspell analyzer not available"
        }
    
    analysis = analyzer.analyze_word(word)
    
    return {
        "is_valid": analysis.is_valid,
        "suggestions": analysis.suggestions[:5],  # Limit to 5 suggestions
        "stems": analysis.stems,
        "dictionary_forms": list(analysis.dictionary_forms),
        "hunspell_available": True
    }


def find_all_possible_dictionary_forms(word: str) -> List[str]:
    """Find all possible dictionary forms for a word from different sources.
    
    Args:
        word: Russian word to analyze
        
    Returns:
        List of unique dictionary forms found
    """
    forms = []
    
    # Get Hunspell forms
    analyzer = get_hunspell_analyzer()
    if analyzer.is_available():
        analysis = analyzer.analyze_word(word)
        forms.extend(analysis.stems)
        forms.extend(analysis.dictionary_forms)
    
    # Remove duplicates and empty strings
    unique_forms = []
    for form in forms:
        if form and form.strip() and form not in unique_forms:
            unique_forms.append(form.strip())
    
    return unique_forms


def validate_russian_word(word: str) -> Dict[str, Any]:
    """Validate a Russian word and provide suggestions if invalid.
    
    Args:
        word: Russian word to validate
        
    Returns:
        Validation result with suggestions
    """
    analyzer = get_hunspell_analyzer()
    
    if not analyzer.is_available():
        return {
            "is_valid": None,
            "word": word,
            "suggestions": [],
            "message": "Cannot validate - Hunspell not available"
        }
    
    is_valid = analyzer.is_word_valid(word)
    suggestions = [] if is_valid else analyzer.get_suggestions(word, limit=5)
    
    result = {
        "is_valid": is_valid,
        "word": word,
        "suggestions": suggestions
    }
    
    if is_valid:
        result["message"] = "Word is valid in Russian dictionary"
    else:
        if suggestions:
            result["message"] = f"Word not found. Suggestions: {', '.join(suggestions[:3])}"
        else:
            result["message"] = "Word not found and no suggestions available"
    
    return result


# Convenience functions for backward compatibility
def get_dictionary_form(word: str) -> Optional[str]:
    """Simple function to get dictionary form (backward compatibility)."""
    return find_best_dictionary_form(word)


def is_valid_russian_word(word: str) -> bool:
    """Simple function to check if word is valid (backward compatibility)."""
    result = validate_russian_word(word)
    return result.get("is_valid", False)
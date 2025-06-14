"""Main PyMorphy2 analysis function."""

import logging
from typing import Dict, Any
from app.grammar.russian import WordClassification
from .base_analyzer import PyMorphy2Analyzer
from .noun_analyzer import PyMorphy2NounAnalyzer
from .verb_analyzer import PyMorphy2VerbAnalyzer
from .adjective_analyzer import PyMorphy2AdjectiveAnalyzer
from .pronoun_analyzer import PyMorphy2PronounAnalyzer
from .number_analyzer import PyMorphy2NumberAnalyzer

logger = logging.getLogger(__name__)


def pymorphy2_analyze_russian_grammar_impl(russian_word: str) -> Dict[str, Any]:
    """PyMorphy2-based implementation for grammar analysis.
    
    Args:
        russian_word: Russian word to analyze
        
    Returns:
        Analysis result dictionary
    """
    try:
        analyzer = PyMorphy2Analyzer()
        
        if not analyzer.is_available():
            return {
                "word": russian_word,
                "success": False,
                "error": "PyMorphy2 analyzer not available",
                "message": "Morphological analysis requires PyMorphy2 installation"
            }
        
        # Get morphological analysis
        analysis = analyzer.analyze_word(russian_word)
        
        if not analysis:
            return {
                "word": russian_word,
                "success": False,
                "message": f"No morphological analysis found for '{russian_word}'"
            }
        
        # Create analysis info
        pymorphy_info = {
            "normal_form": analysis.normal_form,
            "pos": analysis.pos,
            "confidence": analysis.confidence,
            "variants": analysis.variants
        }
        
        # Determine word type
        word_type_map = {
            'NOUN': 'noun',
            'ADJF': 'adjective',  # Full adjective
            'ADJS': 'adjective',  # Short adjective  
            'VERB': 'verb',
            'INFN': 'verb',       # Infinitive
            'PRTF': 'verb',       # Participle
            'PRTS': 'verb',       # Short participle
            'GRND': 'verb',       # Gerund
            'NPRO': 'pronoun',    # Noun-pronoun
            'NUMR': 'number',     # Number
        }
        
        word_type = word_type_map.get(analysis.pos, 'unknown')
        
        # Special handling for numbers that might be tagged as adjectives
        if word_type == 'adjective' and analysis.normal_form in [
            'один', 'одна', 'одно', 'два', 'три', 'четыре', 'пять', 'шесть', 
            'семь', 'восемь', 'девять', 'десять', 'одиннадцать', 'двенадцать',
            'тринадцать', 'четырнадцать', 'пятнадцать', 'шестнадцать',
            'семнадцать', 'восемнадцать', 'девятнадцать', 'двадцать'
        ]:
            word_type = 'number'
        
        # Handle unsupported word types gracefully
        if word_type == 'unknown':
            # Log but don't fail - just skip these words in bulk processing
            logger.info(f"Skipping unsupported word type '{analysis.pos}' for word '{russian_word}' (types like adverbs, particles, predicatives are not needed for language learning)")
            return {
                "word": russian_word,
                "success": False,
                "pymorphy_analysis": pymorphy_info,
                "message": f"Word type '{analysis.pos}' not supported for language learning (skipping)",
                "skip_reason": "unsupported_word_type"
            }
        
        # Create classification
        classification = WordClassification(
            word_type=word_type,
            russian_word=analysis.normal_form,
            original_word=russian_word
        )
        
        result = {
            "original_human_input": russian_word,
            "classification": classification,
            "pymorphy_analysis": pymorphy_info,
            "noun_grammar": None,
            "adjective_grammar": None,
            "verb_grammar": None,
            "pronoun_grammar": None,
            "number_grammar": None,
            "final_answer": None,
        }
        
        # Analyze based on word type
        if word_type == "noun":
            noun_analyzer = PyMorphy2NounAnalyzer()
            noun_grammar = noun_analyzer.analyze_noun(russian_word)
            
            if noun_grammar:
                result["noun_grammar"] = noun_grammar
                result["final_answer"] = noun_grammar.model_dump_json(indent=2)
                result["success"] = True
                
                logger.info(f"Successfully analyzed noun '{russian_word}' -> '{noun_grammar.dictionary_form}'")
                return result
            else:
                return {
                    "word": russian_word,
                    "success": False,
                    "pymorphy_analysis": pymorphy_info,
                    "message": f"Failed to generate noun grammar for '{russian_word}'"
                }
        
        elif word_type == "verb":
            verb_analyzer = PyMorphy2VerbAnalyzer()
            verb_grammar = verb_analyzer.analyze_verb(russian_word)
            
            if verb_grammar:
                result["verb_grammar"] = verb_grammar
                result["final_answer"] = verb_grammar.model_dump_json(indent=2)
                result["success"] = True
                
                logger.info(f"Successfully analyzed verb '{russian_word}' -> '{verb_grammar.dictionary_form}'")
                return result
            else:
                return {
                    "word": russian_word,
                    "success": False,
                    "pymorphy_analysis": pymorphy_info,
                    "message": f"Failed to generate verb grammar for '{russian_word}'"
                }
        
        elif word_type == "adjective":
            adjective_analyzer = PyMorphy2AdjectiveAnalyzer()
            adjective_grammar = adjective_analyzer.analyze_adjective(russian_word)
            
            if adjective_grammar:
                result["adjective_grammar"] = adjective_grammar
                result["final_answer"] = adjective_grammar.model_dump_json(indent=2)
                result["success"] = True
                
                logger.info(f"Successfully analyzed adjective '{russian_word}' -> '{adjective_grammar.dictionary_form}'")
                return result
            else:
                return {
                    "word": russian_word,
                    "success": False,
                    "pymorphy_analysis": pymorphy_info,
                    "message": f"Failed to generate adjective grammar for '{russian_word}'"
                }
        
        elif word_type == "pronoun":
            pronoun_analyzer = PyMorphy2PronounAnalyzer()
            pronoun_grammar = pronoun_analyzer.analyze_pronoun(russian_word)
            
            if pronoun_grammar:
                result["pronoun_grammar"] = pronoun_grammar
                result["final_answer"] = pronoun_grammar.model_dump_json(indent=2)
                result["success"] = True
                
                logger.info(f"Successfully analyzed pronoun '{russian_word}' -> '{pronoun_grammar.dictionary_form}'")
                return result
            else:
                return {
                    "word": russian_word,
                    "success": False,
                    "pymorphy_analysis": pymorphy_info,
                    "message": f"Failed to generate pronoun grammar for '{russian_word}'"
                }
        
        elif word_type == "number":
            number_analyzer = PyMorphy2NumberAnalyzer()
            number_grammar = number_analyzer.analyze_number(russian_word)
            
            if number_grammar:
                result["number_grammar"] = number_grammar
                result["final_answer"] = number_grammar.model_dump_json(indent=2)
                result["success"] = True
                
                logger.info(f"Successfully analyzed number '{russian_word}' -> '{number_grammar.dictionary_form}'")
                return result
            else:
                return {
                    "word": russian_word,
                    "success": False,
                    "pymorphy_analysis": pymorphy_info,
                    "message": f"Failed to generate number grammar for '{russian_word}'"
                }
        
        return {
            "word": russian_word,
            "success": False,
            "pymorphy_analysis": pymorphy_info,
            "message": f"Unsupported word type: {word_type}"
        }
        
    except Exception as e:
        logger.error(f"Error in PyMorphy2 grammar analysis for '{russian_word}': {e}")
        return {
            "word": russian_word,
            "success": False,
            "error": str(e)
        }
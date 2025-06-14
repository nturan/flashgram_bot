"""Hunspell-based morphological analyzer for Russian."""

import logging
import os
from pathlib import Path
from typing import List, Optional, Dict, Set
from dataclasses import dataclass

try:
    import hunspell
    HUNSPELL_AVAILABLE = True
except ImportError:
    HUNSPELL_AVAILABLE = False
    hunspell = None

logger = logging.getLogger(__name__)


@dataclass
class MorphAnalysis:
    """Result of morphological analysis."""
    word: str
    is_valid: bool
    stems: List[str]
    suggestions: List[str]
    dictionary_forms: Set[str]


class RussianHunspellAnalyzer:
    """Russian morphological analyzer using Hunspell dictionary files."""
    
    def __init__(self, dictionaries_path: Optional[str] = None):
        """Initialize the analyzer with Russian dictionary files.
        
        Args:
            dictionaries_path: Path to directory containing .aff and .dic files.
                              If None, uses default path relative to project root.
        """
        self.hunspell_obj = None
        self.available = HUNSPELL_AVAILABLE
        
        if not HUNSPELL_AVAILABLE:
            logger.warning("pyhunspell not available. Install with: pip install pyhunspell")
            return
            
        # Set default path if not provided
        if dictionaries_path is None:
            # Get project root (assuming this file is in app/my_graph/utils/)
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent.parent
            dictionaries_path = project_root / "dictionaries"
        else:
            dictionaries_path = Path(dictionaries_path)
        
        self.dictionaries_path = dictionaries_path
        self.aff_path = dictionaries_path / "ru_RU_utf8.aff"
        self.dic_path = dictionaries_path / "ru_RU_utf8.dic"
        
        # Initialize Hunspell
        self._init_hunspell()
    
    def _init_hunspell(self):
        """Initialize Hunspell with Russian dictionary files."""
        if not self.available:
            return
            
        try:
            # Check if dictionary files exist
            if not self.aff_path.exists():
                logger.error(f"Hunspell .aff file not found: {self.aff_path}")
                self.available = False
                return
                
            if not self.dic_path.exists():
                logger.error(f"Hunspell .dic file not found: {self.dic_path}")
                self.available = False
                return
            
            # Initialize Hunspell object
            self.hunspell_obj = hunspell.HunSpell(
                str(self.dic_path), 
                str(self.aff_path)
            )
            
            logger.info(f"Initialized Hunspell with Russian dictionary: {self.dic_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Hunspell: {e}")
            self.available = False
            self.hunspell_obj = None
    
    def is_available(self) -> bool:
        """Check if Hunspell analyzer is available for use."""
        return self.available and self.hunspell_obj is not None
    
    def _encode_for_hunspell(self, word: str) -> str:
        """Encode UTF-8 word for hunspell dictionary (KOI8-R)."""
        try:
            # Convert UTF-8 to KOI8-R for hunspell
            return word.encode('utf-8').decode('koi8-r', errors='ignore')
        except Exception:
            return word
    
    def _decode_from_hunspell(self, word) -> str:
        """Decode hunspell result back to UTF-8."""
        try:
            # If word is bytes, decode directly
            if isinstance(word, bytes):
                return word.decode('utf-8', errors='ignore')
            # If word is string, try KOI8-R to UTF-8 conversion
            elif isinstance(word, str):
                return word.encode('koi8-r').decode('utf-8', errors='ignore')
            else:
                return str(word)
        except Exception:
            return str(word)

    def analyze_word(self, word: str) -> MorphAnalysis:
        """Analyze a Russian word for morphological information.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            MorphAnalysis object with results
        """
        if not self.is_available():
            return MorphAnalysis(
                word=word,
                is_valid=False,
                stems=[],
                suggestions=[],
                dictionary_forms=set()
            )
        
        try:
            # Encode word for hunspell
            encoded_word = self._encode_for_hunspell(word)
            
            # Check if word is valid (exists in dictionary)
            is_valid = self.hunspell_obj.spell(encoded_word)
            
            # Get morphological analysis (stems/roots)
            stems = self.hunspell_obj.stem(encoded_word) if is_valid else []
            # Decode stems back to UTF-8
            stems = [self._decode_from_hunspell(stem) for stem in stems]
            
            # Get spelling suggestions if word is not valid
            suggestions = [] if is_valid else self.hunspell_obj.suggest(encoded_word)
            # Decode suggestions back to UTF-8
            suggestions = [self._decode_from_hunspell(suggestion) for suggestion in suggestions]
            
            # Extract dictionary forms from stems
            dictionary_forms = set()
            if stems:
                dictionary_forms.update(stems)
            
            # If word is not valid but we have suggestions, analyze them too
            if not is_valid and suggestions:
                for suggestion in suggestions[:3]:  # Limit to top 3 suggestions
                    encoded_suggestion = self._encode_for_hunspell(suggestion)
                    suggestion_stems = self.hunspell_obj.stem(encoded_suggestion)
                    if suggestion_stems:
                        decoded_stems = [self._decode_from_hunspell(stem) for stem in suggestion_stems]
                        dictionary_forms.update(decoded_stems)
            
            return MorphAnalysis(
                word=word,
                is_valid=is_valid,
                stems=stems,
                suggestions=suggestions[:5],  # Limit suggestions
                dictionary_forms=dictionary_forms
            )
            
        except Exception as e:
            logger.error(f"Error analyzing word '{word}': {e}")
            return MorphAnalysis(
                word=word,
                is_valid=False,
                stems=[],
                suggestions=[],
                dictionary_forms=set()
            )
    
    def find_dictionary_form(self, word: str) -> Optional[str]:
        """Find the dictionary (base/lemma) form of a Russian word.
        
        Args:
            word: Russian word in any grammatical form
            
        Returns:
            Dictionary form of the word, or None if not found
        """
        analysis = self.analyze_word(word)
        
        # If word is valid and has stems, return the first stem
        if analysis.is_valid and analysis.stems:
            return analysis.stems[0]
        
        # If word is not valid but has dictionary forms from suggestions, return first one
        if analysis.dictionary_forms:
            return sorted(analysis.dictionary_forms)[0]  # Sort for consistency
        
        # If no stems found but we have suggestions, try the first suggestion
        if analysis.suggestions:
            suggestion_analysis = self.analyze_word(analysis.suggestions[0])
            if suggestion_analysis.stems:
                return suggestion_analysis.stems[0]
        
        return None
    
    def is_word_valid(self, word: str) -> bool:
        """Check if a word exists in the Russian dictionary.
        
        Args:
            word: Word to check
            
        Returns:
            True if word is valid, False otherwise
        """
        if not self.is_available():
            return False
            
        try:
            encoded_word = self._encode_for_hunspell(word)
            return self.hunspell_obj.spell(encoded_word)
        except Exception as e:
            logger.error(f"Error checking word validity for '{word}': {e}")
            return False
    
    def get_suggestions(self, word: str, limit: int = 5) -> List[str]:
        """Get spelling suggestions for a word.
        
        Args:
            word: Word to get suggestions for
            limit: Maximum number of suggestions to return
            
        Returns:
            List of suggested spellings
        """
        if not self.is_available():
            return []
            
        try:
            encoded_word = self._encode_for_hunspell(word)
            suggestions = self.hunspell_obj.suggest(encoded_word)
            if suggestions:
                decoded_suggestions = [self._decode_from_hunspell(suggestion) for suggestion in suggestions]
                return decoded_suggestions[:limit]
            return []
        except Exception as e:
            logger.error(f"Error getting suggestions for '{word}': {e}")
            return []


# Global instance for easy access
_global_analyzer = None

def get_hunspell_analyzer() -> RussianHunspellAnalyzer:
    """Get the global Hunspell analyzer instance."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = RussianHunspellAnalyzer()
    return _global_analyzer


def find_dictionary_form(word: str) -> Optional[str]:
    """Convenience function to find dictionary form using global analyzer.
    
    Args:
        word: Russian word in any form
        
    Returns:
        Dictionary form or None if not found
    """
    analyzer = get_hunspell_analyzer()
    return analyzer.find_dictionary_form(word)


def is_word_valid(word: str) -> bool:
    """Convenience function to check word validity using global analyzer.
    
    Args:
        word: Word to check
        
    Returns:
        True if word is valid
    """
    analyzer = get_hunspell_analyzer()
    return analyzer.is_word_valid(word)
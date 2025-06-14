"""Base PyMorphy2 analyzer with core functionality."""

import logging
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass

# Import compatibility patch first
from app.my_graph.utils.pymorphy2_compat import *

# Now import pymorphy2
import pymorphy2

logger = logging.getLogger(__name__)


@dataclass
class MorphologicalAnalysis:
    """Result of morphological analysis."""
    word: str
    normal_form: str
    pos: str
    variants: List[Dict[str, Any]]
    confidence: float


class PyMorphy2Analyzer:
    """Russian morphological analyzer using pymorphy2."""
    
    def __init__(self):
        try:
            self.morph = pymorphy2.MorphAnalyzer()
            self.available = True
            logger.info("PyMorphy2 analyzer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PyMorphy2: {e}")
            self.morph = None
            self.available = False
    
    def is_available(self) -> bool:
        """Check if analyzer is available for use."""
        return self.available and self.morph is not None
    
    def analyze_word(self, word: str) -> Optional[MorphologicalAnalysis]:
        """Analyze a Russian word using pymorphy2.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            MorphologicalAnalysis object or None if analysis fails
        """
        if not self.is_available():
            return None
        
        try:
            parsed = self.morph.parse(word)
            
            if not parsed:
                return None
            
            # Get the most likely parse (first one)
            primary_parse = parsed[0]
            
            # Create variants list
            variants = []
            for p in parsed:
                variant = {
                    'word': p.word,
                    'normal_form': p.normal_form,
                    'pos': str(p.tag.POS) if p.tag.POS else None,
                    'tag': str(p.tag),
                    'score': getattr(p, 'score', 0.0)
                }
                
                # Add grammatical properties
                if hasattr(p.tag, 'gender') and p.tag.gender:
                    variant['gender'] = str(p.tag.gender)
                if hasattr(p.tag, 'case') and p.tag.case:
                    variant['case'] = str(p.tag.case)
                if hasattr(p.tag, 'number') and p.tag.number:
                    variant['number'] = str(p.tag.number)
                if hasattr(p.tag, 'animacy') and p.tag.animacy:
                    variant['animacy'] = str(p.tag.animacy)
                if hasattr(p.tag, 'aspect') and p.tag.aspect:
                    variant['aspect'] = str(p.tag.aspect)
                if hasattr(p.tag, 'tense') and p.tag.tense:
                    variant['tense'] = str(p.tag.tense)
                if hasattr(p.tag, 'person') and p.tag.person:
                    variant['person'] = str(p.tag.person)
                
                variants.append(variant)
            
            return MorphologicalAnalysis(
                word=word,
                normal_form=primary_parse.normal_form,
                pos=str(primary_parse.tag.POS) if primary_parse.tag.POS else 'UNKN',
                variants=variants,
                confidence=getattr(primary_parse, 'score', 1.0)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing word '{word}': {e}")
            return None
    
    def get_word_forms(self, normal_form: str, target_grammemes: Set[str]) -> List[str]:
        """Get word forms with specific grammatical properties.
        
        Args:
            normal_form: Dictionary form of the word
            target_grammemes: Set of grammatical properties to match
            
        Returns:
            List of matching word forms
        """
        if not self.is_available():
            return []
        
        try:
            parsed = self.morph.parse(normal_form)
            if not parsed:
                return []
            
            # Get the primary parse
            primary_parse = parsed[0]
            
            # Generate forms with target grammemes
            forms = []
            try:
                inflected = primary_parse.inflect(target_grammemes)
                if inflected:
                    forms.append(inflected.word)
            except Exception:
                # If inflection fails, try to find existing forms
                pass
            
            return forms
            
        except Exception as e:
            logger.error(f"Error getting word forms for '{normal_form}': {e}")
            return []


# Global analyzer instance
_global_analyzer = None

def get_pymorphy2_analyzer() -> PyMorphy2Analyzer:
    """Get the global PyMorphy2 analyzer instance."""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = PyMorphy2Analyzer()
    return _global_analyzer
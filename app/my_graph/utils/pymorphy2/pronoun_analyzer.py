"""Pronoun analyzer using pymorphy2."""

import logging
from typing import Dict, Optional
from app.grammar.russian import Pronoun
from .base_analyzer import PyMorphy2Analyzer

logger = logging.getLogger(__name__)


class PyMorphy2PronounAnalyzer:
    """Pronoun analyzer using pymorphy2."""
    
    def __init__(self):
        self.analyzer = PyMorphy2Analyzer()
    
    def generate_pronoun_declension(self, normal_form: str, pronoun_type: str) -> Dict[str, Dict[str, str]]:
        """Generate pronoun declension based on pronoun type.
        
        Args:
            normal_form: Dictionary form of the pronoun
            pronoun_type: Type of pronoun (personal, demonstrative, possessive, etc.)
            
        Returns:
            Dict with appropriate declension patterns
        """
        if not self.analyzer.is_available():
            return {}
        
        # Russian cases mapping
        cases = {
            'nomn': 'nom',  # nominative
            'gent': 'gen',  # genitive  
            'datv': 'dat',  # dative
            'accs': 'acc',  # accusative
            'ablt': 'ins',  # instrumental
            'loct': 'pre'   # prepositional
        }
        
        result = {}
        
        try:
            # Personal pronouns (я, ты, он, она, оно, мы, вы, они) - noun-like
            personal_pronouns = ['я', 'ты', 'он', 'она', 'оно', 'мы', 'вы', 'они']
            
            if normal_form in personal_pronouns:
                # For personal pronouns, generate simple case forms
                declension = {}
                for pymorphy_case, our_case in cases.items():
                    grammemes = {pymorphy_case}
                    forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    declension[our_case] = forms[0] if forms else ""
                
                # Determine if singular or plural
                if normal_form in ['я', 'ты', 'он', 'она', 'оно']:
                    result['singular'] = declension
                else:
                    result['plural'] = declension
            
            else:
                # Adjective-like pronouns (этот, мой, наш, etc.) - gender-specific
                masculine = {}
                feminine = {}
                neuter = {}
                plural = {}
                
                # Generate masculine forms
                for pymorphy_case, our_case in cases.items():
                    grammemes = {pymorphy_case, 'sing', 'masc'}
                    forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    masculine[our_case] = forms[0] if forms else ""
                
                # Generate feminine forms
                for pymorphy_case, our_case in cases.items():
                    grammemes = {pymorphy_case, 'sing', 'femn'}
                    forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    feminine[our_case] = forms[0] if forms else ""
                
                # Generate neuter forms
                for pymorphy_case, our_case in cases.items():
                    grammemes = {pymorphy_case, 'sing', 'neut'}
                    forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    neuter[our_case] = forms[0] if forms else ""
                
                # Generate plural forms
                for pymorphy_case, our_case in cases.items():
                    grammemes = {pymorphy_case, 'plur'}
                    forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    plural[our_case] = forms[0] if forms else ""
                
                result['masculine'] = masculine
                result['feminine'] = feminine
                result['neuter'] = neuter
                result['plural_adjective_like'] = plural
                
        except Exception as e:
            logger.error(f"Error generating pronoun declension for '{normal_form}': {e}")
        
        return result
    
    def analyze_pronoun(self, word: str) -> Optional[Pronoun]:
        """Analyze a Russian pronoun and create a Pronoun object.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            Pronoun object if successful, None otherwise
        """
        if not self.analyzer.is_available():
            logger.warning("PyMorphy2 analyzer not available")
            return None
        
        # Get morphological analysis
        analysis = self.analyzer.analyze_word(word)
        
        if not analysis:
            logger.info(f"No morphological analysis found for '{word}'")
            return None
        
        # Find pronoun variants
        pronoun_variants = [v for v in analysis.variants if v.get('pos') == 'NPRO']
        
        if not pronoun_variants:
            logger.info(f"Word '{word}' is not a pronoun")
            return None
        
        # Use the first (most likely) pronoun variant
        pronoun_variant = pronoun_variants[0]
        
        # Extract properties
        normal_form = pronoun_variant['normal_form']
        
        # Determine pronoun type for declension pattern
        pronoun_type = "personal"  # Default assumption
        
        # Generate declension
        declension = self.generate_pronoun_declension(normal_form, pronoun_type)
        
        try:
            pronoun = Pronoun(
                dictionary_form=normal_form,
                english_translation="",  # TODO: Add translation lookup
                
                # Noun-like declensions (for personal pronouns)
                singular=declension.get('singular'),
                plural=declension.get('plural'),
                
                # Adjective-like declensions (for demonstrative/possessive pronouns)
                masculine=declension.get('masculine'),
                feminine=declension.get('feminine'),
                neuter=declension.get('neuter'),
                plural_adjective_like=declension.get('plural_adjective_like'),
                
                # Special notes
                notes=None
            )
            
            logger.info(f"Successfully analyzed pronoun '{word}' -> '{normal_form}'")
            return pronoun
            
        except Exception as e:
            logger.error(f"Error creating Pronoun object for '{word}': {e}")
            return None
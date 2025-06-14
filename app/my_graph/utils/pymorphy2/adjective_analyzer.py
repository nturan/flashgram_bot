"""Adjective analyzer using pymorphy2."""

import logging
from typing import Dict, Optional
from app.grammar.russian import Adjective
from .base_analyzer import PyMorphy2Analyzer

logger = logging.getLogger(__name__)


class PyMorphy2AdjectiveAnalyzer:
    """Adjective analyzer using pymorphy2."""
    
    def __init__(self):
        self.analyzer = PyMorphy2Analyzer()
    
    def generate_adjective_declension(self, normal_form: str) -> Dict[str, Dict[str, str]]:
        """Generate full adjective declension table for all genders.
        
        Args:
            normal_form: Dictionary form of the adjective
            
        Returns:
            Dict with masculine, feminine, neuter, and plural declensions
        """
        if not self.analyzer.is_available():
            return {"masculine": {}, "feminine": {}, "neuter": {}, "plural": {}}
        
        # Russian cases mapping
        cases = {
            'nomn': 'nom',  # nominative
            'gent': 'gen',  # genitive  
            'datv': 'dat',  # dative
            'accs': 'acc',  # accusative
            'ablt': 'ins',  # instrumental
            'loct': 'pre'   # prepositional
        }
        
        masculine = {}
        feminine = {}
        neuter = {}
        plural = {}
        
        try:
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
                
        except Exception as e:
            logger.error(f"Error generating adjective declension for '{normal_form}': {e}")
        
        return {
            "masculine": masculine,
            "feminine": feminine,
            "neuter": neuter,
            "plural": plural
        }
    
    def generate_short_forms(self, normal_form: str) -> Dict[str, str]:
        """Generate short forms of the adjective.
        
        Args:
            normal_form: Dictionary form of the adjective
            
        Returns:
            Dict with short forms for each gender and plural
        """
        if not self.analyzer.is_available():
            return {}
        
        short_forms = {}
        
        try:
            # Generate short forms
            short_grammemes = [
                ('ADJS', 'masc', 'sing'),  # short masculine
                ('ADJS', 'femn', 'sing'),  # short feminine
                ('ADJS', 'neut', 'sing'),  # short neuter
                ('ADJS', 'plur'),          # short plural
            ]
            
            for grammemes_tuple in short_grammemes:
                grammemes = set(grammemes_tuple)
                forms = self.analyzer.get_word_forms(normal_form, grammemes)
                if forms:
                    if 'masc' in grammemes:
                        short_forms['masculine'] = forms[0]
                    elif 'femn' in grammemes:
                        short_forms['feminine'] = forms[0]
                    elif 'neut' in grammemes:
                        short_forms['neuter'] = forms[0]
                    elif 'plur' in grammemes:
                        short_forms['plural'] = forms[0]
                        
        except Exception as e:
            logger.error(f"Error generating short forms for '{normal_form}': {e}")
        
        return short_forms
    
    def analyze_adjective(self, word: str) -> Optional[Adjective]:
        """Analyze a Russian adjective and create an Adjective object.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            Adjective object if successful, None otherwise
        """
        if not self.analyzer.is_available():
            logger.warning("PyMorphy2 analyzer not available")
            return None
        
        # Get morphological analysis
        analysis = self.analyzer.analyze_word(word)
        
        if not analysis:
            logger.info(f"No morphological analysis found for '{word}'")
            return None
        
        # Find adjective variants
        adjective_variants = [v for v in analysis.variants if v.get('pos') in ['ADJF', 'ADJS']]
        
        if not adjective_variants:
            logger.info(f"Word '{word}' is not an adjective")
            return None
        
        # Use the first (most likely) adjective variant
        adjective_variant = adjective_variants[0]
        
        # Extract properties
        normal_form = adjective_variant['normal_form']
        
        # Generate full declension
        declension = self.generate_adjective_declension(normal_form)
        
        # Generate short forms
        short_forms = self.generate_short_forms(normal_form)
        
        try:
            adjective = Adjective(
                dictionary_form=normal_form,
                english_translation="",  # TODO: Add translation lookup
                
                # Full declensions
                masculine=declension['masculine'],
                feminine=declension['feminine'],
                neuter=declension['neuter'],
                plural=declension['plural'],
                
                # Short forms
                short_form_masculine=short_forms.get('masculine', ''),
                short_form_feminine=short_forms.get('feminine', ''),
                short_form_neuter=short_forms.get('neuter', ''),
                short_form_plural=short_forms.get('plural', ''),
                
                # TODO: Add comparative and superlative forms
                comparative='',
                superlative=''
            )
            
            logger.info(f"Successfully analyzed adjective '{word}' -> '{normal_form}'")
            return adjective
            
        except Exception as e:
            logger.error(f"Error creating Adjective object for '{word}': {e}")
            return None
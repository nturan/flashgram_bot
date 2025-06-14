"""Noun analyzer using pymorphy2."""

import logging
from typing import Dict, Optional
from app.grammar.russian import Noun
from .base_analyzer import PyMorphy2Analyzer

logger = logging.getLogger(__name__)


class PyMorphy2NounAnalyzer:
    """Noun analyzer using pymorphy2."""
    
    def __init__(self):
        self.analyzer = PyMorphy2Analyzer()
    
    def generate_noun_declension(self, normal_form: str, gender: str, animacy: str) -> Dict[str, Dict[str, str]]:
        """Generate full noun declension table.
        
        Args:
            normal_form: Dictionary form of the noun
            gender: Gender (masc, femn, neut)
            animacy: Animacy (anim, inan)
            
        Returns:
            Dict with singular and plural declensions
        """
        if not self.analyzer.is_available():
            return {"singular": {}, "plural": {}}
        
        # Russian cases mapping
        cases = {
            'nomn': 'nom',  # nominative
            'gent': 'gen',  # genitive  
            'datv': 'dat',  # dative
            'accs': 'acc',  # accusative
            'ablt': 'ins',  # instrumental
            'loct': 'pre'   # prepositional
        }
        
        singular = {}
        plural = {}
        
        try:
            # Generate singular forms
            for pymorphy_case, our_case in cases.items():
                grammemes = {pymorphy_case, 'sing', gender, animacy}
                forms = self.analyzer.get_word_forms(normal_form, grammemes)
                singular[our_case] = forms[0] if forms else ""
            
            # Generate plural forms
            for pymorphy_case, our_case in cases.items():
                grammemes = {pymorphy_case, 'plur', gender, animacy}
                forms = self.analyzer.get_word_forms(normal_form, grammemes)
                plural[our_case] = forms[0] if forms else ""
                
        except Exception as e:
            logger.error(f"Error generating declension for '{normal_form}': {e}")
        
        return {
            "singular": singular,
            "plural": plural
        }
    
    def analyze_noun(self, word: str) -> Optional[Noun]:
        """Analyze a Russian noun and create a Noun object.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            Noun object if successful, None otherwise
        """
        if not self.analyzer.is_available():
            logger.warning("PyMorphy2 analyzer not available")
            return None
        
        # Get morphological analysis
        analysis = self.analyzer.analyze_word(word)
        
        if not analysis:
            logger.info(f"No morphological analysis found for '{word}'")
            return None
        
        # Find noun variants
        noun_variants = [v for v in analysis.variants if v.get('pos') == 'NOUN']
        
        if not noun_variants:
            logger.info(f"Word '{word}' is not a noun")
            return None
        
        # Use the first (most likely) noun variant
        noun_variant = noun_variants[0]
        
        # Extract properties
        normal_form = noun_variant['normal_form']
        gender_map = {'masc': 'masculine', 'femn': 'feminine', 'neut': 'neuter'}
        gender = gender_map.get(noun_variant.get('gender', 'masc'), 'masculine')
        animacy = noun_variant.get('animacy', 'inan') == 'anim'
        
        # Generate full declension
        pymorphy_gender = noun_variant.get('gender', 'masc')
        pymorphy_animacy = noun_variant.get('animacy', 'inan')
        
        declension = self.generate_noun_declension(normal_form, pymorphy_gender, pymorphy_animacy)
        
        try:
            noun = Noun(
                dictionary_form=normal_form,
                gender=gender,
                animacy=animacy,
                singular=declension['singular'],
                plural=declension['plural'],
                english_translation=""  # TODO: Add translation lookup
            )
            
            logger.info(f"Successfully analyzed noun '{word}' -> '{normal_form}' ({gender}, animate={animacy})")
            return noun
            
        except Exception as e:
            logger.error(f"Error creating Noun object for '{word}': {e}")
            return None
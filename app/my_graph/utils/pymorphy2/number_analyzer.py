"""Number analyzer using pymorphy2."""

import logging
from typing import Dict, Optional
from app.grammar.russian import Number
from .base_analyzer import PyMorphy2Analyzer

logger = logging.getLogger(__name__)


class PyMorphy2NumberAnalyzer:
    """Number analyzer using pymorphy2."""
    
    def __init__(self):
        self.analyzer = PyMorphy2Analyzer()
    
    def generate_number_declension(self, normal_form: str) -> Dict[str, Dict[str, str]]:
        """Generate number declension based on number type.
        
        Args:
            normal_form: Dictionary form of the number
            
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
            # "One" type numbers (один, одна, одно) - adjective-like declension
            if normal_form in ['один', 'одна', 'одно']:
                masculine = {}
                feminine = {}
                neuter = {}
                
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
                
                result['masculine'] = masculine
                result['feminine'] = feminine
                result['neuter'] = neuter
            
            else:
                # Other numbers - simpler declension
                singular = {}
                for pymorphy_case, our_case in cases.items():
                    grammemes = {pymorphy_case}
                    forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    singular[our_case] = forms[0] if forms else ""
                
                result['singular'] = singular
                
        except Exception as e:
            logger.error(f"Error generating number declension for '{normal_form}': {e}")
        
        return result
    
    def get_noun_agreement_pattern(self, normal_form: str) -> Optional[Dict[str, str]]:
        """Determine what case nouns take when used with this number.
        
        Args:
            normal_form: Dictionary form of the number
            
        Returns:
            Dict showing noun case agreement patterns
        """
        # Basic agreement patterns for Russian numbers
        if normal_form == 'один':
            # один + nominative
            return {
                'nom': 'nom',  # один дом
                'gen': 'gen',  # одного дома
                'dat': 'dat',  # одному дому
                'acc': 'acc',  # один дом / одного человека
                'ins': 'ins',  # одним домом
                'pre': 'pre'   # об одном доме
            }
        elif normal_form in ['два', 'три', 'четыре']:
            # 2-4 + genitive singular in nominative/accusative
            return {
                'nom': 'gen_sing',  # два дома
                'gen': 'gen_plur',  # двух домов
                'dat': 'dat_plur',  # двум домам
                'acc': 'gen_sing',  # два дома / двух людей
                'ins': 'ins_plur',  # двумя домами
                'pre': 'pre_plur'   # о двух домах
            }
        elif normal_form in ['пять', 'шесть', 'семь', 'восемь', 'девять', 'десять']:
            # 5+ + genitive plural
            return {
                'nom': 'gen_plur',  # пять домов
                'gen': 'gen_plur',  # пяти домов
                'dat': 'dat_plur',  # пяти домам
                'acc': 'gen_plur',  # пять домов
                'ins': 'ins_plur',  # пятью домами
                'pre': 'pre_plur'   # о пяти домах
            }
        
        return None
    
    def analyze_number(self, word: str) -> Optional[Number]:
        """Analyze a Russian number and create a Number object.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            Number object if successful, None otherwise
        """
        if not self.analyzer.is_available():
            logger.warning("PyMorphy2 analyzer not available")
            return None
        
        # Get morphological analysis
        analysis = self.analyzer.analyze_word(word)
        
        if not analysis:
            logger.info(f"No morphological analysis found for '{word}'")
            return None
        
        # Find number variants (including adjective-like numbers)
        number_variants = [v for v in analysis.variants if v.get('pos') in ['NUMR', 'ADJF']]
        
        # For adjective-like numbers, filter to only actual numbers
        if analysis.normal_form in ['один', 'одна', 'одно', 'два', 'три', 'четыре', 'пять', 'шесть', 
                                   'семь', 'восемь', 'девять', 'десять', 'одиннадцать', 'двенадцать',
                                   'тринадцать', 'четырнадцать', 'пятнадцать', 'шестнадцать',
                                   'семнадцать', 'восемнадцать', 'девятнадцать', 'двадцать']:
            # Accept adjective-tagged numbers for known number words
            pass
        else:
            # For other words, only accept NUMR tagged ones
            number_variants = [v for v in number_variants if v.get('pos') == 'NUMR']
        
        if not number_variants:
            logger.info(f"Word '{word}' is not a number")
            return None
        
        # Use the first (most likely) number variant
        number_variant = number_variants[0]
        
        # Extract properties
        normal_form = number_variant['normal_form']
        
        # Generate declension
        declension = self.generate_number_declension(normal_form)
        
        # Get noun agreement pattern
        noun_agreement = self.get_noun_agreement_pattern(normal_form)
        
        try:
            number = Number(
                dictionary_form=normal_form,
                english_translation="",  # TODO: Add translation lookup
                
                # Gender-specific forms (for "one" type)
                masculine=declension.get('masculine'),
                feminine=declension.get('feminine'),
                neuter=declension.get('neuter'),
                
                # Simple forms (for other numbers)
                singular=declension.get('singular'),
                plural=declension.get('plural'),
                
                # Compound forms for complex numbers
                compound_forms=None,  # TODO: Handle compound numbers
                
                # Agreement patterns
                noun_agreement=noun_agreement
            )
            
            logger.info(f"Successfully analyzed number '{word}' -> '{normal_form}'")
            return number
            
        except Exception as e:
            logger.error(f"Error creating Number object for '{word}': {e}")
            return None
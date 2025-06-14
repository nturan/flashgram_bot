"""Verb analyzer using pymorphy2."""

import logging
from typing import Dict, Optional
from app.grammar.russian import Verb
from .base_analyzer import PyMorphy2Analyzer

logger = logging.getLogger(__name__)


class PyMorphy2VerbAnalyzer:
    """Verb analyzer using pymorphy2."""
    
    def __init__(self):
        self.analyzer = PyMorphy2Analyzer()
    
    def generate_verb_conjugation(self, normal_form: str, aspect: str) -> Dict[str, str]:
        """Generate verb conjugation patterns."""
        if not self.analyzer.is_available():
            return {}
        
        forms = {}
        
        try:
            parsed = self.analyzer.morph.parse(normal_form)
            if not parsed:
                return {}
            
            # Get the primary parse
            primary_parse = parsed[0]
            
            # Generate present tense forms (only for imperfective verbs)
            if aspect == "imperfective":
                present_grammemes = [
                    ('1per', 'sing', 'pres'),  # я
                    ('2per', 'sing', 'pres'),  # ты  
                    ('3per', 'sing', 'pres'),  # он/она/оно
                    ('1per', 'plur', 'pres'),  # мы
                    ('2per', 'plur', 'pres'),  # вы
                    ('3per', 'plur', 'pres'),  # они
                ]
                
                for person, number, tense in present_grammemes:
                    grammemes = {person, number, tense}
                    inflected_forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    if inflected_forms:
                        key = f"present_{person}_{number}"
                        forms[key] = inflected_forms[0]
            
            # Generate past tense forms
            past_grammemes = [
                ('past', 'masc', 'sing'),  # он
                ('past', 'femn', 'sing'),  # она
                ('past', 'neut', 'sing'),  # оно
                ('past', 'plur'),          # они
            ]
            
            for grammemes_tuple in past_grammemes:
                grammemes = set(grammemes_tuple)
                inflected_forms = self.analyzer.get_word_forms(normal_form, grammemes)
                if inflected_forms:
                    if 'masc' in grammemes:
                        forms['past_masculine'] = inflected_forms[0]
                    elif 'femn' in grammemes:
                        forms['past_feminine'] = inflected_forms[0]
                    elif 'neut' in grammemes:
                        forms['past_neuter'] = inflected_forms[0]
                    elif 'plur' in grammemes:
                        forms['past_plural'] = inflected_forms[0]
            
            # Generate future tense forms (for perfective verbs)
            if aspect == "perfective":
                future_grammemes = [
                    ('1per', 'sing', 'futr'),  # я
                    ('2per', 'sing', 'futr'),  # ты  
                    ('3per', 'sing', 'futr'),  # он/она/оно
                    ('1per', 'plur', 'futr'),  # мы
                    ('2per', 'plur', 'futr'),  # вы
                    ('3per', 'plur', 'futr'),  # они
                ]
                
                for person, number, tense in future_grammemes:
                    grammemes = {person, number, tense}
                    inflected_forms = self.analyzer.get_word_forms(normal_form, grammemes)
                    if inflected_forms:
                        key = f"future_{person}_{number}"
                        forms[key] = inflected_forms[0]
            
            # Generate imperative forms
            imperative_grammemes = [
                ('impr', 'sing'),  # singular imperative
                ('impr', 'plur'),  # plural imperative
            ]
            
            for mood, number in imperative_grammemes:
                grammemes = {mood, number}
                inflected_forms = self.analyzer.get_word_forms(normal_form, grammemes)
                if inflected_forms:
                    key = f"imperative_{number}"
                    forms[key] = inflected_forms[0]
                    
        except Exception as e:
            logger.error(f"Error generating verb forms for '{normal_form}': {e}")
        
        return forms
    
    def analyze_verb(self, word: str) -> Optional[Verb]:
        """Analyze a Russian verb and create a Verb object.
        
        Args:
            word: Russian word to analyze
            
        Returns:
            Verb object if successful, None otherwise
        """
        if not self.analyzer.is_available():
            logger.warning("PyMorphy2 analyzer not available")
            return None
        
        # Get morphological analysis
        analysis = self.analyzer.analyze_word(word)
        
        if not analysis:
            logger.info(f"No morphological analysis found for '{word}'")
            return None
        
        # Find verb variants
        verb_variants = [v for v in analysis.variants if v.get('pos') in ['VERB', 'INFN']]
        
        if not verb_variants:
            logger.info(f"Word '{word}' is not a verb")
            return None
        
        # Use the first (most likely) verb variant
        verb_variant = verb_variants[0]
        
        # Extract properties
        normal_form = verb_variant['normal_form']
        
        # Determine aspect
        aspect_map = {'perf': 'perfective', 'impf': 'imperfective'}
        aspect = aspect_map.get(verb_variant.get('aspect', 'impf'), 'imperfective')
        
        # Generate conjugation
        conjugation = self.generate_verb_conjugation(normal_form, aspect)
        
        try:
            verb = Verb(
                dictionary_form=normal_form,
                english_translation="",  # TODO: Add translation lookup
                aspect=aspect,
                aspect_pair=None,  # TODO: Could be enhanced to find aspectual pairs
                
                # Present tense (only for imperfective)
                present_first_singular=conjugation.get('present_1per_sing'),
                present_second_singular=conjugation.get('present_2per_sing'),
                present_third_singular=conjugation.get('present_3per_sing'),
                present_first_plural=conjugation.get('present_1per_plur'),
                present_second_plural=conjugation.get('present_2per_plur'),
                present_third_plural=conjugation.get('present_3per_plur'),
                
                # Past tense
                past_masculine=conjugation.get('past_masculine', ''),
                past_feminine=conjugation.get('past_feminine', ''),
                past_neuter=conjugation.get('past_neuter', ''),
                past_plural=conjugation.get('past_plural', ''),
                
                # Future tense (for perfective verbs)
                future_first_singular=conjugation.get('future_1per_sing'),
                future_second_singular=conjugation.get('future_2per_sing'),
                future_third_singular=conjugation.get('future_3per_sing'),
                future_first_plural=conjugation.get('future_1per_plur'),
                future_second_plural=conjugation.get('future_2per_plur'),
                future_third_plural=conjugation.get('future_3per_plur'),
                
                # Imperative
                imperative_singular=conjugation.get('imperative_sing'),
                imperative_plural=conjugation.get('imperative_plur'),
            )
            
            logger.info(f"Successfully analyzed verb '{word}' -> '{normal_form}' ({aspect})")
            return verb
            
        except Exception as e:
            logger.error(f"Error creating Verb object for '{word}': {e}")
            return None
"""Grammar form analysis utilities."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class FormAnalyzer:
    """Analyzes grammatical forms and provides descriptions."""
    
    def get_form_description(self, word_type: str, case: str, number: str = None, gender: str = None) -> str:
        """Get a human-readable description of a grammatical form."""
        try:
            if word_type == "noun":
                return self._get_noun_form_description(case, number)
            elif word_type == "adjective":
                return self._get_adjective_form_description(case, number, gender)
            elif word_type == "verb":
                return self._get_verb_form_description(case)  # case is actually tense/person for verbs
            else:
                return f"{case} form"
        except Exception as e:
            logger.error(f"Error getting form description: {e}")
            return "grammatical form"
    
    def _get_noun_form_description(self, case: str, number: str) -> str:
        """Get description for noun forms."""
        case_names = {
            'nom': 'nominative',
            'gen': 'genitive', 
            'dat': 'dative',
            'acc': 'accusative',
            'ins': 'instrumental',
            'pre': 'prepositional'
        }
        
        case_name = case_names.get(case.lower(), case)
        number_name = number if number else ""
        
        return f"{case_name} {number_name}".strip()
    
    def _get_adjective_form_description(self, case: str, number: str, gender: str) -> str:
        """Get description for adjective forms."""
        case_names = {
            'nom': 'nominative',
            'gen': 'genitive',
            'dat': 'dative', 
            'acc': 'accusative',
            'ins': 'instrumental',
            'pre': 'prepositional'
        }
        
        case_name = case_names.get(case.lower(), case)
        
        if number == "plural":
            return f"{case_name} plural"
        elif gender:
            return f"{case_name} {gender}"
        else:
            return f"{case_name} form"
    
    def _get_verb_form_description(self, form_key: str) -> str:
        """Get description for verb forms."""
        form_descriptions = {
            'present_first_singular': 'present tense, 1st person singular (я)',
            'present_second_singular': 'present tense, 2nd person singular (ты)',
            'present_third_singular': 'present tense, 3rd person singular (он/она/оно)',
            'present_first_plural': 'present tense, 1st person plural (мы)',
            'present_second_plural': 'present tense, 2nd person plural (вы)',
            'present_third_plural': 'present tense, 3rd person plural (они)',
            'past_masculine': 'past tense, masculine (он)',
            'past_feminine': 'past tense, feminine (она)',
            'past_neuter': 'past tense, neuter (оно)',
            'past_plural': 'past tense, plural (они)',
            'future_first_singular': 'future tense, 1st person singular (я)',
            'future_second_singular': 'future tense, 2nd person singular (ты)',
            'future_third_singular': 'future tense, 3rd person singular (он/она/оно)',
            'future_first_plural': 'future tense, 1st person plural (мы)',
            'future_second_plural': 'future tense, 2nd person plural (вы)',
            'future_third_plural': 'future tense, 3rd person plural (они)',
            'imperative_singular': 'imperative, singular',
            'imperative_plural': 'imperative, plural'
        }
        
        return form_descriptions.get(form_key, form_key)
    
    def extract_metadata_from_grammar_obj(self, grammar_obj: Any, word_type: str) -> Dict[str, Any]:
        """Extract metadata from a grammar object for flashcard creation."""
        try:
            metadata = {
                "word_type": word_type,
                "dictionary_form": grammar_obj.dictionary_form
            }
            
            if word_type == "noun":
                metadata.update({
                    "gender": grammar_obj.gender,
                    "animacy": grammar_obj.animacy
                })
            elif word_type == "adjective":
                # Add any adjective-specific metadata
                pass
            elif word_type == "verb":
                metadata.update({
                    "aspect": grammar_obj.aspect,
                    "conjugation": grammar_obj.conjugation
                })
                if hasattr(grammar_obj, 'aspect_pair') and grammar_obj.aspect_pair:
                    metadata["aspect_pair"] = grammar_obj.aspect_pair
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {"word_type": word_type}
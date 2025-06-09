"""LLM-powered sentence generation for flashcards."""

import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.config import settings
from pydantic import SecretStr
from .text_processor import TextProcessor

logger = logging.getLogger(__name__)


class LLMSentenceGenerator:
    """Generates example sentences using LLM for specific grammatical forms."""
    
    def __init__(self):
        self.llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
        self.text_processor = TextProcessor()
    
    def generate_example_sentence(self, word: str, form: str, case_or_form_description: str, word_type: str) -> str:
        """Generate an example sentence using the LLM for a specific grammatical form."""
        try:
            # Generate verification question based on word type and form
            verification_guidance = self._get_verification_guidance(case_or_form_description, word_type)
            
            prompt = f"""Generate a simple, natural Russian sentence that uses the word "{form}" ({case_or_form_description} form of "{word}").

CRITICAL VERIFICATION: {verification_guidance}

The word "{form}" must be used in the exact grammatical form specified: {case_or_form_description}.
Before generating your sentence, mentally verify that the word "{form}" serves the correct grammatical function in your sentence.

Requirements:
- The sentence should be 6-12 words long
- Use everyday, conversational Russian  
- The word "{form}" must be used in the exact grammatical context specified
- The context should make the grammatical form unambiguous
- Focus on common, practical usage
- Avoid special punctuation (no quotes, parentheses, asterisks, underscores)
- Use only basic punctuation: periods, commas, exclamation marks, question marks
- Return ONLY the Russian sentence, nothing else

Example format: "Я читаю интересную книгу в библиотеке."""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            sentence = response.content.strip()
            
            # Clean the sentence of problematic characters
            sentence = self.text_processor.clean_sentence_for_telegram(sentence)
            
            # Basic validation - ensure the target form appears in the sentence
            if form.lower() in sentence.lower():
                return sentence
            else:
                # Fallback if LLM didn't include the form
                return f"В этом предложении используется слово {form}."
                
        except Exception as e:
            logger.error(f"Error generating example sentence: {e}")
            # Fallback sentence
            return f"Пример использования: {form}."
    
    def generate_contextual_sentence(self, word: str, form: str, grammatical_key: str, hint: str) -> str:
        """Generate a contextual sentence with a specific hint."""
        try:
            prompt = f"""Generate a simple, natural Russian sentence that uses the word "{form}" ({grammatical_key} form of "{word}") in the context of {hint}.

Requirements:
- The sentence should be 6-12 words long
- Use everyday, conversational Russian
- The context should relate to: {hint}
- Focus on common, practical usage
- Avoid special punctuation (no quotes, parentheses, asterisks, underscores)
- Use only basic punctuation: periods, commas, exclamation marks, question marks
- Return ONLY the Russian sentence, nothing else

Example format: "Я читаю интересную книгу в библиотеке."""
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            hint_sentence = response.content.strip()
            hint_sentence = self.text_processor.clean_sentence_for_telegram(hint_sentence)
            
            # Use the hint-based sentence if it contains the target form
            if form.lower() in hint_sentence.lower():
                return hint_sentence
            else:
                # Fallback to default generation
                return self.generate_example_sentence(word, form, grammatical_key, "word")
                
        except Exception as e:
            logger.warning(f"LLM hint generation failed: {e}, using default generation")
            return self.generate_example_sentence(word, form, grammatical_key, "word")
    
    def _get_verification_guidance(self, case_or_form_description: str, word_type: str) -> str:
        """Generate verification guidance based on word type and grammatical form."""
        description_lower = case_or_form_description.lower()
        
        # Handle noun cases
        if word_type == "noun" or "case" in description_lower:
            if "nominative" in description_lower or "nom" in description_lower:
                return "Ask 'Кто? Что?' - the word should answer 'who?' or 'what?' as the subject."
            elif "genitive" in description_lower or "gen" in description_lower:
                return "Ask 'Кого? Чего?' - the word should answer 'of whom?' or 'of what?' (possession, absence, after numbers 2-4)."
            elif "dative" in description_lower or "dat" in description_lower:
                return "Ask 'Кому? Чему?' - the word should answer 'to whom?' or 'to what?' (indirect object)."
            elif "accusative" in description_lower or "acc" in description_lower:
                return "Ask 'Кого? Что?' - the word should answer 'whom?' or 'what?' as the direct object."
            elif "instrumental" in description_lower or "ins" in description_lower:
                return "Ask 'Кем? Чем?' - the word should answer 'by whom?' or 'with what?' (means, accompaniment)."
            elif "prepositional" in description_lower or "pre" in description_lower:
                return "Ask 'О ком? О чём? Где?' - the word should answer 'about whom/what?' or 'where?' (location, topic)."
        
        # Handle verb forms
        elif word_type == "verb":
            if "present" in description_lower:
                if "1st person singular" in description_lower or "я" in description_lower:
                    return "Verify: Can you substitute 'я' (I) as the subject performing this action right now?"
                elif "2nd person singular" in description_lower or "ты" in description_lower:
                    return "Verify: Can you substitute 'ты' (you) as the subject performing this action right now?"
                elif "3rd person singular" in description_lower or "он/она/оно" in description_lower:
                    return "Verify: Can you substitute 'он/она/оно' (he/she/it) as the subject performing this action right now?"
                elif "1st person plural" in description_lower or "мы" in description_lower:
                    return "Verify: Can you substitute 'мы' (we) as the subject performing this action right now?"
                elif "2nd person plural" in description_lower or "вы" in description_lower:
                    return "Verify: Can you substitute 'вы' (you plural/formal) as the subject performing this action right now?"
                elif "3rd person plural" in description_lower or "они" in description_lower:
                    return "Verify: Can you substitute 'они' (they) as the subject performing this action right now?"
                else:
                    return "Verify: Is this action happening right now (present tense)?"
            elif "past" in description_lower:
                if "masculine" in description_lower:
                    return "Verify: Can you substitute 'он' (he) as the subject who performed this action in the past?"
                elif "feminine" in description_lower:
                    return "Verify: Can you substitute 'она' (she) as the subject who performed this action in the past?"
                elif "neuter" in description_lower:
                    return "Verify: Can you substitute 'оно' (it) as the subject who performed this action in the past?"
                elif "plural" in description_lower:
                    return "Verify: Can you substitute 'они' (they) as the subjects who performed this action in the past?"
                else:
                    return "Verify: Did this action happen in the past?"
            elif "future" in description_lower:
                return "Verify: Will this action happen in the future?"
            elif "imperative" in description_lower:
                return "Verify: Is this a command or request? Can you imagine saying 'Please...' before it?"
        
        # Handle adjective forms
        elif word_type == "adjective":
            if "masculine" in description_lower and "nominative" in description_lower:
                return "Verify: Does this adjective describe a masculine noun in nominative case? Ask 'Какой?' (what kind of - masculine)."
            elif "feminine" in description_lower and "nominative" in description_lower:
                return "Verify: Does this adjective describe a feminine noun in nominative case? Ask 'Какая?' (what kind of - feminine)."
            elif "neuter" in description_lower and "nominative" in description_lower:
                return "Verify: Does this adjective describe a neuter noun in nominative case? Ask 'Какое?' (what kind of - neuter)."
            elif "plural" in description_lower and "nominative" in description_lower:
                return "Verify: Does this adjective describe plural nouns in nominative case? Ask 'Какие?' (what kind of - plural)."
            else:
                return "Verify: Does this adjective agree in gender, number, and case with the noun it describes?"
        
        # Handle pronoun forms
        elif word_type == "pronoun":
            return "Verify: Does this pronoun function correctly in its grammatical role (subject, object, possessive, etc.)?"
        
        # Handle number forms  
        elif word_type == "number":
            return "Verify: Does this number agree properly with the noun it modifies, and are they in the correct case relationship?"
        
        # Default guidance
        return f"Verify: Is '{case_or_form_description}' the correct grammatical function of this word in your sentence?"
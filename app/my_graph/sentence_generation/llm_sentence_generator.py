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
            prompt = f"""Generate a simple, natural Russian sentence that uses the word "{form}" ({case_or_form_description} form of "{word}").

Requirements:
- The sentence should be 6-12 words long
- Use everyday, conversational Russian
- The context should make the grammatical form clear
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
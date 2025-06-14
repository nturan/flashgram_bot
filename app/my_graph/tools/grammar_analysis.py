"""Grammar analysis tool implementation."""

import logging
from typing import Dict, Any

from pydantic import SecretStr
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from app.config import settings
from app.my_graph.utils.hunspell_analyzer import get_hunspell_analyzer, find_dictionary_form
from app.my_graph.prompts import (
    initial_classification_prompt,
    get_noun_grammar_prompt,
    get_adjective_grammar_prompt,
    get_verb_grammar_prompt,
    get_pronoun_grammar_prompt,
    get_number_grammar_prompt,
)
from app.grammar.russian import (
    WordClassification,
    Noun,
    Adjective,
    Verb,
    Pronoun,
    Number,
)

logger = logging.getLogger(__name__)


def analyze_russian_grammar_impl(russian_word: str) -> Dict[str, Any]:
    """Implementation for grammar analysis tool."""
    try:
        # Try to get dictionary form from Hunspell first
        analyzer = get_hunspell_analyzer()
        hunspell_info = {}
        
        if analyzer.is_available():
            analysis = analyzer.analyze_word(russian_word)
            hunspell_info = {
                "is_valid": analysis.is_valid,
                "stems": analysis.stems,
                "dictionary_forms": list(analysis.dictionary_forms),
                "suggestions": analysis.suggestions
            }
            logger.info(f"Hunspell analysis for '{russian_word}': {hunspell_info}")
        
        # Create LLM instance
        llm = ChatOpenAI(
            api_key=SecretStr(settings.openai_api_key), model=settings.llm_model
        )

        # Step 1: Classify the word
        classification_chain = (
            initial_classification_prompt
            | llm
            | PydanticOutputParser(pydantic_object=WordClassification)
        )

        classification: WordClassification = classification_chain.invoke(
            {"word": russian_word}
        )

        result = {
            "original_human_input": russian_word,
            "classification": classification,
            "hunspell_analysis": hunspell_info,
            "noun_grammar": None,
            "adjective_grammar": None,
            "verb_grammar": None,
            "pronoun_grammar": None,
            "number_grammar": None,
            "final_answer": None,
        }

        # Step 2: Get detailed grammar based on word type
        word_type = classification.word_type
        russian_form = classification.russian_word

        if word_type == "noun":
            # Prepare context for LLM with Hunspell information
            word_context = {"word": russian_form}
            if hunspell_info and hunspell_info.get("dictionary_forms"):
                dictionary_forms = hunspell_info["dictionary_forms"]
                word_context["hunspell_dictionary_forms"] = dictionary_forms
                word_context["word"] = f"{russian_form} (dictionary forms from Hunspell: {', '.join(dictionary_forms)})"
            
            noun_chain = (
                get_noun_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Noun)
            )
            noun_grammar = noun_chain.invoke(word_context)
            result["noun_grammar"] = noun_grammar
            result["final_answer"] = noun_grammar.model_dump_json(indent=2)

        elif word_type == "adjective":
            # Prepare context for LLM with Hunspell information
            word_context = {"word": russian_form}
            if hunspell_info and hunspell_info.get("dictionary_forms"):
                dictionary_forms = hunspell_info["dictionary_forms"]
                word_context["word"] = f"{russian_form} (dictionary forms from Hunspell: {', '.join(dictionary_forms)})"
            
            adjective_chain = (
                get_adjective_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Adjective)
            )
            adjective_grammar = adjective_chain.invoke(word_context)
            result["adjective_grammar"] = adjective_grammar
            result["final_answer"] = adjective_grammar.model_dump_json(indent=2)

        elif word_type == "verb":
            # Prepare context for LLM with Hunspell information
            word_context = {"word": russian_form}
            if hunspell_info and hunspell_info.get("dictionary_forms"):
                dictionary_forms = hunspell_info["dictionary_forms"]
                word_context["word"] = f"{russian_form} (dictionary forms from Hunspell: {', '.join(dictionary_forms)})"
            
            verb_chain = (
                get_verb_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Verb)
            )
            verb_grammar = verb_chain.invoke(word_context)
            result["verb_grammar"] = verb_grammar
            result["final_answer"] = verb_grammar.model_dump_json(indent=2)

        elif word_type == "pronoun":
            # Prepare context for LLM with Hunspell information
            word_context = {"word": russian_form}
            if hunspell_info and hunspell_info.get("dictionary_forms"):
                dictionary_forms = hunspell_info["dictionary_forms"]
                word_context["word"] = f"{russian_form} (dictionary forms from Hunspell: {', '.join(dictionary_forms)})"
            
            pronoun_chain = (
                get_pronoun_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Pronoun)
            )
            pronoun_grammar = pronoun_chain.invoke(word_context)
            result["pronoun_grammar"] = pronoun_grammar
            result["final_answer"] = pronoun_grammar.model_dump_json(indent=2)

        elif word_type == "number":
            # Prepare context for LLM with Hunspell information
            word_context = {"word": russian_form}
            if hunspell_info and hunspell_info.get("dictionary_forms"):
                dictionary_forms = hunspell_info["dictionary_forms"]
                word_context["word"] = f"{russian_form} (dictionary forms from Hunspell: {', '.join(dictionary_forms)})"
            
            number_chain = (
                get_number_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Number)
            )
            number_grammar = number_chain.invoke(word_context)
            result["number_grammar"] = number_grammar
            result["final_answer"] = number_grammar.model_dump_json(indent=2)

        # Check if we got a classification but no detailed grammar (e.g., unsupported word type like adverb)
        if not any(
            [
                result.get("noun_grammar"),
                result.get("adjective_grammar"),
                result.get("verb_grammar"),
                result.get("pronoun_grammar"),
                result.get("number_grammar"),
            ]
        ):
            return {
                "word": russian_word,
                "analysis": result,
                "word_type": word_type,
                "message": f"I can identify this as a {word_type}, but detailed grammar analysis is not yet supported for this word type.",
                "success": True,
            }

        return {"word": russian_word, "analysis": result, "success": True}

    except Exception as e:
        logger.error(f"Error in grammar analysis tool: {e}")
        return {"word": russian_word, "error": str(e), "success": False}
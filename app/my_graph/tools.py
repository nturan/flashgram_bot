"""Tool implementations for the Conversational Russian Tutor chatbot."""

import json
import logging
from typing import Dict, Any, Optional, Union, List

from pydantic import SecretStr
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from app.config import settings
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
from app.my_graph.flashcard_generator import flashcard_generator
from app.my_graph.sentence_generation import LLMSentenceGenerator
from app.flashcards import flashcard_service
from app.flashcards.models import WordType

logger = logging.getLogger(__name__)


def analyze_russian_grammar_impl(russian_word: str) -> Dict[str, Any]:
    """Implementation for grammar analysis tool."""
    try:
        # Create LLM instance
        llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
        
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
            "noun_grammar": None,
            "adjective_grammar": None,
            "verb_grammar": None,
            "pronoun_grammar": None,
            "number_grammar": None,
            "final_answer": None
        }
        
        # Step 2: Get detailed grammar based on word type
        word_type = classification.word_type
        russian_form = classification.russian_word
        
        if word_type == "noun":
            noun_chain = (
                get_noun_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Noun)
            )
            noun_grammar = noun_chain.invoke({"word": russian_form})
            result["noun_grammar"] = noun_grammar
            result["final_answer"] = noun_grammar.model_dump_json(indent=2)
            
        elif word_type == "adjective":
            adjective_chain = (
                get_adjective_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Adjective)
            )
            adjective_grammar = adjective_chain.invoke({"word": russian_form})
            result["adjective_grammar"] = adjective_grammar
            result["final_answer"] = adjective_grammar.model_dump_json(indent=2)
            
        elif word_type == "verb":
            verb_chain = (
                get_verb_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Verb)
            )
            verb_grammar = verb_chain.invoke({"word": russian_form})
            result["verb_grammar"] = verb_grammar
            result["final_answer"] = verb_grammar.model_dump_json(indent=2)
            
        elif word_type == "pronoun":
            pronoun_chain = (
                get_pronoun_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Pronoun)
            )
            pronoun_grammar = pronoun_chain.invoke({"word": russian_form})
            result["pronoun_grammar"] = pronoun_grammar
            result["final_answer"] = pronoun_grammar.model_dump_json(indent=2)
            
        elif word_type == "number":
            number_chain = (
                get_number_grammar_prompt
                | llm
                | PydanticOutputParser(pydantic_object=Number)
            )
            number_grammar = number_chain.invoke({"word": russian_form})
            result["number_grammar"] = number_grammar
            result["final_answer"] = number_grammar.model_dump_json(indent=2)
        
        # Check if we got a classification but no detailed grammar (e.g., unsupported word type like adverb)
        if not any([
            result.get("noun_grammar"),
            result.get("adjective_grammar"), 
            result.get("verb_grammar"),
            result.get("pronoun_grammar"),
            result.get("number_grammar")
        ]):
            return {
                "word": russian_word,
                "analysis": result,
                "word_type": word_type,
                "message": f"I can identify this as a {word_type}, but detailed grammar analysis is not yet supported for this word type.",
                "success": True
            }
        
        return {
            "word": russian_word,
            "analysis": result,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in grammar analysis tool: {e}")
        return {
            "word": russian_word,
            "error": str(e),
            "success": False
        }


def correct_multilingual_mistakes_impl(mixed_text: str) -> Dict[str, Any]:
    """Implementation for correction tool."""
    try:
        # Create LLM instance
        llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
        
        correction_prompt = f"""Please analyze and correct this text that is intended to be Russian but may contain foreign words or grammatical mistakes:

Text: "{mixed_text}"

Provide a response in the following JSON format:
{{
    "original": "{mixed_text}",
    "corrected": "grammatically correct Russian version",
    "mistakes": [
        {{
            "type": "foreign_word|grammar|case|gender|spelling",
            "original": "incorrect part",
            "corrected": "correct version", 
            "explanation": "brief explanation of the mistake"
        }}
    ],
    "overall_explanation": "brief summary of what was corrected"
}}

Focus on:
1. Replacing English/German words with Russian equivalents
2. Fixing case agreements (noun-adjective, preposition-noun)
3. Correcting verb conjugations
4. Fixing word order if needed
"""
        
        response = llm.invoke([HumanMessage(content=correction_prompt)])
        
        # Try to parse JSON response
        try:
            result = json.loads(response.content)
            result["success"] = True
            return result
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "original": mixed_text,
                "corrected": response.content,
                "mistakes": [],
                "overall_explanation": "Correction provided but couldn't parse detailed breakdown",
                "success": True
            }
            
    except Exception as e:
        logger.error(f"Error in correction tool: {e}")
        return {
            "original": mixed_text,
            "error": str(e),
            "success": False
        }


def generate_flashcards_from_analysis_impl(analysis_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None, 
                                         focus_areas: Optional[List[str]] = None,
                                         word: Optional[str] = None) -> Dict[str, Any]:
    """Implementation for flashcard generation tool."""
    try:
        # Handle case where analysis_data is a list (multiple words analyzed)
        if isinstance(analysis_data, list):
            if len(analysis_data) == 1:
                analysis_data = analysis_data[0]
            else:
                # For multiple words, generate flashcards for all and combine results
                total_flashcards = 0
                combined_word_types = []
                
                for single_analysis in analysis_data:
                    result = generate_flashcards_from_analysis_impl(single_analysis, focus_areas, None)
                    if result.get("success"):
                        total_flashcards += result.get("flashcards_generated", 0)
                        if result.get("word_type"):
                            combined_word_types.append(result["word_type"])
                
                return {
                    "flashcards_generated": total_flashcards,
                    "total_flashcards": total_flashcards,
                    "word_types": combined_word_types,
                    "focus_areas": focus_areas,
                    "message": f"Generated {total_flashcards} flashcards for {len(analysis_data)} words",
                    "success": True
                }

        # If no analysis_data provided but word is given, analyze the word first
        if not analysis_data and word:
            analysis_result = analyze_russian_grammar_impl(word)
            if analysis_result.get("success"):
                analysis_data = analysis_result
        
        # Extract grammar analysis from the tool result
        grammar_result = None
        if analysis_data and "analysis" in analysis_data:
            grammar_result = analysis_data["analysis"]
        elif analysis_data and any(key in analysis_data for key in ["noun_grammar", "adjective_grammar", "verb_grammar", "pronoun_grammar", "number_grammar"]):
            # analysis_data might be the grammar_result itself
            grammar_result = analysis_data
        
        if grammar_result:
            # Determine word type and grammar object
            flashcards = []
            word_type = None
            grammar_obj = None
            
            if grammar_result.get("noun_grammar"):
                grammar_data = grammar_result["noun_grammar"]
                word_type = "noun"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    grammar_obj = Noun(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("adjective_grammar"):
                grammar_data = grammar_result["adjective_grammar"]
                word_type = "adjective"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    grammar_obj = Adjective(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("verb_grammar"):
                grammar_data = grammar_result["verb_grammar"]
                word_type = "verb"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    grammar_obj = Verb(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("pronoun_grammar"):
                grammar_data = grammar_result["pronoun_grammar"]
                word_type = "pronoun"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    grammar_obj = Pronoun(**grammar_data)
                else:
                    grammar_obj = grammar_data
            elif grammar_result.get("number_grammar"):
                grammar_data = grammar_result["number_grammar"]
                word_type = "number"
                # Convert dict back to Pydantic model if needed
                if isinstance(grammar_data, dict):
                    from app.grammar.russian import Number as NumberClass
                    grammar_obj = NumberClass(**grammar_data)
                else:
                    grammar_obj = grammar_data
            
            if grammar_obj and word_type:
                # Generate flashcards
                flashcards = flashcard_generator.generate_flashcards_from_grammar(
                    grammar_obj, word_type
                )
                
                # Save to database
                saved_count = flashcard_generator.save_flashcards_to_database(flashcards)
                
                # Track dictionary word only if flashcards were generated successfully
                if saved_count > 0 and grammar_obj:
                    # Extract dictionary form from grammar object
                    dictionary_form = getattr(grammar_obj, 'dictionary_form', None)
                    if dictionary_form:
                        try:
                            word_type_enum = WordType(word_type)
                            
                            # Check if word already exists in dictionary
                            existing_word = flashcard_service.db.get_processed_word(dictionary_form, word_type_enum)
                            if existing_word:
                                # Update existing word stats
                                flashcard_service.db.update_processed_word_stats(
                                    dictionary_form, word_type_enum, additional_flashcards=saved_count
                                )
                                logger.info(f"Updated stats for existing word {dictionary_form} (+{saved_count} flashcards)")
                            else:
                                # Add new processed word
                                flashcard_service.db.add_processed_word(
                                    dictionary_form=dictionary_form,
                                    word_type=word_type_enum,
                                    flashcards_generated=saved_count,
                                    grammar_data=grammar_result
                                )
                                logger.info(f"Added new word {dictionary_form} to dictionary with {saved_count} flashcards")
                        except ValueError:
                            logger.warning(f"Word type {word_type} not supported for dictionary tracking")
                
                focus_info = f" (focusing on {', '.join(focus_areas)})" if focus_areas else ""
                
                return {
                    "flashcards_generated": saved_count,
                    "total_flashcards": len(flashcards),
                    "word_type": word_type,
                    "focus_areas": focus_areas,
                    "message": f"Generated {saved_count} flashcards for {word_type}{focus_info}",
                    "success": True
                }
            else:
                # Word type not supported for flashcard generation
                return {
                    "flashcards_generated": 0,
                    "error": f"Flashcard generation not supported for this word type",
                    "success": False
                }
        
        return {
            "flashcards_generated": 0,
            "error": "No valid grammar analysis found. Please provide analysis_data or word parameter.",
            "success": False
        }
        
    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        return {
            "flashcards_generated": 0,
            "error": str(e),
            "success": False
        }


def translate_phrase_impl(text: str, from_lang: str, to_lang: str) -> Dict[str, Any]:
    """Implementation for translation tool."""
    try:
        # Create LLM instance
        llm = ChatOpenAI(api_key=SecretStr(settings.openai_api_key), model=settings.llm_model)
        
        translation_prompt = f"""Translate the following {from_lang} text to {to_lang}:

Text: "{text}"

Provide a natural, contextually appropriate translation. If the text contains grammar learning content, include brief notes about any important grammatical considerations."""

        response = llm.invoke([HumanMessage(content=translation_prompt)])
        
        return {
            "original": text,
            "translation": response.content,
            "from_language": from_lang,
            "to_language": to_lang,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error in translation tool: {e}")
        return {
            "original": text,
            "error": str(e),
            "success": False
        }


def generate_example_sentences_impl(word: str, grammatical_context: str, theme: Optional[str] = None) -> Dict[str, Any]:
    """Implementation for example sentence generation tool."""
    try:
        sentence_generator = LLMSentenceGenerator()
        
        examples = []
        
        # Generate 2-3 example sentences
        for i in range(3):
            if theme:
                sentence = sentence_generator.generate_contextual_sentence(
                    word, word, grammatical_context, theme
                )
            else:
                sentence = sentence_generator.generate_example_sentence(
                    word, word, grammatical_context, "word"
                )
            examples.append(sentence)
        
        return {
            "word": word,
            "context": grammatical_context,
            "theme": theme,
            "examples": examples,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error generating example sentences: {e}")
        return {
            "word": word,
            "error": str(e),
            "success": False
        }


def process_bulk_text_for_flashcards_impl(text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Implementation for bulk text processing tool."""
    try:
        # Import here to avoid circular import
        from app.my_graph.bulk_text_processor import bulk_processor
        
        # Use a default user_id if not provided (for testing)
        if user_id is None:
            user_id = 0
        
        # Start bulk processing
        job_id = bulk_processor.start_bulk_processing(text, user_id)
        
        # Get initial job status
        job_status = bulk_processor.get_job_status(job_id)
        
        return {
            "job_id": job_id,
            "status": "started",
            "total_words": job_status["total_words"] if job_status else 0,
            "message": f"Started processing text with {job_status['total_words'] if job_status else 0} Russian words. This will run in the background.",
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error starting bulk text processing: {e}")
        return {
            "error": str(e),
            "success": False
        }


def check_bulk_processing_status_impl(job_id: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    """Implementation for bulk processing status check tool."""
    try:
        # Import here to avoid circular import
        from app.my_graph.bulk_text_processor import bulk_processor
        
        if job_id:
            # Check specific job
            job_status = bulk_processor.get_job_status(job_id)
            if not job_status:
                return {
                    "error": f"Job {job_id} not found",
                    "success": False
                }
            return {
                "job": job_status,
                "success": True
            }
        
        elif user_id:
            # Get all jobs for user
            user_jobs = bulk_processor.get_user_jobs(user_id)
            return {
                "jobs": user_jobs,
                "total_jobs": len(user_jobs),
                "success": True
            }
        
        else:
            return {
                "error": "Please provide either job_id or user_id",
                "success": False
            }
        
    except Exception as e:
        logger.error(f"Error checking bulk processing status: {e}")
        return {
            "error": str(e),
            "success": False
        }
"""Flashcard generation tool implementation."""

import logging
from typing import Dict, Any, Optional, Union, List

from app.grammar.russian import (
    Noun,
    Adjective,
    Verb,
    Pronoun,
    Number,
)
from app.my_graph.flashcard_generator import flashcard_generator
from app.flashcards import flashcard_service
from app.flashcards.models import WordType

logger = logging.getLogger(__name__)


def generate_flashcards_from_analysis_impl(
    analysis_data: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    focus_areas: Optional[List[str]] = None,
    word: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Implementation for flashcard generation tool."""
    try:
        # Check if user_id is provided - required for multi-user support
        if user_id is None:
            return {
                "flashcards_generated": 0,
                "error": "User ID is required for flashcard generation",
                "success": False,
            }
        # Handle case where analysis_data is a list (multiple words analyzed)
        if isinstance(analysis_data, list):
            if len(analysis_data) == 1:
                analysis_data = analysis_data[0]
            else:
                # For multiple words, generate flashcards for all and combine results
                total_flashcards = 0
                combined_word_types = []

                for single_analysis in analysis_data:
                    result = generate_flashcards_from_analysis_impl(
                        single_analysis, focus_areas, None, user_id
                    )
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
                    "success": True,
                }

        # If no analysis_data provided but word is given, analyze the word first
        if not analysis_data and word:
            from app.my_graph.tools.grammar_analysis import analyze_russian_grammar_impl
            
            analysis_result = analyze_russian_grammar_impl(word)
            if analysis_result.get("success"):
                analysis_data = analysis_result

        # Extract grammar analysis from the tool result
        grammar_result = None
        if analysis_data and "analysis" in analysis_data:
            grammar_result = analysis_data["analysis"]
        elif analysis_data and any(
            key in analysis_data
            for key in [
                "noun_grammar",
                "adjective_grammar",
                "verb_grammar",
                "pronoun_grammar",
                "number_grammar",
            ]
        ):
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
                    grammar_obj, word_type, None, user_id
                )

                # Save to database
                saved_count = flashcard_generator.save_flashcards_to_database(
                    user_id, flashcards
                )

                # Track dictionary word only if flashcards were generated successfully
                if saved_count > 0 and grammar_obj:
                    # Extract dictionary form from grammar object
                    dictionary_form = getattr(grammar_obj, "dictionary_form", None)
                    if dictionary_form:
                        try:
                            word_type_enum = WordType(word_type)

                            # Check if word already exists in dictionary
                            existing_word = flashcard_service.db.get_processed_word(
                                user_id, dictionary_form, word_type_enum
                            )
                            if existing_word:
                                # Update existing word stats
                                flashcard_service.db.update_processed_word_stats(
                                    user_id,
                                    dictionary_form,
                                    word_type_enum,
                                    additional_flashcards=saved_count,
                                )
                                logger.info(
                                    f"Updated stats for existing word {dictionary_form} (+{saved_count} flashcards)"
                                )
                            else:
                                # Add new processed word
                                flashcard_service.db.add_processed_word(
                                    user_id=user_id,
                                    dictionary_form=dictionary_form,
                                    word_type=word_type_enum,
                                    flashcards_generated=saved_count,
                                    grammar_data=grammar_result,
                                )
                                logger.info(
                                    f"Added new word {dictionary_form} to dictionary with {saved_count} flashcards"
                                )
                        except ValueError:
                            logger.warning(
                                f"Word type {word_type} not supported for dictionary tracking"
                            )

                focus_info = (
                    f" (focusing on {', '.join(focus_areas)})" if focus_areas else ""
                )

                return {
                    "flashcards_generated": saved_count,
                    "total_flashcards": len(flashcards),
                    "word_type": word_type,
                    "focus_areas": focus_areas,
                    "message": f"Generated {saved_count} flashcards for {word_type}{focus_info}",
                    "success": True,
                }
            else:
                # Word type not supported for flashcard generation
                return {
                    "flashcards_generated": 0,
                    "error": f"Flashcard generation not supported for this word type",
                    "success": False,
                }

        return {
            "flashcards_generated": 0,
            "error": "No valid grammar analysis found. Please provide analysis_data or word parameter.",
            "success": False,
        }

    except Exception as e:
        logger.error(f"Error generating flashcards: {e}")
        return {"flashcards_generated": 0, "error": str(e), "success": False}
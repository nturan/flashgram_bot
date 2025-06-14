"""Simplified tests for flashcard generation tool."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.tools.flashcard_generation import generate_flashcards_from_analysis_impl


class TestFlashcardGenerationSimple:
    """Simplified test cases for flashcard generation functionality."""

    def test_generate_flashcards_from_analysis_success(self):
        """Test successful flashcard generation."""
        from app.flashcards.models import TwoSidedCard, WordType
        
        # Mock the dependencies with valid data
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_flashcards = [TwoSidedCard(user_id=1, front="дом", back="house", word_type=WordType.NOUN)]
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            analysis_data = {
                "analysis": {
                    "noun_grammar": {
                        "dictionary_form": "дом",
                        "gender": "masculine",
                        "animacy": False,
                        "singular": {"nom": "дом", "gen": "дома", "dat": "дому", "acc": "дом", "ins": "домом", "pre": "доме"},
                        "plural": {"nom": "дома", "gen": "домов", "dat": "домам", "acc": "дома", "ins": "домами", "pre": "домах"},
                        "english_translation": "house"
                    }
                }
            }
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["flashcards_generated"] == 1
            assert result["word_type"] == "noun"

    def test_generate_flashcards_from_analysis_error(self):
        """Test error handling in flashcard generation."""
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg:
            mock_fg.generate_flashcards_from_grammar.side_effect = Exception("Database connection failed")
            
            analysis_data = {
                "analysis": {
                    "noun_grammar": {
                        "dictionary_form": "дом",
                        "gender": "masculine",
                        "animacy": False,
                        "singular": {"nom": "дом", "gen": "дома", "dat": "дому", "acc": "дом", "ins": "домом", "pre": "доме"},
                        "plural": {"nom": "дома", "gen": "домов", "dat": "домам", "acc": "дома", "ins": "домами", "pre": "домах"},
                        "english_translation": "house"
                    }
                }
            }
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is False
            assert result["flashcards_generated"] == 0
            assert "error" in result

    def test_generate_flashcards_from_analysis_no_data(self):
        """Test handling of missing analysis data."""
        result = generate_flashcards_from_analysis_impl(None, user_id=1)
        
        assert result["success"] is False
        assert result["flashcards_generated"] == 0
        assert "No valid grammar analysis found" in result["error"]

    def test_generate_flashcards_from_analysis_unsupported_type(self):
        """Test handling of unsupported word types."""
        analysis_data = {
            "analysis": {
                "adverb_grammar": {  # Unsupported type
                    "dictionary_form": "быстро",
                    "translation": "quickly"
                }
            }
        }
        
        result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
        
        assert result["success"] is False
        assert result["flashcards_generated"] == 0
        assert "not supported for this word type" in result["error"]
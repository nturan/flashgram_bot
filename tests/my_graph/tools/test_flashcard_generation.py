"""Tests for flashcard generation tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.my_graph.tools.flashcard_generation import generate_flashcards_from_analysis_impl
from app.grammar.russian import Noun, Adjective, Verb, Pronoun, Number
from app.flashcards.models import TwoSidedCard, WordType, DifficultyLevel


class TestFlashcardGeneration:
    """Test cases for flashcard generation from grammar analysis."""

    def test_generate_flashcards_from_analysis_with_noun_data(self):
        """Test flashcard generation with noun analysis data."""
        # Mock noun grammar data
        noun_data = {
            "dictionary_form": "дом",
            "gender": "masculine",
            "animacy": False,
            "singular": {
                "nom": "дом",
                "gen": "дома",
                "dat": "дому",
                "acc": "дом",
                "ins": "домом",
                "pre": "доме"
            },
            "plural": {
                "nom": "дома",
                "gen": "домов",
                "dat": "домам",
                "acc": "дома",
                "ins": "домами",
                "pre": "домах"
            },
            "english_translation": "house"
        }
        
        analysis_data = {
            "analysis": {
                "noun_grammar": noun_data
            }
        }
        
        # Mock flashcard generator
        mock_flashcards = [
            TwoSidedCard(
                user_id=1,
                front="дом",
                back="house",
                word_type=WordType.NOUN,
                difficulty=DifficultyLevel.EASY
            )
        ]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["flashcards_generated"] == 1
            assert result["word_type"] == "noun"
            mock_fg.generate_flashcards_from_grammar.assert_called_once()
            mock_fg.save_flashcards_to_database.assert_called_once_with(1, mock_flashcards)

    def test_generate_flashcards_from_analysis_with_adjective_data(self):
        """Test flashcard generation with adjective analysis data."""
        adjective_data = {
            "dictionary_form": "красивый",
            "english_translation": "beautiful",
            "masculine": {
                "nom": "красивый",
                "gen": "красивого",
                "dat": "красивому",
                "acc": "красивый",
                "ins": "красивым",
                "pre": "красивом"
            },
            "feminine": {
                "nom": "красивая",
                "gen": "красивой",
                "dat": "красивой",
                "acc": "красивую",
                "ins": "красивой",
                "pre": "красивой"
            },
            "neuter": {
                "nom": "красивое",
                "gen": "красивого",
                "dat": "красивому",
                "acc": "красивое",
                "ins": "красивым",
                "pre": "красивом"
            },
            "plural": {
                "nom": "красивые",
                "gen": "красивых",
                "dat": "красивым",
                "acc": "красивые",
                "ins": "красивыми",
                "pre": "красивых"
            }
        }
        
        analysis_data = {
            "analysis": {
                "adjective_grammar": adjective_data
            }
        }
        
        mock_flashcards = [
            TwoSidedCard(
                user_id=1,
                front="красивый",
                back="beautiful",
                word_type=WordType.ADJECTIVE,
                difficulty=DifficultyLevel.EASY
            )
        ]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["word_type"] == "adjective"

    def test_generate_flashcards_from_analysis_with_word_parameter(self):
        """Test flashcard generation using word parameter instead of analysis_data."""
        with patch('app.my_graph.tools.grammar_analysis.analyze_russian_grammar_impl') as mock_analyze, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            # Mock the grammar analysis
            mock_analyze.return_value = {
                "success": True,
                "analysis": {
                    "noun_grammar": {
                        "dictionary_form": "кот",
                        "gender": "masculine",
                        "animacy": True,
                        "singular": {
                            "nom": "кот",
                            "gen": "кота",
                            "dat": "коту",
                            "acc": "кота",
                            "ins": "котом",
                            "pre": "коте"
                        },
                        "plural": {
                            "nom": "коты",
                            "gen": "котов",
                            "dat": "котам",
                            "acc": "котов",
                            "ins": "котами",
                            "pre": "котах"
                        },
                        "english_translation": "cat"
                    }
                }
            }
            
            mock_flashcards = [TwoSidedCard(user_id=1, front="кот", back="cat", word_type=WordType.NOUN)]
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(word="кот", user_id=1)
            
            assert result["success"] is True
            mock_analyze.assert_called_once_with("кот")

    def test_generate_flashcards_from_analysis_with_list_input(self):
        """Test flashcard generation with list of analysis data."""
        analysis_list = [
            {
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
            },
            {
                "analysis": {
                    "adjective_grammar": {
                        "dictionary_form": "красивый",
                        "english_translation": "beautiful",
                        "masculine": {"nom": "красивый", "gen": "красивого", "dat": "красивому", "acc": "красивый", "ins": "красивым", "pre": "красивом"},
                        "feminine": {"nom": "красивая", "gen": "красивой", "dat": "красивой", "acc": "красивую", "ins": "красивой", "pre": "красивой"},
                        "neuter": {"nom": "красивое", "gen": "красивого", "dat": "красивому", "acc": "красивое", "ins": "красивым", "pre": "красивом"},
                        "plural": {"nom": "красивые", "gen": "красивых", "dat": "красивым", "acc": "красивые", "ins": "красивыми", "pre": "красивых"}
                    }
                }
            }
        ]
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="дом", back="house", word_type=WordType.NOUN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_list, user_id=1)
            
            assert result["success"] is True
            assert result["flashcards_generated"] == 2  # 2 calls, 1 each
            assert len(result["word_types"]) == 2

    def test_generate_flashcards_from_analysis_existing_word_update(self):
        """Test updating existing processed word stats."""
        noun_data = {
            "dictionary_form": "дом",
            "gender": "masculine",
            "animacy": False,
            "singular": {"nom": "дом", "gen": "дома", "dat": "дому", "acc": "дом", "ins": "домом", "pre": "доме"},
            "plural": {"nom": "дома", "gen": "домов", "dat": "домам", "acc": "дома", "ins": "домами", "pre": "домах"},
            "english_translation": "house"
        }
        
        analysis_data = {
            "analysis": {
                "noun_grammar": noun_data
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="дом", back="house", word_type=WordType.NOUN)]
        mock_existing_word = {"dictionary_form": "дом", "flashcards_count": 5}
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = mock_existing_word
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            mock_fs.db.update_processed_word_stats.assert_called_once()

    def test_generate_flashcards_from_analysis_new_word_addition(self):
        """Test adding new processed word to dictionary."""
        noun_data = {
            "dictionary_form": "собака",
            "gender": "feminine",
            "animacy": True,
            "singular": {"nom": "собака", "gen": "собаки", "dat": "собаке", "acc": "собаку", "ins": "собакой", "pre": "собаке"},
            "plural": {"nom": "собаки", "gen": "собак", "dat": "собакам", "acc": "собак", "ins": "собаками", "pre": "собаках"},
            "english_translation": "dog"
        }
        
        analysis_data = {
            "analysis": {
                "noun_grammar": noun_data
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="собака", back="dog", word_type=WordType.NOUN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None  # New word
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            mock_fs.db.add_processed_word.assert_called_once()

    def test_generate_flashcards_from_analysis_with_focus_areas(self):
        """Test flashcard generation with focus areas specified."""
        noun_data = {
            "dictionary_form": "стол",
            "gender": "masculine",
            "animacy": False,
            "singular": {"nom": "стол", "gen": "стола", "dat": "столу", "acc": "стол", "ins": "столом", "pre": "столе"},
            "plural": {"nom": "столы", "gen": "столов", "dat": "столам", "acc": "столы", "ins": "столами", "pre": "столах"},
            "english_translation": "table"
        }
        
        analysis_data = {
            "analysis": {
                "noun_grammar": noun_data
            }
        }
        
        focus_areas = ["declension", "cases"]
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="стол", back="table", word_type=WordType.NOUN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, focus_areas=focus_areas, user_id=1)
            
            assert result["success"] is True
            assert result["focus_areas"] == focus_areas
            assert "focusing on declension, cases" in result["message"]

    def test_generate_flashcards_from_analysis_unsupported_word_type(self):
        """Test handling of unsupported word types."""
        analysis_data = {
            "analysis": {
                "adverb_grammar": {  # Unsupported type
                    "dictionary_form": "быстро",
                    "word": "быстро",
                    "translation": "quickly"
                }
            }
        }
        
        result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
        
        assert result["success"] is False
        assert result["flashcards_generated"] == 0
        assert "not supported for this word type" in result["error"]

    def test_generate_flashcards_from_analysis_no_valid_data(self):
        """Test handling of missing or invalid analysis data."""
        result = generate_flashcards_from_analysis_impl(None, user_id=1)
        
        assert result["success"] is False
        assert result["flashcards_generated"] == 0
        assert "No valid grammar analysis found" in result["error"]

    def test_generate_flashcards_from_analysis_database_save_error(self):
        """Test handling of database save errors."""
        noun_data = {
            "dictionary_form": "дом",
            "gender": "masculine",
            "animacy": False,
            "singular": {"nom": "дом", "gen": "дома", "dat": "дому", "acc": "дом", "ins": "домом", "pre": "доме"},
            "plural": {"nom": "дома", "gen": "домов", "dat": "домам", "acc": "дома", "ins": "домами", "pre": "домах"},
            "english_translation": "house"
        }
        
        analysis_data = {
            "analysis": {
                "noun_grammar": noun_data
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="дом", back="house", word_type=WordType.NOUN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg:
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 0  # Save failed
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["flashcards_generated"] == 0

    def test_generate_flashcards_from_analysis_exception_handling(self):
        """Test handling of unexpected exceptions."""
        analysis_data = {
            "analysis": {
                "noun_grammar": {
                    "dictionary_form": "тест",
                    "gender": "masculine",
                    "animacy": False,
                    "singular": {"nom": "тест", "gen": "теста", "dat": "тесту", "acc": "тест", "ins": "тестом", "pre": "тесте"},
                    "plural": {"nom": "тесты", "gen": "тестов", "dat": "тестам", "acc": "тесты", "ins": "тестами", "pre": "тестах"},
                    "english_translation": "test"
                }
            }
        }
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg:
            mock_fg.generate_flashcards_from_grammar.side_effect = Exception("Unexpected error")
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is False
            assert result["flashcards_generated"] == 0
            assert "Unexpected error" in result["error"]

    def test_generate_flashcards_from_analysis_verb_data(self):
        """Test flashcard generation with verb analysis data."""
        verb_data = {
            "dictionary_form": "читать",
            "english_translation": "to read",
            "aspect": "imperfective",
            "present_first_singular": "читаю",
            "present_second_singular": "читаешь",
            "present_third_singular": "читает",
            "present_first_plural": "читаем",
            "present_second_plural": "читаете",
            "present_third_plural": "читают",
            "past_masculine": "читал",
            "past_feminine": "читала",
            "past_neuter": "читало",
            "past_plural": "читали"
        }
        
        analysis_data = {
            "analysis": {
                "verb_grammar": verb_data
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="читать", back="to read", word_type=WordType.VERB)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["word_type"] == "verb"

    def test_generate_flashcards_from_analysis_pronoun_data(self):
        """Test flashcard generation with pronoun analysis data."""
        pronoun_data = {
            "dictionary_form": "я",
            "english_translation": "I",
            "singular": {
                "nom": "я",
                "gen": "меня",
                "dat": "мне",
                "acc": "меня",
                "ins": "мной",
                "pre": "мне"
            }
        }
        
        analysis_data = {
            "analysis": {
                "pronoun_grammar": pronoun_data
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="я", back="I", word_type=WordType.PRONOUN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["word_type"] == "pronoun"

    def test_generate_flashcards_from_analysis_number_data(self):
        """Test flashcard generation with number analysis data."""
        number_data = {
            "dictionary_form": "один",
            "english_translation": "one",
            "masculine": {
                "nom": "один",
                "gen": "одного",
                "dat": "одному",
                "acc": "один",
                "ins": "одним",
                "pre": "одном"
            },
            "feminine": {
                "nom": "одна",
                "gen": "одной",
                "dat": "одной",
                "acc": "одну",
                "ins": "одной",
                "pre": "одной"
            },
            "neuter": {
                "nom": "одно",
                "gen": "одного",
                "dat": "одному",
                "acc": "одно",
                "ins": "одним",
                "pre": "одном"
            }
        }
        
        analysis_data = {
            "analysis": {
                "number_grammar": number_data
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="один", back="one", word_type=WordType.UNKNOWN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs:
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            assert result["word_type"] == "number"

    def test_generate_flashcards_from_analysis_dict_to_pydantic_conversion(self):
        """Test conversion of dictionary data to Pydantic models."""
        # Test with dictionary format grammar data
        analysis_data = {
            "noun_grammar": {  # Direct format, not nested under "analysis"
                "dictionary_form": "книга",
                "gender": "feminine",
                "animacy": False,
                "singular": {"nom": "книга", "gen": "книги", "dat": "книге", "acc": "книгу", "ins": "книгой", "pre": "книге"},
                "plural": {"nom": "книги", "gen": "книг", "dat": "книгам", "acc": "книги", "ins": "книгами", "pre": "книгах"},
                "english_translation": "book"
            }
        }
        
        mock_flashcards = [TwoSidedCard(user_id=1, front="книга", back="book", word_type=WordType.NOUN)]
        
        with patch('app.my_graph.tools.flashcard_generation.flashcard_generator') as mock_fg, \
             patch('app.my_graph.tools.flashcard_generation.flashcard_service') as mock_fs, \
             patch('app.my_graph.tools.flashcard_generation.Noun') as mock_noun:
            
            mock_noun_instance = Mock()
            mock_noun_instance.dictionary_form = "книга"
            mock_noun.return_value = mock_noun_instance
            
            mock_fg.generate_flashcards_from_grammar.return_value = mock_flashcards
            mock_fg.save_flashcards_to_database.return_value = 1
            mock_fs.db.get_processed_word.return_value = None
            
            result = generate_flashcards_from_analysis_impl(analysis_data, user_id=1)
            
            assert result["success"] is True
            mock_noun.assert_called_once()  # Verify Pydantic model was created from dict
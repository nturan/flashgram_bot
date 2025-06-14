"""Tests for text correction tool."""

import pytest
import json
from unittest.mock import Mock, patch

from app.my_graph.tools.text_correction import correct_multilingual_mistakes_impl


class TestTextCorrection:
    """Test cases for multilingual text correction functionality."""

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_success_with_json(self, mock_openai):
        """Test successful text correction with proper JSON response."""
        # Mock LLM response with valid JSON
        mock_response = Mock()
        mock_response.content = json.dumps({
            "original": "Я like собака",
            "corrected": "Я люблю собаку",
            "mistakes": [
                {
                    "type": "foreign_word",
                    "original": "like",
                    "corrected": "люблю",
                    "explanation": "English word replaced with Russian verb"
                },
                {
                    "type": "case",
                    "original": "собака",
                    "corrected": "собаку",
                    "explanation": "Changed to accusative case as direct object"
                }
            ],
            "overall_explanation": "Replaced English words and fixed case agreement"
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Я like собака")
        
        assert result["success"] is True
        assert result["original"] == "Я like собака"
        assert result["corrected"] == "Я люблю собаку"
        assert len(result["mistakes"]) == 2
        assert result["mistakes"][0]["type"] == "foreign_word"
        assert result["mistakes"][1]["type"] == "case"
        assert "overall_explanation" in result

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_json_parse_error(self, mock_openai):
        """Test handling of invalid JSON response from LLM."""
        # Mock LLM response with invalid JSON
        mock_response = Mock()
        mock_response.content = "This is not valid JSON but still a correction"
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Я have problem")
        
        assert result["success"] is True
        assert result["original"] == "Я have problem"
        assert result["corrected"] == "This is not valid JSON but still a correction"
        assert result["mistakes"] == []
        assert "couldn't parse detailed breakdown" in result["overall_explanation"]

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_llm_error(self, mock_openai):
        """Test error handling when LLM call fails."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("API connection failed")
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Test text")
        
        assert result["success"] is False
        assert result["original"] == "Test text"
        assert "error" in result
        assert "API connection failed" in result["error"]

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_german_words(self, mock_openai):
        """Test correction of German words mixed with Russian."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "original": "Я gehe в школу",
            "corrected": "Я иду в школу",
            "mistakes": [
                {
                    "type": "foreign_word",
                    "original": "gehe",
                    "corrected": "иду",
                    "explanation": "German verb replaced with Russian equivalent"
                }
            ],
            "overall_explanation": "Replaced German verb with Russian"
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Я gehe в школу")
        
        assert result["success"] is True
        assert result["corrected"] == "Я иду в школу"
        assert result["mistakes"][0]["original"] == "gehe"
        assert result["mistakes"][0]["corrected"] == "иду"

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_grammar_only(self, mock_openai):
        """Test correction of purely grammatical mistakes without foreign words."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "original": "Красивая дом стоит",
            "corrected": "Красивый дом стоит",
            "mistakes": [
                {
                    "type": "gender",
                    "original": "Красивая",
                    "corrected": "Красивый",
                    "explanation": "Adjective should agree with masculine noun 'дом'"
                }
            ],
            "overall_explanation": "Fixed gender agreement between adjective and noun"
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Красивая дом стоит")
        
        assert result["success"] is True
        assert result["corrected"] == "Красивый дом стоит"
        assert result["mistakes"][0]["type"] == "gender"

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_no_errors(self, mock_openai):
        """Test handling of text that doesn't need correction."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "original": "Я читаю книгу",
            "corrected": "Я читаю книгу",
            "mistakes": [],
            "overall_explanation": "Text is already grammatically correct"
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Я читаю книгу")
        
        assert result["success"] is True
        assert result["original"] == result["corrected"]
        assert len(result["mistakes"]) == 0
        assert "already" in result["overall_explanation"] or "correct" in result["overall_explanation"]

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_complex_text(self, mock_openai):
        """Test correction of complex text with multiple error types."""
        mock_response = Mock()
        mock_response.content = json.dumps({
            "original": "Yesterday я went to магазин and купил bread",
            "corrected": "Вчера я пошёл в магазин и купил хлеб",
            "mistakes": [
                {
                    "type": "foreign_word",
                    "original": "Yesterday",
                    "corrected": "Вчера",
                    "explanation": "English time expression replaced with Russian"
                },
                {
                    "type": "foreign_word",
                    "original": "went",
                    "corrected": "пошёл",
                    "explanation": "English verb replaced with Russian past tense"
                },
                {
                    "type": "foreign_word",
                    "original": "and",
                    "corrected": "и",
                    "explanation": "English conjunction replaced with Russian"
                },
                {
                    "type": "foreign_word",
                    "original": "bread",
                    "corrected": "хлеб",
                    "explanation": "English noun replaced with Russian"
                }
            ],
            "overall_explanation": "Translated all English words to Russian while preserving sentence structure"
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("Yesterday я went to магазин and купил bread")
        
        assert result["success"] is True
        assert result["corrected"] == "Вчера я пошёл в магазин и купил хлеб"
        assert len(result["mistakes"]) == 4
        assert all(mistake["type"] == "foreign_word" for mistake in result["mistakes"])

    def test_correct_multilingual_mistakes_empty_input(self):
        """Test handling of empty input text."""
        result = correct_multilingual_mistakes_impl("")
        
        # Should still attempt to process empty text
        assert result["original"] == ""
        # The result depends on how the LLM handles empty input, so we just check basic structure

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_very_long_text(self, mock_openai):
        """Test handling of very long input text."""
        long_text = "Я люблю читать книги. " * 100  # Very long text
        
        mock_response = Mock()
        mock_response.content = json.dumps({
            "original": long_text,
            "corrected": long_text,
            "mistakes": [],
            "overall_explanation": "Text is grammatically correct"
        })
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl(long_text)
        
        assert result["success"] is True
        assert result["original"] == long_text

    @patch('app.my_graph.tools.text_correction.settings')
    def test_correct_multilingual_mistakes_settings_integration(self, mock_settings):
        """Test that the function uses settings correctly."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.llm_model = "gpt-4"
        
        with patch('app.my_graph.tools.text_correction.ChatOpenAI') as mock_openai:
            mock_llm = Mock()
            mock_llm.invoke.side_effect = Exception("Test exception")
            mock_openai.return_value = mock_llm
            
            result = correct_multilingual_mistakes_impl("test")
            
            # Should have been called with correct settings
            mock_openai.assert_called_once()
            call_args = mock_openai.call_args
            assert call_args[1]['model'] == "gpt-4"

    @patch('app.my_graph.tools.text_correction.ChatOpenAI')
    def test_correct_multilingual_mistakes_partial_json(self, mock_openai):
        """Test handling of partially malformed JSON response."""
        # Mock LLM response with malformed JSON (missing closing bracket)
        mock_response = Mock()
        mock_response.content = '{"original": "test", "corrected": "тест"'
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = correct_multilingual_mistakes_impl("test")
        
        assert result["success"] is True
        assert result["original"] == "test"
        assert result["corrected"] == '{"original": "test", "corrected": "тест"'
        assert result["mistakes"] == []
        assert "couldn't parse detailed breakdown" in result["overall_explanation"]
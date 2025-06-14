"""Tests for translation tool."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.tools.translation import translate_phrase_impl


class TestTranslation:
    """Test cases for phrase translation functionality."""

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_russian_to_english(self, mock_openai):
        """Test translation from Russian to English."""
        mock_response = Mock()
        mock_response.content = "I am reading a book about Russian grammar."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(
            "Я читаю книгу о русской грамматике",
            "Russian",
            "English"
        )
        
        assert result["success"] is True
        assert result["original"] == "Я читаю книгу о русской грамматике"
        assert result["translation"] == "I am reading a book about Russian grammar."
        assert result["from_language"] == "Russian"
        assert result["to_language"] == "English"
        
        # Verify LLM was called with correct prompt
        mock_llm.invoke.assert_called_once()
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1
        assert "Russian" in call_args[0].content
        assert "English" in call_args[0].content

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_english_to_russian(self, mock_openai):
        """Test translation from English to Russian."""
        mock_response = Mock()
        mock_response.content = "Я изучаю русский язык каждый день."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(
            "I study Russian language every day",
            "English",
            "Russian"
        )
        
        assert result["success"] is True
        assert result["original"] == "I study Russian language every day"
        assert result["translation"] == "Я изучаю русский язык каждый день."
        assert result["from_language"] == "English"
        assert result["to_language"] == "Russian"

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_german_to_russian(self, mock_openai):
        """Test translation from German to Russian."""
        mock_response = Mock()
        mock_response.content = "Я иду в школу."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(
            "Ich gehe zur Schule",
            "German",
            "Russian"
        )
        
        assert result["success"] is True
        assert result["original"] == "Ich gehe zur Schule"
        assert result["translation"] == "Я иду в школу."
        assert result["from_language"] == "German"
        assert result["to_language"] == "Russian"

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_with_grammar_notes(self, mock_openai):
        """Test translation that includes grammatical notes."""
        mock_response = Mock()
        mock_response.content = """I love books.

Grammatical note: The verb "люблю" (love) is in first person singular present tense and requires the accusative case for the direct object "книги" (books)."""
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(
            "Я люблю книги",
            "Russian",
            "English"
        )
        
        assert result["success"] is True
        assert result["original"] == "Я люблю книги"
        assert "I love books" in result["translation"]
        assert "Grammatical note" in result["translation"]
        assert "accusative case" in result["translation"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_llm_error(self, mock_openai):
        """Test error handling when LLM call fails."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Network timeout")
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(
            "Test text",
            "English",
            "Russian"
        )
        
        assert result["success"] is False
        assert result["original"] == "Test text"
        assert "error" in result
        assert "Network timeout" in result["error"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_empty_text(self, mock_openai):
        """Test translation of empty text."""
        mock_response = Mock()
        mock_response.content = ""
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl("", "English", "Russian")
        
        assert result["success"] is True
        assert result["original"] == ""
        assert result["translation"] == ""

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_very_long_text(self, mock_openai):
        """Test translation of very long text."""
        long_text = "This is a very long sentence that contains many words. " * 50
        mock_response = Mock()
        mock_response.content = "Это очень длинное предложение с множеством слов. " * 50
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(long_text, "English", "Russian")
        
        assert result["success"] is True
        assert result["original"] == long_text
        assert len(result["translation"]) > 0

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_special_characters(self, mock_openai):
        """Test translation of text with special characters and punctuation."""
        text_with_special = "Hello, world! How are you? I'm fine... (really!)"
        mock_response = Mock()
        mock_response.content = "Привет, мир! Как дела? У меня всё хорошо... (правда!)"
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(text_with_special, "English", "Russian")
        
        assert result["success"] is True
        assert result["original"] == text_with_special
        assert "Привет, мир!" in result["translation"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_numbers_and_dates(self, mock_openai):
        """Test translation of text containing numbers and dates."""
        text_with_numbers = "I was born on January 15, 1990, and I am 33 years old."
        mock_response = Mock()
        mock_response.content = "Я родился 15 января 1990 года, и мне 33 года."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(text_with_numbers, "English", "Russian")
        
        assert result["success"] is True
        assert result["original"] == text_with_numbers
        assert "1990" in result["translation"]
        assert "33" in result["translation"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_technical_terms(self, mock_openai):
        """Test translation of text with technical/specialized terms."""
        technical_text = "Machine learning algorithms use neural networks for pattern recognition."
        mock_response = Mock()
        mock_response.content = "Алгоритмы машинного обучения используют нейронные сети для распознавания образов."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(technical_text, "English", "Russian")
        
        assert result["success"] is True
        assert "машинного обучения" in result["translation"]
        assert "нейронные сети" in result["translation"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_idiomatic_expressions(self, mock_openai):
        """Test translation of idiomatic expressions."""
        idiomatic_text = "It's raining cats and dogs today."
        mock_response = Mock()
        mock_response.content = "Сегодня дождь как из ведра."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(idiomatic_text, "English", "Russian")
        
        assert result["success"] is True
        assert result["original"] == idiomatic_text
        assert "как из ведра" in result["translation"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_russian_to_german(self, mock_openai):
        """Test translation from Russian to German."""
        mock_response = Mock()
        mock_response.content = "Ich lese ein Buch über russische Grammatik."
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(
            "Я читаю книгу о русской грамматике",
            "Russian",
            "German"
        )
        
        assert result["success"] is True
        assert result["from_language"] == "Russian"
        assert result["to_language"] == "German"
        assert "Ich lese ein Buch" in result["translation"]

    @patch('app.my_graph.tools.translation.settings')
    def test_translate_phrase_settings_integration(self, mock_settings):
        """Test that the function uses settings correctly."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.llm_model = "gpt-4"
        
        with patch('app.my_graph.tools.translation.ChatOpenAI') as mock_openai:
            mock_llm = Mock()
            mock_llm.invoke.side_effect = Exception("Test exception")
            mock_openai.return_value = mock_llm
            
            result = translate_phrase_impl("test", "English", "Russian")
            
            # Should have been called with correct settings
            mock_openai.assert_called_once()
            call_args = mock_openai.call_args
            assert call_args[1]['model'] == "gpt-4"

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_preserve_formatting(self, mock_openai):
        """Test that translation preserves basic formatting."""
        formatted_text = """Line 1
Line 2
- Bullet point 1
- Bullet point 2"""
        
        mock_response = Mock()
        mock_response.content = """Строка 1
Строка 2
- Пункт 1
- Пункт 2"""
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(formatted_text, "English", "Russian")
        
        assert result["success"] is True
        assert "\n" in result["translation"]
        assert "- " in result["translation"]

    @patch('app.my_graph.tools.translation.ChatOpenAI')
    def test_translate_phrase_mixed_languages_input(self, mock_openai):
        """Test translation of text that already contains mixed languages."""
        mixed_text = "I want to learn русский язык"
        mock_response = Mock()
        mock_response.content = "Я хочу изучать русский язык"
        
        mock_llm = Mock()
        mock_llm.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm
        
        result = translate_phrase_impl(mixed_text, "English", "Russian")
        
        assert result["success"] is True
        assert result["original"] == mixed_text
        assert "русский язык" in result["translation"]
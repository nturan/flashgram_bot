"""Tests for sentence generation tool."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.tools.sentence_generation import generate_example_sentences_impl


class TestSentenceGeneration:
    """Test cases for example sentence generation functionality."""

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_basic(self, mock_generator_class):
        """Test basic example sentence generation without theme."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Я читаю интересную книгу."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="книга",
            grammatical_context="accusative case, feminine noun"
        )
        
        assert result["success"] is True
        assert result["word"] == "книга"
        assert result["context"] == "accusative case, feminine noun"
        assert result["theme"] is None
        assert len(result["examples"]) == 3
        assert all(example == "Я читаю интересную книгу." for example in result["examples"])
        
        # Verify the generator was called correctly
        assert mock_generator.generate_example_sentence.call_count == 3
        call_args = mock_generator.generate_example_sentence.call_args
        assert call_args[0] == ("книга", "книга", "accusative case, feminine noun", "word")

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_with_theme(self, mock_generator_class):
        """Test example sentence generation with a specific theme."""
        mock_generator = Mock()
        mock_generator.generate_contextual_sentence.return_value = "В школе дети изучают математику."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="школа",
            grammatical_context="prepositional case, feminine noun",
            theme="education"
        )
        
        assert result["success"] is True
        assert result["word"] == "школа"
        assert result["context"] == "prepositional case, feminine noun"
        assert result["theme"] == "education"
        assert len(result["examples"]) == 3
        assert all(example == "В школе дети изучают математику." for example in result["examples"])
        
        # Verify the generator was called with theme
        assert mock_generator.generate_contextual_sentence.call_count == 3
        call_args = mock_generator.generate_contextual_sentence.call_args
        assert call_args[0] == ("школа", "школа", "prepositional case, feminine noun", "education")

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_different_examples(self, mock_generator_class):
        """Test that different example sentences can be generated."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.side_effect = [
            "Собака бежит в парке.",
            "Моя собака очень дружелюбная.",
            "Собака лает на кота."
        ]
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="собака",
            grammatical_context="nominative case, feminine noun"
        )
        
        assert result["success"] is True
        assert len(result["examples"]) == 3
        assert result["examples"][0] == "Собака бежит в парке."
        assert result["examples"][1] == "Моя собака очень дружелюбная."
        assert result["examples"][2] == "Собака лает на кота."

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_verb_context(self, mock_generator_class):
        """Test sentence generation for verb context."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Я читаю книгу каждый день."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="читать",
            grammatical_context="first person singular present tense"
        )
        
        assert result["success"] is True
        assert result["word"] == "читать"
        assert result["context"] == "first person singular present tense"
        assert len(result["examples"]) == 3

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_adjective_context(self, mock_generator_class):
        """Test sentence generation for adjective context."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Красивый дом стоит на холме."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="красивый",
            grammatical_context="masculine nominative singular"
        )
        
        assert result["success"] is True
        assert result["word"] == "красивый"
        assert result["context"] == "masculine nominative singular"
        assert all("Красивый дом" in example for example in result["examples"])

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_theme_variations(self, mock_generator_class):
        """Test sentence generation with different themes."""
        themes_and_responses = [
            ("food", "В ресторане я заказал вкусную еду."),
            ("travel", "Во время путешествия я видел много интересного."),
            ("family", "Моя семья очень дружная и заботливая.")
        ]
        
        for theme, expected_response in themes_and_responses:
            mock_generator = Mock()
            mock_generator.generate_contextual_sentence.return_value = expected_response
            mock_generator_class.return_value = mock_generator
            
            result = generate_example_sentences_impl(
                word="test",
                grammatical_context="test context",
                theme=theme
            )
            
            assert result["success"] is True
            assert result["theme"] == theme
            assert all(example == expected_response for example in result["examples"])

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_generator_exception(self, mock_generator_class):
        """Test error handling when sentence generator raises an exception."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.side_effect = Exception("API connection failed")
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="тест",
            grammatical_context="test context"
        )
        
        assert result["success"] is False
        assert result["word"] == "тест"
        assert "error" in result
        assert "API connection failed" in result["error"]

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_generator_init_exception(self, mock_generator_class):
        """Test error handling when sentence generator initialization fails."""
        mock_generator_class.side_effect = Exception("Generator initialization failed")
        
        result = generate_example_sentences_impl(
            word="тест",
            grammatical_context="test context"
        )
        
        assert result["success"] is False
        assert result["word"] == "тест"
        assert "Generator initialization failed" in result["error"]

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_partial_failure(self, mock_generator_class):
        """Test handling when some sentence generations fail."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.side_effect = [
            "Первое предложение успешно.",
            Exception("Second generation failed"),
            "Третье предложение успешно."
        ]
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="тест",
            grammatical_context="test context"
        )
        
        # Should fail on the first exception
        assert result["success"] is False
        assert "Second generation failed" in result["error"]

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_empty_word(self, mock_generator_class):
        """Test sentence generation with empty word."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Пример предложения."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="",
            grammatical_context="test context"
        )
        
        assert result["success"] is True
        assert result["word"] == ""
        assert len(result["examples"]) == 3

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_empty_context(self, mock_generator_class):
        """Test sentence generation with empty grammatical context."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Пример предложения."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="слово",
            grammatical_context=""
        )
        
        assert result["success"] is True
        assert result["context"] == ""
        assert len(result["examples"]) == 3

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_empty_theme(self, mock_generator_class):
        """Test sentence generation with empty theme (should use non-contextual generation)."""
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Пример без темы."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word="слово",
            grammatical_context="context",
            theme=""
        )
        
        # Empty theme should be treated as None and use generate_example_sentence
        assert result["success"] is True
        assert result["theme"] == ""
        assert mock_generator.generate_example_sentence.call_count == 3
        assert mock_generator.generate_contextual_sentence.call_count == 0

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_long_inputs(self, mock_generator_class):
        """Test sentence generation with very long inputs."""
        long_word = "очень" * 50
        long_context = "длинный грамматический контекст " * 20
        long_theme = "очень длинная тема " * 10
        
        mock_generator = Mock()
        mock_generator.generate_contextual_sentence.return_value = "Длинное предложение в ответ."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word=long_word,
            grammatical_context=long_context,
            theme=long_theme
        )
        
        assert result["success"] is True
        assert result["word"] == long_word
        assert result["context"] == long_context
        assert result["theme"] == long_theme

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_special_characters(self, mock_generator_class):
        """Test sentence generation with special characters in inputs."""
        word_with_special = "слово-то"
        context_with_special = "контекст (с особыми символами)!"
        theme_with_special = "тема#с@специальными$символами"
        
        mock_generator = Mock()
        mock_generator.generate_contextual_sentence.return_value = "Предложение со специальными символами."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word=word_with_special,
            grammatical_context=context_with_special,
            theme=theme_with_special
        )
        
        assert result["success"] is True
        assert result["word"] == word_with_special
        assert result["context"] == context_with_special
        assert result["theme"] == theme_with_special

    @patch('app.my_graph.tools.sentence_generation.LLMSentenceGenerator')
    def test_generate_example_sentences_unicode_characters(self, mock_generator_class):
        """Test sentence generation with Unicode characters."""
        unicode_word = "слово🌟"
        unicode_context = "контекст с эмодзи 😊"
        
        mock_generator = Mock()
        mock_generator.generate_example_sentence.return_value = "Предложение с Unicode символами 🎉."
        mock_generator_class.return_value = mock_generator
        
        result = generate_example_sentences_impl(
            word=unicode_word,
            grammatical_context=unicode_context
        )
        
        assert result["success"] is True
        assert result["word"] == unicode_word
        assert result["context"] == unicode_context
        assert "🎉" in result["examples"][0]
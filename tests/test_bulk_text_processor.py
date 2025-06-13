"""Tests for BulkTextProcessor functionality."""

import unittest
from app.my_graph.bulk_text_processor import BulkTextProcessor


class TestBulkTextProcessor(unittest.TestCase):
    """Test cases for BulkTextProcessor class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.processor = BulkTextProcessor()

    def test_extract_russian_words_basic(self):
        """Test extraction of Russian words from simple text."""
        text = "Это простой русский текст для тестирования."
        expected = ["это", "простой", "русский", "текст", "для", "тестирования"]
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)

    def test_extract_russian_words_mixed_language(self):
        """Test extraction of Russian words from mixed language text."""
        text = "Hello привет world мир! This is English text."
        expected = ["привет", "мир"]
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)

    def test_extract_russian_words_filters_short_words(self):
        """Test that words shorter than 3 characters are filtered out."""
        text = "Я ты он она они большой дом."
        # Should filter out "я", "ты", "он" (< 3 chars) but keep "она", "они", "большой", "дом"
        expected = ["она", "они", "большой", "дом"]
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)

    def test_extract_russian_words_removes_duplicates(self):
        """Test that duplicate words are removed."""
        text = "дом дом дом большой дом красивый большой"
        expected = ["дом", "большой", "красивый"]
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)

    def test_extract_russian_words_empty_text(self):
        """Test extraction from empty text."""
        text = ""
        expected = []
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)

    def test_extract_russian_words_no_russian(self):
        """Test extraction from text with no Russian words."""
        text = "Hello world! This is English text 123."
        expected = []
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)

    def test_extract_russian_words_with_punctuation(self):
        """Test extraction from text with punctuation and special characters."""
        text = "Привет, как дела? Всё хорошо! Спасибо."
        expected = ["привет", "как", "дела", "всё", "хорошо", "спасибо"]
        result = self.processor.extract_russian_words(text)
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()

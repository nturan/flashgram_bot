"""Tests for base flashcard generator."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.generators.base_generator import BaseGenerator
from app.flashcards.models import FillInTheBlank, TwoSidedCard, MultipleChoice


class TestBaseGenerator:
    """Test cases for BaseGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        self.generator = BaseGenerator()

    def test_init(self):
        """Test BaseGenerator initialization."""
        assert self.generator.sentence_generator is not None
        assert self.generator.text_processor is not None
        assert self.generator.suffix_extractor is not None
        assert self.generator.form_analyzer is not None

    def test_create_fill_in_gap_card_with_pre_generated_sentence(self):
        """Test creating fill-in-gap card with pre-generated sentence."""
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract, \
             patch.object(self.generator.text_processor, 'create_sentence_with_blank') as mock_create_blank:
            
            mock_extract.return_value = ("дом", "а")
            mock_create_blank.return_value = "В ___а живет семья."
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="дом",
                target_form="дома",
                form_description="GEN singular",
                word_type="noun",
                tags=["russian", "noun"],
                grammatical_key="genitive",
                pre_generated_sentence="В дома живет семья."
            )
            
            assert isinstance(card, FillInTheBlank)
            assert card.text_with_blanks == "В ___а живет семья."
            assert card.answers == ["а"]
            assert card.case_sensitive is False
            assert "fill_in_gap" in card.tags
            assert "suffix" in card.tags
            assert "russian" in card.tags
            assert "noun" in card.tags
            assert card.title == "дом - GEN singular (gap fill)"
            assert card.metadata["form_description"] == "GEN singular"
            assert card.metadata["dictionary_form"] == "дом"
            assert card.metadata["grammatical_key"] == "genitive"

    def test_create_fill_in_gap_card_generate_sentence(self):
        """Test creating fill-in-gap card with sentence generation."""
        with patch.object(self.generator.sentence_generator, 'generate_example_sentence') as mock_generate, \
             patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract, \
             patch.object(self.generator.text_processor, 'create_sentence_with_blank') as mock_create_blank:
            
            mock_generate.return_value = "Я вижу красивую собаку."
            mock_extract.return_value = ("собак", "у")
            mock_create_blank.return_value = "Я вижу красивую собак___."
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="собака",
                target_form="собаку",
                form_description="ACC singular",
                word_type="noun",
                tags=["russian", "noun", "feminine"]
            )
            
            assert isinstance(card, FillInTheBlank)
            assert card.text_with_blanks == "Я вижу красивую собак___."
            assert card.answers == ["у"]
            assert card.metadata["grammatical_key"] == "ACC singular"
            
            mock_generate.assert_called_once_with("собака", "собаку", "ACC singular", "noun")

    def test_create_two_sided_card(self):
        """Test creating two-sided flashcard."""
        card = self.generator.create_two_sided_card(
            front="What is the gender of 'дом'?",
            back="masculine",
            tags=["russian", "noun", "gender"],
            title="дом - gender"
        )
        
        assert isinstance(card, TwoSidedCard)
        assert card.front == "What is the gender of 'дом'?"
        assert card.back == "masculine"
        assert card.tags == ["russian", "noun", "gender"]
        assert card.title == "дом - gender"

    def test_should_create_flashcard_valid_form(self):
        """Test should_create_flashcard with valid form."""
        result = self.generator.should_create_flashcard("дома", "дом")
        assert result is True

    def test_should_create_flashcard_same_as_dictionary(self):
        """Test should_create_flashcard with form same as dictionary form."""
        result = self.generator.should_create_flashcard("дом", "дом")
        assert result is False

    def test_should_create_flashcard_case_insensitive(self):
        """Test should_create_flashcard is case insensitive."""
        result = self.generator.should_create_flashcard("ДОМ", "дом")
        assert result is False

    def test_should_create_flashcard_empty_form(self):
        """Test should_create_flashcard with empty form."""
        result = self.generator.should_create_flashcard("", "дом")
        assert not result  # Empty string is falsy

    def test_should_create_flashcard_whitespace_form(self):
        """Test should_create_flashcard with whitespace-only form."""
        result = self.generator.should_create_flashcard("   ", "дом")
        assert not result  # Empty string after strip is falsy

    def test_should_create_flashcard_none_form(self):
        """Test should_create_flashcard with None form."""
        # The method returns None for None input (falsy)
        result = self.generator.should_create_flashcard(None, "дом")
        assert not result  # None is falsy

    def test_generate_flashcards_from_grammar_not_implemented(self):
        """Test that generate_flashcards_from_grammar raises NotImplementedError."""
        with pytest.raises(NotImplementedError) as exc_info:
            self.generator.generate_flashcards_from_grammar(Mock(), "noun")
        
        assert "Subclasses must implement generate_flashcards_from_grammar" in str(exc_info.value)

    def test_create_fill_in_gap_card_no_grammatical_key(self):
        """Test creating fill-in-gap card without grammatical key."""
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract, \
             patch.object(self.generator.text_processor, 'create_sentence_with_blank') as mock_create_blank:
            
            mock_extract.return_value = ("стол", "а")
            mock_create_blank.return_value = "На стол___ лежит книга."
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="стол",
                target_form="столе",
                form_description="PREP singular",
                word_type="noun",
                tags=["russian", "noun"],
                pre_generated_sentence="На столе лежит книга."
            )
            
            assert card.metadata["grammatical_key"] == "PREP singular"  # Uses form_description

    def test_create_fill_in_gap_card_with_grammatical_key(self):
        """Test creating fill-in-gap card with explicit grammatical key."""
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract, \
             patch.object(self.generator.text_processor, 'create_sentence_with_blank') as mock_create_blank:
            
            mock_extract.return_value = ("кот", "а")
            mock_create_blank.return_value = "Я вижу кот___."
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="кот",
                target_form="кота",
                form_description="ACC singular",
                word_type="noun",
                tags=["russian", "noun"],
                grammatical_key="accusative_case",
                pre_generated_sentence="Я вижу кота."
            )
            
            assert card.metadata["grammatical_key"] == "accusative_case"

    def test_create_multiple_choice_card(self):
        """Test creating multiple choice flashcard."""
        card = self.generator.create_multiple_choice_card(
            question="What is the gender of 'дом'?",
            options=["masculine", "feminine", "neuter"],
            correct_indices=[0],
            tags=["russian", "noun", "gender", "multiple_choice"],
            title="дом - gender",
            allow_multiple=False
        )
        
        assert isinstance(card, MultipleChoice)
        assert card.question == "What is the gender of 'дом'?"
        assert card.options == ["masculine", "feminine", "neuter"]
        assert card.correct_indices == [0]
        assert card.allow_multiple is False
        assert card.tags == ["russian", "noun", "gender", "multiple_choice"]
        assert card.title == "дом - gender"
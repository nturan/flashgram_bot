"""Tests for base flashcard generator."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.my_graph.generators.base_generator import BaseGenerator


class TestBaseGenerator:
    """Test cases for BaseGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        self.generator = BaseGenerator()

    def test_init(self):
        """Test BaseGenerator initialization."""
        assert self.generator.suffix_extractor is not None
        assert self.generator.form_analyzer is not None

    @patch('app.my_graph.generators.base_generator.FillInTheBlank')
    def test_create_fill_in_gap_card_with_pre_generated_sentence(self, mock_fill_in_blank):
        """Test creating fill-in-gap card with pre-generated sentence."""
        mock_card = MagicMock()
        mock_fill_in_blank.return_value = mock_card
        
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract:
            
            mock_extract.return_value = ("дом", "а")
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="дом",
                target_form="дома",
                form_description="GEN singular",
                word_type="noun",
                tags=["russian", "noun"],
                grammatical_key="genitive",
                pre_generated_sentence="В дома живет семья."
            )
            
            # Verify the FillInTheBlank constructor was called with correct arguments
            mock_fill_in_blank.assert_called_once_with(
                user_id=1,
                text_with_blanks="В дом___ живет семья.",
                answers=["а"],
                case_sensitive=False,
                tags=["russian", "noun", "fill_in_gap", "suffix"],
                title="дом - GEN singular (gap fill)",
                metadata={
                    "form_description": "GEN singular",
                    "dictionary_form": "дом",
                    "grammatical_key": "genitive",
                },
            )
            
            assert card == mock_card

    @patch('app.my_graph.generators.base_generator.FillInTheBlank')
    def test_create_fill_in_gap_card_generate_sentence(self, mock_fill_in_blank):
        """Test creating fill-in-gap card without pre-generated sentence (fallback)."""
        mock_card = MagicMock()
        mock_fill_in_blank.return_value = mock_card
        
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract:
            
            mock_extract.return_value = ("собак", "у")
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="собака",
                target_form="собаку",
                form_description="ACC singular",
                word_type="noun",
                tags=["russian", "noun", "feminine"]
            )
            
            # Verify the FillInTheBlank constructor was called with template fallback
            mock_fill_in_blank.assert_called_once_with(
                user_id=1,
                text_with_blanks="Пример с собак___.",
                answers=["у"],
                case_sensitive=False,
                tags=["russian", "noun", "feminine", "fill_in_gap", "suffix"],
                title="собака - ACC singular (gap fill)",
                metadata={
                    "form_description": "ACC singular",
                    "dictionary_form": "собака",
                    "grammatical_key": "ACC singular",
                },
            )
            
            assert card == mock_card

    @patch('app.my_graph.generators.base_generator.TwoSidedCard')
    def test_create_two_sided_card(self, mock_two_sided_card):
        """Test creating two-sided flashcard."""
        mock_card = MagicMock()
        mock_two_sided_card.return_value = mock_card
        
        card = self.generator.create_two_sided_card(
            front="What is the gender of 'дом'?",
            back="masculine",
            tags=["russian", "noun", "gender"],
            title="дом - gender"
        )
        
        mock_two_sided_card.assert_called_once_with(
            user_id=1,
            front="What is the gender of 'дом'?",
            back="masculine",
            tags=["russian", "noun", "gender"],
            title="дом - gender"
        )
        
        assert card == mock_card

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

    @patch('app.my_graph.generators.base_generator.FillInTheBlank')
    def test_create_fill_in_gap_card_no_grammatical_key(self, mock_fill_in_blank):
        """Test creating fill-in-gap card without grammatical key."""
        mock_card = MagicMock()
        mock_fill_in_blank.return_value = mock_card
        
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract:
            
            mock_extract.return_value = ("стол", "е")
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="стол",
                target_form="столе",
                form_description="PREP singular",
                word_type="noun",
                tags=["russian", "noun"],
                pre_generated_sentence="На столе лежит книга."
            )
            
            # Verify grammatical_key uses form_description when not provided
            expected_metadata = {
                "form_description": "PREP singular",
                "dictionary_form": "стол",
                "grammatical_key": "PREP singular"
            }
            mock_fill_in_blank.assert_called_once()
            call_args = mock_fill_in_blank.call_args
            assert call_args.kwargs['metadata'] == expected_metadata
            assert card == mock_card

    @patch('app.my_graph.generators.base_generator.FillInTheBlank')
    def test_create_fill_in_gap_card_with_grammatical_key(self, mock_fill_in_blank):
        """Test creating fill-in-gap card with explicit grammatical key."""
        mock_card = MagicMock()
        mock_fill_in_blank.return_value = mock_card
        
        with patch.object(self.generator.suffix_extractor, 'extract_suffix') as mock_extract:
            
            mock_extract.return_value = ("кот", "а")
            
            card = self.generator.create_fill_in_gap_card(
                dictionary_form="кот",
                target_form="кота",
                form_description="ACC singular",
                word_type="noun",
                tags=["russian", "noun"],
                grammatical_key="accusative_case",
                pre_generated_sentence="Я вижу кота."
            )
            
            # Verify grammatical_key uses provided value
            expected_metadata = {
                "form_description": "ACC singular",
                "dictionary_form": "кот",
                "grammatical_key": "accusative_case"
            }
            mock_fill_in_blank.assert_called_once()
            call_args = mock_fill_in_blank.call_args
            assert call_args.kwargs['metadata'] == expected_metadata
            assert card == mock_card

    @patch('app.my_graph.generators.base_generator.MultipleChoice')
    def test_create_multiple_choice_card(self, mock_multiple_choice):
        """Test creating multiple choice flashcard."""
        mock_card = MagicMock()
        mock_multiple_choice.return_value = mock_card
        
        card = self.generator.create_multiple_choice_card(
            question="What is the gender of 'дом'?",
            options=["masculine", "feminine", "neuter"],
            correct_indices=[0],
            tags=["russian", "noun", "gender", "multiple_choice"],
            title="дом - gender",
            allow_multiple=False
        )
        
        mock_multiple_choice.assert_called_once_with(
            user_id=1,
            question="What is the gender of 'дом'?",
            options=["masculine", "feminine", "neuter"],
            correct_indices=[0],
            allow_multiple=False,
            tags=["russian", "noun", "gender", "multiple_choice"],
            title="дом - gender",
        )
        
        assert card == mock_card
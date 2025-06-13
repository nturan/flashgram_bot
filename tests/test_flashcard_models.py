"""Tests for flashcard models and their validation."""

import pytest
from datetime import datetime
from pydantic import ValidationError
from app.flashcards.models import (
    TwoSidedCard,
    FillInTheBlank,
    MultipleChoice,
    DictionaryWord,
    FlashcardType,
    DifficultyLevel,
    WordType,
    create_flashcard_from_dict,
)


class TestFlashcardEnums:
    """Test flashcard enum types."""

    def test_flashcard_type_enum(self):
        """Test FlashcardType enum values."""
        assert FlashcardType.TWO_SIDED == "two_sided"
        assert FlashcardType.FILL_IN_BLANK == "fill_in_blank"
        assert FlashcardType.MULTIPLE_CHOICE == "multiple_choice"

    def test_difficulty_level_enum(self):
        """Test DifficultyLevel enum values."""
        assert DifficultyLevel.VERY_EASY == "very_easy"
        assert DifficultyLevel.EASY == "easy"
        assert DifficultyLevel.MEDIUM == "medium"
        assert DifficultyLevel.HARD == "hard"
        assert DifficultyLevel.VERY_HARD == "very_hard"

    def test_word_type_enum(self):
        """Test WordType enum values."""
        assert WordType.NOUN == "noun"
        assert WordType.ADJECTIVE == "adjective"
        assert WordType.VERB == "verb"
        assert WordType.PRONOUN == "pronoun"


class TestTwoSidedCard:
    """Test TwoSidedCard model."""

    def test_create_valid_two_sided_card(self):
        """Test creating a valid two-sided flashcard."""
        card = TwoSidedCard(
            front="What is the Russian word for 'house'?",
            back="дом",
            tags=["vocabulary", "nouns"],
        )

        assert card.type == FlashcardType.TWO_SIDED
        assert card.front == "What is the Russian word for 'house'?"
        assert card.back == "дом"
        assert card.tags == ["vocabulary", "nouns"]
        assert card.difficulty == DifficultyLevel.MEDIUM  # default
        assert card.repetition_count == 0  # default
        assert card.ease_factor == 2.5  # default

    def test_two_sided_card_get_question(self):
        """Test get_question method."""
        card = TwoSidedCard(front="Test question", back="Test answer")
        assert card.get_question() == "Test question"

    def test_two_sided_card_check_answer(self):
        """Test check_answer method."""
        card = TwoSidedCard(front="What is 'дом'?", back="house")

        # Exact match
        assert card.check_answer("house") == True

        # Case insensitive
        assert card.check_answer("HOUSE") == True
        assert card.check_answer("House") == True

        # Whitespace handling
        assert card.check_answer("  house  ") == True

        # Wrong answer
        assert card.check_answer("home") == False
        assert card.check_answer("building") == False

    def test_two_sided_card_validation(self):
        """Test validation for required fields."""
        # Missing front
        with pytest.raises(ValidationError):
            TwoSidedCard(back="answer")

        # Missing back
        with pytest.raises(ValidationError):
            TwoSidedCard(front="question")

        # Empty strings should be allowed
        card = TwoSidedCard(front="", back="")
        assert card.front == ""
        assert card.back == ""


class TestFillInTheBlank:
    """Test FillInTheBlank model."""

    def test_create_valid_fill_in_blank(self):
        """Test creating a valid fill-in-the-blank flashcard."""
        card = FillInTheBlank(
            text_with_blanks="Я читаю {blank} книгу.",
            answers=["интересную"],
            case_sensitive=False,
        )

        assert card.type == FlashcardType.FILL_IN_BLANK
        assert card.text_with_blanks == "Я читаю {blank} книгу."
        assert card.answers == ["интересную"]
        assert card.case_sensitive == False

    def test_fill_in_blank_get_question(self):
        """Test get_question method replacing blanks."""
        card = FillInTheBlank(
            text_with_blanks="The {blank} is {blank}.", answers=["cat", "sleeping"]
        )

        expected = "The _____ is _____."
        assert card.get_question() == expected

    def test_fill_in_blank_check_answer(self):
        """Test check_answer method."""
        card = FillInTheBlank(
            text_with_blanks="Я читаю {blank} книгу.",
            answers=["интересную"],
            case_sensitive=False,
        )

        # Correct answer
        assert card.check_answer(["интересную"]) == True

        # Case insensitive (default)
        assert card.check_answer(["ИНТЕРЕСНУЮ"]) == True
        assert card.check_answer(["Интересную"]) == True

        # Whitespace handling
        assert card.check_answer(["  интересную  "]) == True

        # Wrong answer
        assert card.check_answer(["красивую"]) == False

        # Wrong number of answers
        assert card.check_answer([]) == False
        assert card.check_answer(["интересную", "extra"]) == False

    def test_fill_in_blank_case_sensitive(self):
        """Test case sensitive checking."""
        card = FillInTheBlank(
            text_with_blanks="Name: {blank}", answers=["John"], case_sensitive=True
        )

        assert card.check_answer(["John"]) == True
        assert card.check_answer(["john"]) == False
        assert card.check_answer(["JOHN"]) == False

    def test_fill_in_blank_multiple_blanks(self):
        """Test multiple blanks."""
        card = FillInTheBlank(
            text_with_blanks="I {blank} a {blank} book.", answers=["read", "good"]
        )

        assert card.get_blank_count() == 2
        assert card.check_answer(["read", "good"]) == True
        assert card.check_answer(["good", "read"]) == False  # Order matters

    def test_fill_in_blank_get_blank_count(self):
        """Test get_blank_count method."""
        card1 = FillInTheBlank(text_with_blanks="One {blank}", answers=["word"])
        assert card1.get_blank_count() == 1

        card2 = FillInTheBlank(
            text_with_blanks="Two {blank} and {blank}", answers=["words", "more"]
        )
        assert card2.get_blank_count() == 2

        card3 = FillInTheBlank(text_with_blanks="No blanks here", answers=[])
        assert card3.get_blank_count() == 0


class TestMultipleChoice:
    """Test MultipleChoice model."""

    def test_create_valid_multiple_choice(self):
        """Test creating a valid multiple choice flashcard."""
        card = MultipleChoice(
            question="What is the genitive singular of 'дом'?",
            options=["дома", "дому", "домом", "доме"],
            correct_indices=[0],
            allow_multiple=False,
        )

        assert card.type == FlashcardType.MULTIPLE_CHOICE
        assert card.question == "What is the genitive singular of 'дом'?"
        assert len(card.options) == 4
        assert card.correct_indices == [0]
        assert card.allow_multiple == False

    def test_multiple_choice_get_question(self):
        """Test get_question method with formatted options."""
        card = MultipleChoice(
            question="Choose the correct answer:",
            options=["Option 1", "Option 2", "Option 3"],
            correct_indices=[1],
        )

        expected = "Choose the correct answer:\n\nA. Option 1\nB. Option 2\nC. Option 3"
        assert card.get_question() == expected

    def test_multiple_choice_check_answer(self):
        """Test check_answer method."""
        card = MultipleChoice(
            question="Select correct options:",
            options=["A", "B", "C", "D"],
            correct_indices=[0, 2],  # A and C are correct
            allow_multiple=True,
        )

        # Correct answer
        assert card.check_answer([0, 2]) == True
        assert card.check_answer([2, 0]) == True  # Order doesn't matter

        # Partial correct
        assert card.check_answer([0]) == False
        assert card.check_answer([2]) == False

        # Wrong answers
        assert card.check_answer([1]) == False
        assert card.check_answer([0, 1, 2]) == False

        # Empty answer
        assert card.check_answer([]) == False

    def test_multiple_choice_single_correct(self):
        """Test single correct answer."""
        card = MultipleChoice(
            question="Single choice question",
            options=["A", "B", "C"],
            correct_indices=[1],
        )

        assert card.check_answer([1]) == True
        assert card.check_answer([0]) == False
        assert card.check_answer([1, 2]) == False  # Too many selected

    def test_multiple_choice_get_correct_letters(self):
        """Test get_correct_letters method."""
        card = MultipleChoice(
            question="Test question",
            options=["Option A", "Option B", "Option C", "Option D"],
            correct_indices=[0, 2, 3],
        )

        letters = card.get_correct_letters()
        assert letters == ["A", "C", "D"]

    def test_multiple_choice_validation(self):
        """Test validation for multiple choice cards."""
        # Test that basic validation works for required fields
        with pytest.raises(ValidationError):
            MultipleChoice(
                # Missing question
                options=["A", "B"],
                correct_indices=[0],
            )

        with pytest.raises(ValidationError):
            MultipleChoice(
                question="Test",
                # Missing options
                correct_indices=[0],
            )

        with pytest.raises(ValidationError):
            MultipleChoice(
                question="Test",
                options=["A", "B"],
                # Missing correct_indices
            )

        # Note: Pydantic doesn't automatically validate that correct_indices
        # are within range of options - this would be business logic validation


class TestDictionaryWord:
    """Test DictionaryWord model."""

    def test_create_valid_dictionary_word(self):
        """Test creating a valid dictionary word."""
        word = DictionaryWord(
            dictionary_form="дом",
            word_type=WordType.NOUN,
            flashcards_generated=5,
            grammar_data={"gender": "masculine", "animacy": "inanimate"},
        )

        assert word.dictionary_form == "дом"
        assert word.word_type == WordType.NOUN
        assert word.flashcards_generated == 5
        assert word.grammar_data["gender"] == "masculine"
        assert isinstance(word.processed_date, datetime)
        assert isinstance(word.created_at, datetime)

    def test_dictionary_word_defaults(self):
        """Test default values for DictionaryWord."""
        word = DictionaryWord(dictionary_form="тест", word_type=WordType.VERB)

        assert word.flashcards_generated == 0
        assert word.grammar_data == {}
        assert isinstance(word.processed_date, datetime)

    def test_dictionary_word_validation(self):
        """Test validation for required fields."""
        # Missing dictionary_form
        with pytest.raises(ValidationError):
            DictionaryWord(word_type=WordType.NOUN)

        # Missing word_type
        with pytest.raises(ValidationError):
            DictionaryWord(dictionary_form="тест")


class TestFlashcardFactory:
    """Test flashcard creation utilities."""

    def test_create_flashcard_from_dict_two_sided(self):
        """Test creating TwoSidedCard from dict."""
        data = {
            "type": "two_sided",
            "front": "Question",
            "back": "Answer",
            "tags": ["test"],
        }

        card = create_flashcard_from_dict(data)
        assert isinstance(card, TwoSidedCard)
        assert card.front == "Question"
        assert card.back == "Answer"
        assert card.tags == ["test"]

    def test_create_flashcard_from_dict_fill_in_blank(self):
        """Test creating FillInTheBlank from dict."""
        data = {
            "type": "fill_in_blank",
            "text_with_blanks": "Fill {blank} blank",
            "answers": ["the"],
            "case_sensitive": True,
        }

        card = create_flashcard_from_dict(data)
        assert isinstance(card, FillInTheBlank)
        assert card.text_with_blanks == "Fill {blank} blank"
        assert card.answers == ["the"]
        assert card.case_sensitive == True

    def test_create_flashcard_from_dict_multiple_choice(self):
        """Test creating MultipleChoice from dict."""
        data = {
            "type": "multiple_choice",
            "question": "Choose:",
            "options": ["A", "B", "C"],
            "correct_indices": [0, 2],
        }

        card = create_flashcard_from_dict(data)
        assert isinstance(card, MultipleChoice)
        assert card.question == "Choose:"
        assert card.options == ["A", "B", "C"]
        assert card.correct_indices == [0, 2]

    def test_create_flashcard_from_dict_invalid_type(self):
        """Test error handling for invalid flashcard type."""
        data = {"type": "invalid_type", "some_field": "value"}

        with pytest.raises(ValueError) as exc_info:
            create_flashcard_from_dict(data)

        assert "Unknown flashcard type" in str(exc_info.value)

    def test_create_flashcard_from_dict_missing_type(self):
        """Test error handling for missing type field."""
        data = {"front": "Question", "back": "Answer"}

        with pytest.raises(ValueError):
            create_flashcard_from_dict(data)


class TestFlashcardInheritance:
    """Test that all flashcard types inherit properly from BaseFlashcard."""

    def test_base_flashcard_fields_in_two_sided(self):
        """Test that TwoSidedCard has all base fields."""
        card = TwoSidedCard(
            front="Test",
            back="Test",
            difficulty=DifficultyLevel.HARD,
            tags=["grammar"],
            times_correct=3,
            times_incorrect=1,
        )

        # Check base fields are accessible
        assert card.difficulty == DifficultyLevel.HARD
        assert card.tags == ["grammar"]
        assert card.times_correct == 3
        assert card.times_incorrect == 1
        assert card.repetition_count == 0  # default
        assert card.ease_factor == 2.5  # default
        assert isinstance(card.due_date, datetime)

    def test_base_flashcard_fields_in_fill_in_blank(self):
        """Test that FillInTheBlank has all base fields."""
        card = FillInTheBlank(
            text_with_blanks="Test {blank}",
            answers=["word"],
            interval_days=7,
            metadata={"difficulty_reason": "complex grammar"},
        )

        assert card.interval_days == 7
        assert card.metadata["difficulty_reason"] == "complex grammar"
        assert isinstance(card.created_at, datetime)
        assert isinstance(card.updated_at, datetime)

    def test_base_flashcard_fields_in_multiple_choice(self):
        """Test that MultipleChoice has all base fields."""
        card = MultipleChoice(
            question="Test?",
            options=["A", "B"],
            correct_indices=[0],
            repetition_count=5,
            ease_factor=1.8,
        )

        assert card.repetition_count == 5
        assert card.ease_factor == 1.8
        assert card.type == FlashcardType.MULTIPLE_CHOICE

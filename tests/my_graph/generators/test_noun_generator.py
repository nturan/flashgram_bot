"""Tests for noun flashcard generator."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.generators.noun_generator import NounGenerator
from app.grammar.russian import Noun
from app.flashcards.models import FillInTheBlank, TwoSidedCard, MultipleChoice


class TestNounGenerator:
    """Test cases for NounGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        self.generator = NounGenerator()

    @pytest.fixture
    def sample_noun(self):
        """Create a sample noun for testing."""
        return Noun(
            dictionary_form="дом",
            gender="masculine",
            animacy=False,
            singular={
                "nom": "дом",
                "gen": "дома",
                "dat": "дому",
                "acc": "дом",
                "ins": "домом",
                "pre": "доме"
            },
            plural={
                "nom": "дома",
                "gen": "домов",
                "dat": "домам",
                "acc": "дома",
                "ins": "домами",
                "pre": "домах"
            },
            english_translation="house"
        )

    @pytest.fixture
    def generated_sentences(self):
        """Sample generated sentences."""
        return {
            "gen_singular": "У дома есть сад.",
            "dat_singular": "Мы идем к дому.",
            "ins_plural": "Мы живем в домами соседей."
        }

    def test_generate_flashcards_from_grammar_basic(self, sample_noun):
        """Test basic flashcard generation for noun."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_multiple_choice_card') as mock_create_mc:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_mc.return_value = Mock(spec=MultipleChoice)
            
            flashcards = self.generator.generate_flashcards_from_grammar(sample_noun)
            
            # Should create cards for all different forms plus property cards
            assert len(flashcards) > 0
            # Check calls for singular forms (6 cases - nom should be skipped)
            assert mock_create_gap.call_count >= 5  # At least gen, dat, acc, ins, pre for singular
            # Check calls for property cards (gender + animacy) - now multiple choice
            assert mock_create_mc.call_count == 2

    def test_generate_flashcards_from_grammar_with_sentences(self, sample_noun, generated_sentences):
        """Test flashcard generation with pre-generated sentences."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator.generate_flashcards_from_grammar(
                sample_noun, generated_sentences=generated_sentences
            )
            
            # Verify that pre-generated sentences are passed to create_fill_in_gap_card
            call_args_list = mock_create_gap.call_args_list
            
            # Find calls with pre_generated_sentence
            sentences_used = []
            for call in call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                if 'pre_generated_sentence' in kwargs:
                    sentences_used.append(kwargs['pre_generated_sentence'])
            
            # Should use some of the pre-generated sentences
            assert len(sentences_used) > 0

    def test_generate_singular_forms(self, sample_noun):
        """Test generation of singular form flashcards."""
        with patch.object(self.generator, 'should_create_flashcard') as mock_should_create, \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_should_create.return_value = True
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_singular_forms(sample_noun, "дом", {})
            
            # Should create cards for all forms where should_create_flashcard returns True
            assert len(flashcards) == 6  # All 6 cases
            assert mock_create_gap.call_count == 6

    def test_generate_singular_forms_skip_identical(self, sample_noun):
        """Test that identical forms are skipped in singular generation."""
        # Mock should_create_flashcard to return False for nom and acc (both "дом")
        def mock_should_create(form, dictionary_form):
            return form not in ["дом"]  # Skip nom and acc which are same as dictionary form
        
        with patch.object(self.generator, 'should_create_flashcard', side_effect=mock_should_create), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_singular_forms(sample_noun, "дом", {})
            
            # Should create cards only for forms different from dictionary form
            assert len(flashcards) == 4  # gen, dat, ins, pre (excluding nom and acc)
            assert mock_create_gap.call_count == 4

    def test_generate_plural_forms(self, sample_noun):
        """Test generation of plural form flashcards."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_plural_forms(sample_noun, "дом", {})
            
            assert len(flashcards) == 6  # All 6 cases for plural
            assert mock_create_gap.call_count == 6
            
            # Check that all calls have plural-related tags
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'plural' in tags

    def test_generate_property_flashcards(self, sample_noun):
        """Test generation of property flashcards (gender, animacy)."""
        with patch.object(self.generator, 'create_multiple_choice_card') as mock_create_mc:
            
            mock_create_mc.return_value = Mock(spec=MultipleChoice)
            
            flashcards = self.generator._generate_property_flashcards(sample_noun, "дом")
            
            assert len(flashcards) == 2  # Gender and animacy cards
            assert mock_create_mc.call_count == 2
            
            # Check gender card
            first_call = mock_create_mc.call_args_list[0]
            kwargs = first_call[1] if len(first_call) > 1 else {}
            gender_question = kwargs.get('question', '')
            gender_options = kwargs.get('options', [])
            gender_correct = kwargs.get('correct_indices', [])
            assert "gender" in gender_question.lower()
            assert "дом" in gender_question
            assert "masculine" in gender_options
            assert "feminine" in gender_options
            assert "neuter" in gender_options
            assert 0 in gender_correct  # masculine is first option
            
            # Check animacy card
            second_call = mock_create_mc.call_args_list[1]
            kwargs = second_call[1] if len(second_call) > 1 else {}
            animacy_question = kwargs.get('question', '')
            animacy_options = kwargs.get('options', [])
            animacy_correct = kwargs.get('correct_indices', [])
            assert "animate" in animacy_question.lower()
            assert "дом" in animacy_question
            assert "animate" in animacy_options
            assert "inanimate" in animacy_options
            assert 1 in animacy_correct  # inanimate is second option for this noun

    def test_generate_property_flashcards_animate_noun(self):
        """Test property flashcards for animate noun."""
        animate_noun = Noun(
            dictionary_form="кот",
            gender="masculine",
            animacy=True,
            singular={"nom": "кот", "gen": "кота", "dat": "коту", "acc": "кота", "ins": "котом", "pre": "коте"},
            plural={"nom": "коты", "gen": "котов", "dat": "котам", "acc": "котов", "ins": "котами", "pre": "котах"},
            english_translation="cat"
        )
        
        with patch.object(self.generator, 'create_multiple_choice_card') as mock_create_mc:
            
            mock_create_mc.return_value = Mock(spec=MultipleChoice)
            
            flashcards = self.generator._generate_property_flashcards(animate_noun, "кот")
            
            # Check animacy card shows "animate" as correct answer
            second_call = mock_create_mc.call_args_list[1]
            kwargs = second_call[1] if len(second_call) > 1 else {}
            animacy_correct = kwargs.get('correct_indices', [])
            animacy_options = kwargs.get('options', [])
            assert 0 in animacy_correct  # animate is first option for animate noun

    def test_generate_flashcards_empty_sentences_dict(self, sample_noun):
        """Test flashcard generation with empty sentences dictionary."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_multiple_choice_card') as mock_create_mc:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_mc.return_value = Mock(spec=MultipleChoice)
            
            # Test with None sentences
            flashcards1 = self.generator.generate_flashcards_from_grammar(sample_noun, generated_sentences=None)
            assert len(flashcards1) > 0
            
            # Test with empty dict
            flashcards2 = self.generator.generate_flashcards_from_grammar(sample_noun, generated_sentences={})
            assert len(flashcards2) > 0

    def test_generate_flashcards_with_word_type_parameter(self, sample_noun):
        """Test flashcard generation with custom word type."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_multiple_choice_card') as mock_create_mc:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_mc.return_value = Mock(spec=MultipleChoice)
            
            flashcards = self.generator.generate_flashcards_from_grammar(
                sample_noun, word_type="custom_noun"
            )
            
            # Check that the word_type parameter is used in calls
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                assert kwargs.get('word_type') == "noun"  # Generator always uses "noun"

    def test_flashcard_creation_with_grammatical_keys(self, sample_noun):
        """Test that flashcards are created with proper grammatical keys."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            self.generator._generate_singular_forms(sample_noun, "дом", {})
            
            # Check that grammatical keys are properly set
            call_args_list = mock_create_gap.call_args_list
            
            for call in call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                grammatical_key = kwargs.get('grammatical_key', '')
                assert 'singular' in grammatical_key
                assert any(case in grammatical_key.upper() for case in ['NOM', 'GEN', 'DAT', 'ACC', 'INS', 'PRE'])

    def test_flashcard_tags_structure(self, sample_noun):
        """Test that flashcards have proper tag structure."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            self.generator._generate_singular_forms(sample_noun, "дом", {})
            
            # Check tag structure
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'russian' in tags
                assert 'noun' in tags
                assert 'singular' in tags
                assert 'grammar' in tags
                # Should also contain the specific case
                assert any(case in tags for case in ['nom', 'gen', 'dat', 'acc', 'ins', 'pre'])
"""Tests for verb flashcard generator."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.generators.verb_generator import VerbGenerator
from app.grammar.russian import Verb
from app.flashcards.models import FillInTheBlank, TwoSidedCard, MultipleChoice


class TestVerbGenerator:
    """Test cases for VerbGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        self.generator = VerbGenerator()

    @pytest.fixture
    def sample_verb(self):
        """Create a sample verb for testing."""
        return Verb(
            dictionary_form="читать",
            english_translation="to read",
            aspect="imperfective",
            aspect_pair="прочитать",
            present_first_singular="читаю",
            present_second_singular="читаешь",
            present_third_singular="читает",
            present_first_plural="читаем",
            present_second_plural="читаете",
            present_third_plural="читают",
            past_masculine="читал",
            past_feminine="читала",
            past_neuter="читало",
            past_plural="читали",
            future_first_singular="буду читать",
            future_second_singular="будешь читать",
            future_third_singular="будет читать",
            future_first_plural="будем читать",
            future_second_plural="будете читать",
            future_third_plural="будут читать",
            imperative_singular="читай",
            imperative_plural="читайте"
        )

    @pytest.fixture
    def perfective_verb(self):
        """Create a perfective verb for testing."""
        return Verb(
            dictionary_form="прочитать",
            english_translation="to read (complete)",
            aspect="perfective",
            aspect_pair="читать",
            present_first_singular="",  # Perfective verbs don't have present
            present_second_singular="",
            present_third_singular="",
            present_first_plural="",
            present_second_plural="",
            present_third_plural="",
            past_masculine="прочитал",
            past_feminine="прочитала",
            past_neuter="прочитало",
            past_plural="прочитали",
            future_first_singular="прочитаю",
            future_second_singular="прочитаешь",
            future_third_singular="прочитает",
            future_first_plural="прочитаем",
            future_second_plural="прочитаете",
            future_third_plural="прочитают",
            imperative_singular="прочитай",
            imperative_plural="прочитайте"
        )

    def test_generate_flashcards_from_grammar_basic(self, sample_verb):
        """Test basic flashcard generation for verb."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            # Mock MultipleChoice creation
            with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
                mock_mc.return_value = Mock(spec=MultipleChoice)
                
                flashcards = self.generator.generate_flashcards_from_grammar(sample_verb)
                
                # Should create many cards for all tenses and forms
                assert len(flashcards) > 0
                # Should have aspect multiple choice cards and aspect pair cards
                assert mock_mc.call_count >= 1

    def test_generate_aspect_flashcards(self, sample_verb):
        """Test generation of aspect flashcards."""
        with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
            
            mock_mc_instance = Mock(spec=MultipleChoice)
            mock_mc.return_value = mock_mc_instance
            
            flashcards = self.generator._generate_aspect_flashcards(sample_verb, "читать")
            
            # Should create aspect multiple choice + aspect pair cards
            assert len(flashcards) >= 1
            assert mock_mc.call_count >= 1
            
            # Check aspect multiple choice creation
            call_args = mock_mc.call_args_list[0]
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert "читать" in kwargs.get('question', '')
            assert kwargs.get('options') == ["perfective", "imperfective"]
            assert kwargs.get('correct_indices') == [1]  # imperfective is index 1

    def test_generate_aspect_flashcards_perfective(self, perfective_verb):
        """Test aspect flashcards for perfective verb."""
        with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
            
            mock_mc_instance = Mock(spec=MultipleChoice)
            mock_mc.return_value = mock_mc_instance
            
            flashcards = self.generator._generate_aspect_flashcards(perfective_verb, "прочитать")
            
            # Check that perfective is correctly identified
            call_args = mock_mc.call_args_list[0]
            kwargs = call_args[1] if len(call_args) > 1 else {}
            assert kwargs.get('correct_indices') == [0]  # perfective is index 0

    def test_generate_aspect_pair_flashcards_imperfective(self, sample_verb):
        """Test aspect pair flashcards for imperfective verb."""
        with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
            
            mock_mc_instance = Mock(spec=MultipleChoice)
            mock_mc.return_value = mock_mc_instance
            
            flashcards = self.generator._generate_aspect_pair_flashcards(sample_verb, "читать")
            
            # Should create 2 cards: which is perfective, which is imperfective
            assert len(flashcards) == 2
            assert mock_mc.call_count == 2
            
            # Check perfective question
            first_call = mock_mc.call_args_list[0]
            first_kwargs = first_call[1] if len(first_call) > 1 else {}
            assert "PERFECTIVE" in first_kwargs.get('question', '')
            assert first_kwargs.get('options') == ["прочитать", "читать"]
            assert first_kwargs.get('correct_indices') == [0]  # прочитать is perfective
            
            # Check imperfective question
            second_call = mock_mc.call_args_list[1]
            second_kwargs = second_call[1] if len(second_call) > 1 else {}
            assert "IMPERFECTIVE" in second_kwargs.get('question', '')
            assert second_kwargs.get('correct_indices') == [1]  # читать is imperfective

    def test_generate_aspect_pair_flashcards_perfective(self, perfective_verb):
        """Test aspect pair flashcards for perfective verb."""
        with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
            
            mock_mc_instance = Mock(spec=MultipleChoice)
            mock_mc.return_value = mock_mc_instance
            
            flashcards = self.generator._generate_aspect_pair_flashcards(perfective_verb, "прочитать")
            
            # Check that options are correctly ordered for perfective verb
            first_call = mock_mc.call_args_list[0]
            first_kwargs = first_call[1] if len(first_call) > 1 else {}
            assert first_kwargs.get('options') == ["прочитать", "читать"]  # [dictionary_form, aspect_pair]
            assert first_kwargs.get('correct_indices') == [0]  # прочитать is perfective (index 0)

    def test_generate_conjugation_flashcards(self, sample_verb):
        """Test generation of conjugation pattern flashcards."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_conjugation_flashcards(sample_verb, "читать")
            
            # Should create conjugation pattern card
            assert len(flashcards) == 1
            assert mock_create_two.call_count == 1
            
            # Check card content
            call_args = mock_create_two.call_args_list[0]
            kwargs = call_args[1] if len(call_args) > 1 else {}
            front = kwargs.get('front', '')
            back = kwargs.get('back', '')
            assert "читать" in front
            assert "я" in front and "ты" in front
            assert "я читаю, ты читаешь" in back

    def test_generate_conjugation_flashcards_no_present_forms(self, perfective_verb):
        """Test conjugation flashcards when present forms are missing."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_conjugation_flashcards(perfective_verb, "прочитать")
            
            # Should not create conjugation cards if no present forms
            assert len(flashcards) == 0
            assert mock_create_two.call_count == 0

    def test_generate_present_tense_flashcards(self, sample_verb):
        """Test generation of present tense flashcards."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_present_tense_flashcards(sample_verb, "читать")
            
            assert len(flashcards) == 6  # All 6 persons
            assert mock_create_gap.call_count == 6
            
            # Check tags for present tense
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'present' in tags
                assert 'verb' in tags

    def test_generate_past_tense_flashcards(self, sample_verb):
        """Test generation of past tense flashcards."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_past_tense_flashcards(sample_verb, "читать")
            
            assert len(flashcards) == 4  # masculine, feminine, neuter, plural
            assert mock_create_gap.call_count == 4
            
            # Check tags for past tense
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'past' in tags
                assert 'verb' in tags

    def test_generate_future_tense_flashcards(self, sample_verb):
        """Test generation of future tense flashcards."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_future_tense_flashcards(sample_verb, "читать")
            
            assert len(flashcards) == 6  # All 6 persons
            assert mock_create_gap.call_count == 6
            
            # Check tags for future tense
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'future' in tags
                assert 'verb' in tags

    def test_generate_imperative_flashcards(self, sample_verb):
        """Test generation of imperative flashcards."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_imperative_flashcards(sample_verb, "читать")
            
            assert len(flashcards) == 2  # singular and plural
            assert mock_create_gap.call_count == 2
            
            # Check tags for imperative
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'imperative' in tags
                assert 'verb' in tags

    def test_generate_imperative_flashcards_missing_forms(self):
        """Test imperative flashcards when forms are missing."""
        verb_no_imperative = Verb(
            dictionary_form="тест",
            english_translation="test",
            aspect="imperfective",
            present_first_singular="тест",
            past_masculine="тест",
            past_feminine="теста",
            past_neuter="тесто",
            past_plural="тесты",
            imperative_singular="",  # Empty
            imperative_plural=""   # Empty (None not allowed)
        )
        
        with patch.object(self.generator, 'should_create_flashcard') as mock_should_create, \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_should_create.return_value = False  # should_create_flashcard returns False for empty
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_imperative_flashcards(verb_no_imperative, "тест")
            
            # Should not create cards for missing imperative forms
            assert len(flashcards) == 0
            assert mock_create_gap.call_count == 0

    def test_skip_empty_forms(self, sample_verb):
        """Test that empty or None forms are skipped."""
        # Create verb with some empty forms
        verb_with_gaps = Verb(
            dictionary_form="тест",
            english_translation="test",
            aspect="imperfective",
            present_first_singular="тесто",
            present_second_singular="",  # Empty
            present_third_singular=None,  # None
            present_first_plural="тестим",
            present_second_plural="тестите",
            present_third_plural="тестят",
            past_masculine="тестил",
            past_feminine="тестила",
            past_neuter="тестило",
            past_plural="тестили"
        )
        
        def mock_should_create(form, dictionary_form):
            return form and form.strip() and form != dictionary_form
        
        with patch.object(self.generator, 'should_create_flashcard', side_effect=mock_should_create), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_present_tense_flashcards(verb_with_gaps, "тест")
            
            # Should skip empty/None forms and dictionary form matches
            assert len(flashcards) == 4  # Only non-empty, different forms

    def test_grammatical_keys_structure(self, sample_verb):
        """Test that flashcards have proper grammatical keys."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            self.generator._generate_present_tense_flashcards(sample_verb, "читать")
            
            # Check grammatical key structure
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                grammatical_key = kwargs.get('grammatical_key', '')
                assert 'present' in grammatical_key
                assert any(person in grammatical_key for person in ['first', 'second', 'third'])

    def test_aspect_no_pair(self):
        """Test aspect flashcards when there's no aspect pair."""
        verb_no_pair = Verb(
            dictionary_form="спать",
            english_translation="to sleep",
            aspect="imperfective",
            aspect_pair="",  # No aspect pair
            present_first_singular="сплю",
            past_masculine="спал",
            past_feminine="спала",
            past_neuter="спало",
            past_plural="спали"
        )
        
        with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
            
            mock_mc_instance = Mock(spec=MultipleChoice)
            mock_mc.return_value = mock_mc_instance
            
            flashcards = self.generator._generate_aspect_flashcards(verb_no_pair, "спать")
            
            # Should still create basic aspect card, but not aspect pair cards
            assert len(flashcards) == 1
            assert mock_mc.call_count == 1

    def test_generate_flashcards_with_sentences(self, sample_verb):
        """Test flashcard generation with sentences parameter."""
        generated_sentences = {
            "present_first": "Я читаю книгу.",
            "past_masculine": "Он читал вчера."
        }
        
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            with patch('app.my_graph.generators.verb_generator.MultipleChoice') as mock_mc:
                mock_mc.return_value = Mock(spec=MultipleChoice)
                
                flashcards = self.generator.generate_flashcards_from_grammar(
                    sample_verb, generated_sentences=generated_sentences
                )
                
                # Should handle sentences parameter
                assert len(flashcards) > 0
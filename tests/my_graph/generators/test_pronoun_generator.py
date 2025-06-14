"""Tests for pronoun flashcard generator."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.generators.pronoun_generator import PronounGenerator
from app.grammar.russian import Pronoun
from app.flashcards.models import FillInTheBlank, TwoSidedCard


class TestPronounGenerator:
    """Test cases for PronounGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        self.generator = PronounGenerator()

    @pytest.fixture
    def personal_pronoun(self):
        """Create a personal pronoun for testing (noun-like declension)."""
        return Pronoun(
            dictionary_form="я",
            english_translation="I",
            singular={
                "nom": "я",
                "gen": "меня",
                "dat": "мне",
                "acc": "меня",
                "ins": "мной",
                "pre": "мне"
            },
            plural={
                "nom": "мы",
                "gen": "нас",
                "dat": "нам",
                "acc": "нас",
                "ins": "нами",
                "pre": "нас"
            }
        )

    @pytest.fixture
    def demonstrative_pronoun(self):
        """Create a demonstrative pronoun for testing (adjective-like declension)."""
        return Pronoun(
            dictionary_form="этот",
            english_translation="this",
            masculine={
                "nom": "этот",
                "gen": "этого",
                "dat": "этому",
                "acc": "этот",
                "ins": "этим",
                "pre": "этом"
            },
            feminine={
                "nom": "эта",
                "gen": "этой",
                "dat": "этой",
                "acc": "эту",
                "ins": "этой",
                "pre": "этой"
            },
            neuter={
                "nom": "это",
                "gen": "этого",
                "dat": "этому",
                "acc": "это",
                "ins": "этим",
                "pre": "этом"
            },
            plural_adjective_like={
                "nom": "эти",
                "gen": "этих",
                "dat": "этим",
                "acc": "эти",
                "ins": "этими",
                "pre": "этих"
            }
        )

    @pytest.fixture
    def special_pronoun(self):
        """Create a special/irregular pronoun for testing."""
        return Pronoun(
            dictionary_form="себя",
            english_translation="oneself",
            notes="Reflexive pronoun, no nominative form"
        )

    def test_generate_flashcards_from_grammar_personal(self, personal_pronoun):
        """Test flashcard generation for personal pronoun."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(personal_pronoun)
            
            # Should create cards for singular and plural forms plus property cards
            assert len(flashcards) > 0
            # Should create property cards (translation)
            assert mock_create_two.call_count >= 1

    def test_generate_flashcards_from_grammar_demonstrative(self, demonstrative_pronoun):
        """Test flashcard generation for demonstrative pronoun."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(demonstrative_pronoun)
            
            # Should create cards for all gender forms plus property cards
            assert len(flashcards) > 0
            # Should have many gap-fill cards for gender/case combinations
            assert mock_create_gap.call_count > 20  # Many forms

    def test_generate_flashcards_from_grammar_special(self, special_pronoun):
        """Test flashcard generation for special pronoun."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(special_pronoun)
            
            # Should create at least property cards
            assert len(flashcards) > 0
            assert mock_create_two.call_count >= 1

    def test_generate_noun_like_forms(self, personal_pronoun):
        """Test generation of noun-like forms."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_noun_like_forms(personal_pronoun, "я")
            
            assert len(flashcards) == 12  # 6 singular + 6 plural cases
            assert mock_create_gap.call_count == 12
            
            # Check tags for personal pronouns
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'pronoun' in tags
                assert 'personal' in tags

    def test_generate_noun_like_forms_singular_only(self):
        """Test noun-like forms with only singular declension."""
        singular_only_pronoun = Pronoun(
            dictionary_form="кто",
            english_translation="who",
            singular={
                "nom": "кто",
                "gen": "кого",
                "dat": "кому",
                "acc": "кого",
                "ins": "кем",
                "pre": "ком"
            }
        )
        
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_noun_like_forms(singular_only_pronoun, "кто")
            
            assert len(flashcards) == 6  # Only singular cases
            assert mock_create_gap.call_count == 6

    def test_generate_adjective_like_forms(self, demonstrative_pronoun):
        """Test generation of adjective-like forms."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_adjective_like_forms(demonstrative_pronoun, "этот")
            
            assert len(flashcards) == 24  # 6 cases × 4 genders (m, f, n, pl)
            assert mock_create_gap.call_count == 24
            
            # Check tags for demonstrative pronouns
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'pronoun' in tags
                assert 'demonstrative' in tags

    def test_generate_adjective_like_forms_partial(self):
        """Test adjective-like forms with only some genders."""
        partial_pronoun = Pronoun(
            dictionary_form="тест",
            english_translation="test",
            masculine={
                "nom": "тест",
                "gen": "теста"
            },
            feminine={
                "nom": "теста",
                "gen": "тестой"
            }
            # No neuter or plural_adjective_like
        )
        
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_adjective_like_forms(partial_pronoun, "тест")
            
            assert len(flashcards) == 4  # 2 masculine + 2 feminine cases
            assert mock_create_gap.call_count == 4

    def test_generate_special_forms_with_singular(self):
        """Test special forms when singular is available."""
        special_with_singular = Pronoun(
            dictionary_form="что",
            english_translation="what",
            singular={
                "nom": "что",
                "gen": "чего",
                "dat": "чему",
                "acc": "что",
                "ins": "чем",
                "pre": "чём"
            }
        )
        
        with patch.object(self.generator, '_generate_noun_like_forms') as mock_noun_like:
            
            mock_noun_like.return_value = [Mock(spec=FillInTheBlank)]
            
            flashcards = self.generator._generate_special_forms(special_with_singular, "что")
            
            # Should delegate to noun-like forms
            assert len(flashcards) == 1
            mock_noun_like.assert_called_once_with(special_with_singular, "что", 1)

    def test_generate_special_forms_with_gender(self):
        """Test special forms when gender forms are available."""
        special_with_gender = Pronoun(
            dictionary_form="какой",
            english_translation="which",
            masculine={
                "nom": "какой",
                "gen": "какого"
            }
        )
        
        with patch.object(self.generator, '_generate_adjective_like_forms') as mock_adj_like:
            
            mock_adj_like.return_value = [Mock(spec=FillInTheBlank)]
            
            flashcards = self.generator._generate_special_forms(special_with_gender, "какой")
            
            # Should delegate to adjective-like forms
            assert len(flashcards) == 1
            mock_adj_like.assert_called_once_with(special_with_gender, "какой", 1)

    def test_generate_special_forms_irregular(self, special_pronoun):
        """Test special forms for truly irregular pronouns."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_special_forms(special_pronoun, "себя")
            
            # Should create basic translation card
            assert len(flashcards) == 1
            assert mock_create_two.call_count == 1
            
            # Check card content
            call_args = mock_create_two.call_args_list[0]
            kwargs = call_args[1] if len(call_args) > 1 else {}
            front = kwargs.get('front', '')
            back = kwargs.get('back', '')
            assert "себя" in front
            assert back == "oneself"

    def test_generate_property_flashcards(self, personal_pronoun):
        """Test generation of property flashcards."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(personal_pronoun, "я")
            
            assert len(flashcards) == 1  # Only translation card (no notes)
            assert mock_create_two.call_count == 1
            
            # Check translation card
            call_args = mock_create_two.call_args_list[0]
            kwargs = call_args[1] if len(call_args) > 1 else {}
            front = kwargs.get('front', '')
            back = kwargs.get('back', '')
            assert "я" in front
            assert "English" in front
            assert back == "I"

    def test_generate_property_flashcards_with_notes(self, special_pronoun):
        """Test property flashcards with notes."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(special_pronoun, "себя")
            
            assert len(flashcards) == 2  # Translation + notes cards
            assert mock_create_two.call_count == 2
            
            # Check notes card
            second_call = mock_create_two.call_args_list[1]
            second_kwargs = second_call[1] if len(second_call) > 1 else {}
            notes_front = second_kwargs.get('front', '')
            notes_back = second_kwargs.get('back', '')
            assert "notes" in notes_front.lower()
            assert "себя" in notes_front
            assert "Reflexive pronoun" in notes_back

    def test_skip_identical_forms(self, personal_pronoun):
        """Test that forms identical to dictionary form are skipped."""
        def mock_should_create(form, dictionary_form):
            return form != dictionary_form  # Skip identical forms
        
        with patch.object(self.generator, 'should_create_flashcard', side_effect=mock_should_create), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_noun_like_forms(personal_pronoun, "я")
            
            # Should skip nominative singular "я" but include all others
            assert len(flashcards) == 11  # All except nom singular
            assert mock_create_gap.call_count == 11

    def test_grammatical_keys_structure(self, personal_pronoun):
        """Test that flashcards have proper grammatical keys."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            self.generator._generate_noun_like_forms(personal_pronoun, "я")
            
            # Check grammatical key structure
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                grammatical_key = kwargs.get('grammatical_key', '')
                assert 'case' in grammatical_key or any(case in grammatical_key.upper() for case in ['NOM', 'GEN', 'DAT', 'ACC', 'INS', 'PRE'])

    def test_tag_structure_comprehensive(self, personal_pronoun, demonstrative_pronoun):
        """Test comprehensive tag structure across different pronoun types."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            # Test both pronoun types
            self.generator._generate_noun_like_forms(personal_pronoun, "я")
            self.generator._generate_adjective_like_forms(demonstrative_pronoun, "этот")
            
            # Check that all calls have proper base tags
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'russian' in tags
                assert 'pronoun' in tags

    def test_generate_flashcards_with_sentences(self, personal_pronoun):
        """Test flashcard generation with sentences parameter."""
        generated_sentences = {
            "gen_singular": "У меня есть книга.",
            "dat_singular": "Мне нравится читать."
        }
        
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(
                personal_pronoun, generated_sentences=generated_sentences
            )
            
            # Should handle sentences parameter
            assert len(flashcards) > 0

    def test_empty_notes_handling(self):
        """Test handling of empty or None notes."""
        pronoun_empty_notes = Pronoun(
            dictionary_form="он",
            english_translation="he",
            singular={"nom": "он", "gen": "его"},
            notes=""  # Empty notes
        )
        
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(pronoun_empty_notes, "он")
            
            # Should only create translation card, not notes card
            assert len(flashcards) == 1
            assert mock_create_two.call_count == 1
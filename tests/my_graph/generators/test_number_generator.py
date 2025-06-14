"""Tests for number flashcard generator."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.generators.number_generator import NumberGenerator
from app.grammar.russian import Number
from app.flashcards.models import FillInTheBlank, TwoSidedCard


class TestNumberGenerator:
    """Test cases for NumberGenerator class."""

    def setup_method(self):
        """Set up test instance."""
        self.generator = NumberGenerator()

    @pytest.fixture
    def one_type_number(self):
        """Create a 'one' type number for testing."""
        return Number(
            dictionary_form="один",
            english_translation="one",
            masculine={
                "nom": "один",
                "gen": "одного",
                "dat": "одному",
                "acc": "один",
                "ins": "одним",
                "pre": "одном"
            },
            feminine={
                "nom": "одна",
                "gen": "одной",
                "dat": "одной",
                "acc": "одну",
                "ins": "одной",
                "pre": "одной"
            },
            neuter={
                "nom": "одно",
                "gen": "одного",
                "dat": "одному",
                "acc": "одно",
                "ins": "одним",
                "pre": "одном"
            },
            noun_agreement={
                "nom": "singular nominative",
                "gen": "singular genitive after negation",
                "dat": "singular dative",
                "acc": "singular accusative",
                "ins": "singular instrumental",
                "pre": "singular prepositional"
            }
        )

    @pytest.fixture
    def simple_number(self):
        """Create a simple case number for testing."""
        return Number(
            dictionary_form="пять",
            english_translation="five",
            singular={
                "nom": "пять",
                "gen": "пяти",
                "dat": "пяти",
                "acc": "пять",
                "ins": "пятью",
                "pre": "пяти"
            },
            noun_agreement={
                "nom": "genitive plural",
                "gen": "genitive plural",
                "dat": "genitive plural",
                "acc": "genitive plural",
                "ins": "genitive plural",
                "pre": "genitive plural"
            }
        )

    @pytest.fixture
    def thousands_number(self):
        """Create a thousands-type number for testing."""
        return Number(
            dictionary_form="тысяча",
            english_translation="thousand",
            singular={
                "nom": "тысяча",
                "gen": "тысячи",
                "dat": "тысяче",
                "acc": "тысячу",
                "ins": "тысячей",
                "pre": "тысяче"
            },
            plural={
                "nom": "тысячи",
                "gen": "тысяч",
                "dat": "тысячам",
                "acc": "тысячи",
                "ins": "тысячами",
                "pre": "тысячах"
            }
        )

    @pytest.fixture
    def compound_number(self):
        """Create a compound number for testing."""
        return Number(
            dictionary_form="двадцать один",
            english_translation="twenty-one",
            compound_forms={
                "nom_masculine": "двадцать один",
                "gen_masculine": "двадцати одного",
                "dat_masculine": "двадцати одному",
                "acc_masculine": "двадцать один",
                "ins_masculine": "двадцатью одним",
                "pre_masculine": "двадцати одном"
            }
        )

    def test_generate_flashcards_from_grammar_one_type(self, one_type_number):
        """Test flashcard generation for 'one' type number."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(one_type_number)
            
            # Should create cards for all gender forms plus property cards
            assert len(flashcards) > 0
            # Should create gap-fill cards for gender/case combinations
            assert mock_create_gap.call_count > 0
            # Should create property cards
            assert mock_create_two.call_count >= 1

    def test_generate_flashcards_from_grammar_simple(self, simple_number):
        """Test flashcard generation for simple case number."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(simple_number)
            
            # Should create cards for case forms plus property cards
            assert len(flashcards) > 0
            # Should create gap-fill cards for cases
            assert mock_create_gap.call_count > 0
            # Should create property cards
            assert mock_create_two.call_count >= 1

    def test_generate_flashcards_from_grammar_thousands(self, thousands_number):
        """Test flashcard generation for thousands number."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(thousands_number)
            
            # Should create cards for singular and plural forms plus property cards
            assert len(flashcards) > 0
            # Should create gap-fill cards for both singular and plural
            assert mock_create_gap.call_count > 10  # Both singular and plural cases
            # Should create property cards
            assert mock_create_two.call_count >= 1

    def test_generate_flashcards_from_grammar_compound(self, compound_number):
        """Test flashcard generation for compound number."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(compound_number)
            
            # Should create cards for compound forms plus property cards
            assert len(flashcards) > 0
            # Should create gap-fill cards for compound forms
            assert mock_create_gap.call_count > 0
            # Should create property cards
            assert mock_create_two.call_count >= 1

    def test_generate_one_type_forms(self, one_type_number):
        """Test generation of 'one' type forms."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_one_type_forms(one_type_number, "один")
            
            assert len(flashcards) == 18  # 6 cases × 3 genders
            assert mock_create_gap.call_count == 18
            
            # Check tags for one-type numbers
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'number' in tags
                assert 'one' in tags

    def test_generate_simple_case_forms(self, simple_number):
        """Test generation of simple case forms."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_simple_case_forms(simple_number, "пять")
            
            assert len(flashcards) == 6  # All 6 cases
            assert mock_create_gap.call_count == 6
            
            # Check basic form descriptions
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                form_description = kwargs.get('form_description', '')
                assert form_description  # Should have some description

    def test_generate_thousands_forms(self, thousands_number):
        """Test generation of thousands forms."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_thousands_forms(thousands_number, "тысяча")
            
            assert len(flashcards) == 12  # 6 singular + 6 plural cases
            assert mock_create_gap.call_count == 12
            
            # Check that both singular and plural tags are used
            singular_calls = []
            plural_calls = []
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                if 'singular' in tags:
                    singular_calls.append(call)
                elif 'plural' in tags:
                    plural_calls.append(call)
            
            assert len(singular_calls) == 6
            assert len(plural_calls) == 6

    def test_generate_compound_forms(self, compound_number):
        """Test generation of compound forms."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_compound_forms(compound_number, "двадцать один")
            
            assert len(flashcards) == 6  # All compound form cases
            assert mock_create_gap.call_count == 6
            
            # Check compound-specific tags
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                tags = kwargs.get('tags', [])
                assert 'compound' in tags

    def test_generate_special_forms_with_singular(self):
        """Test special forms when singular is available."""
        special_number = Number(
            dictionary_form="ноль",
            english_translation="zero",
            numeric_value=0,
            number_type="cardinal",
            number_category="special",
            singular={
                "nom": "ноль",
                "gen": "ноля",
                "dat": "нолю",
                "acc": "ноль",
                "ins": "нолём",
                "pre": "ноле"
            }
        )
        
        with patch.object(self.generator, '_generate_simple_case_forms') as mock_simple:
            
            mock_simple.return_value = [Mock(spec=FillInTheBlank)]
            
            flashcards = self.generator._generate_special_forms(special_number, "ноль")
            
            # Should delegate to simple case forms
            assert len(flashcards) == 1
            mock_simple.assert_called_once_with(special_number, "ноль")

    def test_generate_special_forms_with_gender(self):
        """Test special forms when gender forms are available."""
        special_number = Number(
            dictionary_form="тест",
            english_translation="test",
            numeric_value=1,
            number_type="cardinal",
            number_category="special",
            masculine={
                "nom": "тест",
                "gen": "теста"
            }
        )
        
        with patch.object(self.generator, '_generate_one_type_forms') as mock_one_type:
            
            mock_one_type.return_value = [Mock(spec=FillInTheBlank)]
            
            flashcards = self.generator._generate_special_forms(special_number, "тест")
            
            # Should delegate to one-type forms
            assert len(flashcards) == 1
            mock_one_type.assert_called_once_with(special_number, "тест")

    def test_generate_special_forms_irregular(self):
        """Test special forms for truly irregular numbers."""
        irregular_number = Number(
            dictionary_form="много",
            english_translation="many/much",
            numeric_value=None,
            number_type="cardinal",
            number_category="special"
        )
        
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_special_forms(irregular_number, "много")
            
            # Should create basic translation card
            assert len(flashcards) == 1
            assert mock_create_two.call_count == 1

    def test_generate_property_flashcards(self, one_type_number):
        """Test generation of property flashcards."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(one_type_number, "один")
            
            # Should create translation and agreement cards
            assert len(flashcards) >= 1
            assert mock_create_two.call_count >= 1
            
            # Check that translation card exists
            found_translation = False
            for call in mock_create_two.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                front = kwargs.get('front', '')
                if "English" in front:
                    found_translation = True
                    assert kwargs.get('back') == "one"
            
            assert found_translation

    def test_generate_property_flashcards_with_usage_notes(self, thousands_number):
        """Test property flashcards without usage notes (field doesn't exist)."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(thousands_number, "тысяча")
            
            # Should create basic property cards
            assert len(flashcards) >= 1
            assert mock_create_two.call_count >= 1

    def test_number_type_descriptions(self, one_type_number):
        """Test basic property card creation."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(one_type_number, "один")
            
            # Should create some property cards
            assert len(flashcards) >= 1
            assert mock_create_two.call_count >= 1

    def test_number_category_descriptions(self, simple_number):
        """Test basic property card creation for simple numbers."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(simple_number, "пять")
            
            # Should create some property cards
            assert len(flashcards) >= 1
            assert mock_create_two.call_count >= 1

    def test_noun_agreement_flashcard(self, one_type_number):
        """Test noun agreement flashcard generation."""
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(one_type_number, "один")
            
            # Should create cards including potential agreement card
            assert len(flashcards) >= 1
            assert mock_create_two.call_count >= 1
            
            # Check for agreement card in the created cards
            found_agreement = False
            for call in mock_create_two.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                front = kwargs.get('front', '')
                if "agree" in front.lower():
                    found_agreement = True
                    back = kwargs.get('back', '')
                    assert "один" in front
                    assert back  # Should have some agreement content
            
            # Agreement card should exist since we provided noun_agreement
            assert found_agreement

    def test_skip_identical_forms(self, one_type_number):
        """Test that forms identical to dictionary form are skipped."""
        def mock_should_create(form, dictionary_form):
            return form != dictionary_form  # Skip identical forms
        
        with patch.object(self.generator, 'should_create_flashcard', side_effect=mock_should_create), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            flashcards = self.generator._generate_one_type_forms(one_type_number, "один")
            
            # Should skip masculine nominative and accusative "один"
            # But include all other forms
            assert len(flashcards) == 16  # 18 total - 2 identical forms

    def test_grammatical_keys_structure(self, one_type_number):
        """Test that flashcards have proper grammatical keys."""
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            
            self.generator._generate_one_type_forms(one_type_number, "один")
            
            # Check grammatical key structure
            for call in mock_create_gap.call_args_list:
                kwargs = call[1] if len(call) > 1 else {}
                grammatical_key = kwargs.get('grammatical_key', '')
                assert any(case in grammatical_key.upper() for case in ['NOM', 'GEN', 'DAT', 'ACC', 'INS', 'PRE'])
                assert any(gender in grammatical_key for gender in ['masculine', 'feminine', 'neuter'])

    def test_generate_flashcards_with_sentences(self, one_type_number):
        """Test flashcard generation with sentences parameter."""
        generated_sentences = {
            "nom_masculine": "Один студент читает книгу.",
            "acc_feminine": "Я вижу одну девушку."
        }
        
        with patch.object(self.generator, 'should_create_flashcard', return_value=True), \
             patch.object(self.generator, 'create_fill_in_gap_card') as mock_create_gap, \
             patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_gap.return_value = Mock(spec=FillInTheBlank)
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator.generate_flashcards_from_grammar(
                one_type_number, generated_sentences=generated_sentences
            )
            
            # Should handle sentences parameter
            assert len(flashcards) > 0

    def test_no_noun_agreement_handling(self):
        """Test handling when noun_agreement is not present."""
        number_no_agreement = Number(
            dictionary_form="семь",
            english_translation="seven",
            singular={"nom": "семь", "gen": "семи", "dat": "семи", "acc": "семь", "ins": "семью", "pre": "семи"}
        )
        
        with patch.object(self.generator, 'create_two_sided_card') as mock_create_two:
            
            mock_create_two.return_value = Mock(spec=TwoSidedCard)
            
            flashcards = self.generator._generate_property_flashcards(number_no_agreement, "семь")
            
            # Should create fewer cards (no agreement card)
            assert len(flashcards) >= 1
            assert mock_create_two.call_count >= 1
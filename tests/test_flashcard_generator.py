"""Tests for flashcard generation functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.my_graph.flashcard_generator import FlashcardGenerator
from app.my_graph.generators.base_generator import BaseGenerator
from app.my_graph.generators.noun_generator import NounGenerator
from app.flashcards.models import TwoSidedCard, FillInTheBlank, MultipleChoice, FlashcardType
from app.grammar.russian import Noun, Adjective, Verb, Pronoun, Number


class TestFlashcardGenerator:
    """Test the main FlashcardGenerator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.generator = FlashcardGenerator()
    
    def test_flashcard_generator_initialization(self):
        """Test FlashcardGenerator initializes with all sub-generators."""
        generator = FlashcardGenerator()
        
        assert hasattr(generator, 'noun_generator')
        assert hasattr(generator, 'adjective_generator')
        assert hasattr(generator, 'verb_generator')
        assert hasattr(generator, 'pronoun_generator')
        assert hasattr(generator, 'number_generator')
        assert hasattr(generator, 'service')
    
    @patch('app.my_graph.flashcard_generator.flashcard_service')
    def test_save_flashcards_to_database_success(self, mock_service):
        """Test successfully saving flashcards to database."""
        generator = FlashcardGenerator()
        
        # Mock successful database saves
        mock_service.db.add_flashcard.return_value = "mock_id_123"
        
        # Create test flashcards
        flashcards = [
            TwoSidedCard(front="Test 1", back="Answer 1", title="Card 1"),
            TwoSidedCard(front="Test 2", back="Answer 2", title="Card 2"),
            TwoSidedCard(front="Test 3", back="Answer 3", title="Card 3")
        ]
        
        # Save flashcards
        saved_count = generator.save_flashcards_to_database(flashcards)
        
        # Verify results
        assert saved_count == 3
        assert mock_service.db.add_flashcard.call_count == 3
    
    @patch('app.my_graph.flashcard_generator.flashcard_service')
    def test_save_flashcards_to_database_partial_failure(self, mock_service):
        """Test saving flashcards with some failures."""
        generator = FlashcardGenerator()
        
        # Mock database - first save succeeds, second fails, third succeeds
        mock_service.db.add_flashcard.side_effect = ["id1", None, "id3"]
        
        flashcards = [
            TwoSidedCard(front="Test 1", back="Answer 1", title="Card 1"),
            TwoSidedCard(front="Test 2", back="Answer 2", title="Card 2"),
            TwoSidedCard(front="Test 3", back="Answer 3", title="Card 3")
        ]
        
        saved_count = generator.save_flashcards_to_database(flashcards)
        
        assert saved_count == 2  # Only 2 out of 3 saved successfully
    
    @patch('app.my_graph.flashcard_generator.flashcard_service')
    def test_save_flashcards_to_database_exception(self, mock_service):
        """Test handling exceptions during flashcard saving."""
        generator = FlashcardGenerator()
        
        # Mock database to raise exception
        mock_service.db.add_flashcard.side_effect = Exception("Database error")
        
        flashcards = [
            TwoSidedCard(front="Test", back="Answer", title="Card")
        ]
        
        # Should handle exception gracefully and return 0
        saved_count = generator.save_flashcards_to_database(flashcards)
        assert saved_count == 0
    
    def test_generate_flashcards_from_grammar_noun(self):
        """Test generating flashcards for a noun."""
        generator = FlashcardGenerator()
        
        # Create mock noun
        mock_noun = Mock(spec=Noun)
        mock_noun.dictionary_form = "дом"
        
        # Mock the noun generator
        with patch.object(generator.noun_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.return_value = [
                TwoSidedCard(front="Test", back="Answer", title="Noun card")
            ]
            
            flashcards = generator.generate_flashcards_from_grammar(mock_noun, "noun")
            
            assert len(flashcards) == 1
            assert isinstance(flashcards[0], TwoSidedCard)
            mock_gen.assert_called_once_with(mock_noun, "noun", None)
    
    def test_generate_flashcards_from_grammar_adjective(self):
        """Test generating flashcards for an adjective."""
        generator = FlashcardGenerator()
        
        mock_adjective = Mock(spec=Adjective)
        mock_adjective.dictionary_form = "красивый"
        
        with patch.object(generator.adjective_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.return_value = []
            
            flashcards = generator.generate_flashcards_from_grammar(mock_adjective, "adjective")
            
            assert flashcards == []
            mock_gen.assert_called_once_with(mock_adjective, "adjective", None)
    
    def test_generate_flashcards_from_grammar_verb(self):
        """Test generating flashcards for a verb."""
        generator = FlashcardGenerator()
        
        mock_verb = Mock(spec=Verb)
        mock_verb.dictionary_form = "читать"
        
        with patch.object(generator.verb_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.return_value = [Mock(), Mock()]
            
            flashcards = generator.generate_flashcards_from_grammar(mock_verb, "verb")
            
            assert len(flashcards) == 2
            mock_gen.assert_called_once_with(mock_verb, "verb", None)
    
    def test_generate_flashcards_from_grammar_pronoun(self):
        """Test generating flashcards for a pronoun."""
        generator = FlashcardGenerator()
        
        mock_pronoun = Mock(spec=Pronoun)
        
        with patch.object(generator.pronoun_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.return_value = [Mock()]
            
            flashcards = generator.generate_flashcards_from_grammar(mock_pronoun, "pronoun")
            
            assert len(flashcards) == 1
            mock_gen.assert_called_once()
    
    def test_generate_flashcards_from_grammar_number(self):
        """Test generating flashcards for a number."""
        generator = FlashcardGenerator()
        
        mock_number = Mock(spec=Number)
        
        with patch.object(generator.number_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.return_value = []
            
            flashcards = generator.generate_flashcards_from_grammar(mock_number, "number")
            
            assert flashcards == []
            mock_gen.assert_called_once()
    
    def test_generate_flashcards_from_grammar_unknown_type(self):
        """Test handling unknown grammar object types."""
        generator = FlashcardGenerator()
        
        # Pass an unknown object type
        unknown_obj = Mock()
        
        with patch('app.my_graph.flashcard_generator.logger') as mock_logger:
            flashcards = generator.generate_flashcards_from_grammar(unknown_obj, "unknown")
            
            assert flashcards == []
            mock_logger.warning.assert_called_once()
    
    def test_generate_flashcards_from_grammar_with_sentences(self):
        """Test generating flashcards with pre-generated sentences."""
        generator = FlashcardGenerator()
        
        mock_noun = Mock(spec=Noun)
        sentences = {"nominative_singular": "Это дом.", "genitive_singular": "У меня нет дома."}
        
        with patch.object(generator.noun_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.return_value = []
            
            generator.generate_flashcards_from_grammar(mock_noun, "noun", sentences)
            
            mock_gen.assert_called_once_with(mock_noun, "noun", sentences)
    
    def test_generate_flashcards_from_grammar_exception_handling(self):
        """Test exception handling in flashcard generation."""
        generator = FlashcardGenerator()
        
        mock_noun = Mock(spec=Noun)
        
        with patch.object(generator.noun_generator, 'generate_flashcards_from_grammar') as mock_gen:
            mock_gen.side_effect = Exception("Generation error")
            
            with patch('app.my_graph.flashcard_generator.logger') as mock_logger:
                flashcards = generator.generate_flashcards_from_grammar(mock_noun, "noun")
                
                assert flashcards == []
                mock_logger.error.assert_called_once()


class TestBaseGenerator:
    """Test the BaseGenerator base class."""
    
    def test_base_generator_initialization(self):
        """Test BaseGenerator initializes with required components."""
        generator = BaseGenerator()
        
        assert hasattr(generator, 'sentence_generator')
        assert hasattr(generator, 'text_processor')
        assert hasattr(generator, 'suffix_extractor')
        assert hasattr(generator, 'form_analyzer')
    
    def test_create_two_sided_card(self):
        """Test creating a two-sided flashcard."""
        generator = BaseGenerator()
        
        card = generator.create_two_sided_card(
            front="What is 'дом'?",
            back="house",
            tags=["vocabulary", "nouns"],
            title="дом translation"
        )
        
        assert isinstance(card, TwoSidedCard)
        assert card.front == "What is 'дом'?"
        assert card.back == "house"
        assert card.tags == ["vocabulary", "nouns"]
        assert card.title == "дом translation"
        assert card.type == FlashcardType.TWO_SIDED
    
    @patch('app.my_graph.generators.base_generator.LLMSentenceGenerator')
    @patch('app.my_graph.generators.base_generator.TextProcessor')
    @patch('app.my_graph.generators.base_generator.SuffixExtractor')
    def test_create_fill_in_gap_card(self, mock_suffix_extractor, mock_text_processor, mock_sentence_generator):
        """Test creating a fill-in-the-gap flashcard."""
        generator = BaseGenerator()
        
        # Mock the dependencies
        mock_sentence_generator.return_value.generate_example_sentence.return_value = "Я читаю книгу дома."
        mock_suffix_extractor.return_value.extract_suffix.return_value = ("дом", "а")
        mock_text_processor.return_value.create_sentence_with_blank.return_value = "Я читаю книгу дом{blank}."
        
        card = generator.create_fill_in_gap_card(
            dictionary_form="дом",
            target_form="дома",
            form_description="GENITIVE singular",
            word_type="noun",
            tags=["grammar", "cases"],
            grammatical_key="genitive_singular"
        )
        
        assert isinstance(card, FillInTheBlank)
        assert card.text_with_blanks == "Я читаю книгу дом{blank}."
        assert card.answers == ["а"]
        assert card.case_sensitive == False
        assert "fill_in_gap" in card.tags
        assert "suffix" in card.tags
        assert "grammar" in card.tags
        assert card.title == "дом - GENITIVE singular (gap fill)"
        assert card.metadata["form_description"] == "GENITIVE singular"
        assert card.metadata["dictionary_form"] == "дом"
    
    @patch('app.my_graph.generators.base_generator.LLMSentenceGenerator')
    def test_create_fill_in_gap_card_with_pre_generated_sentence(self, mock_sentence_generator):
        """Test creating fill-in-gap card with pre-generated sentence."""
        generator = BaseGenerator()
        
        # Mock other dependencies
        with patch.object(generator.suffix_extractor, 'extract_suffix') as mock_suffix:
            with patch.object(generator.text_processor, 'create_sentence_with_blank') as mock_blank:
                mock_suffix.return_value = ("кот", "а")
                mock_blank.return_value = "У меня есть кот{blank}."
                
                card = generator.create_fill_in_gap_card(
                    dictionary_form="кот",
                    target_form="кота", 
                    form_description="GENITIVE singular",
                    word_type="noun",
                    tags=["test"],
                    pre_generated_sentence="У меня есть кота."
                )
                
                # Should not call sentence generator since we provided pre-generated sentence
                mock_sentence_generator.return_value.generate_example_sentence.assert_not_called()
                assert card.text_with_blanks == "У меня есть кот{blank}."
    
    def test_should_create_flashcard(self):
        """Test logic for determining when to create flashcards."""
        generator = BaseGenerator()
        
        # Should create flashcard when form differs from dictionary form
        assert generator.should_create_flashcard("дома", "дом") == True
        assert generator.should_create_flashcard("красивая", "красивый") == True
        
        # Should not create flashcard when forms are the same
        assert generator.should_create_flashcard("дом", "дом") == False
        assert generator.should_create_flashcard("ДОМ", "дом") == False  # case insensitive
        
        # Should return falsy values for empty/None forms (not necessarily False)
        result_empty = generator.should_create_flashcard("", "дом")
        assert not result_empty  # Should be falsy
        
        result_none = generator.should_create_flashcard(None, "дом")
        assert not result_none  # Should be falsy
        
        result_whitespace = generator.should_create_flashcard("   ", "дом")
        assert not result_whitespace  # Should be falsy
    
    def test_generate_flashcards_from_grammar_not_implemented(self):
        """Test that base class raises NotImplementedError."""
        generator = BaseGenerator()
        
        with pytest.raises(NotImplementedError):
            generator.generate_flashcards_from_grammar(Mock(), "test")


class TestNounGenerator:
    """Test the NounGenerator specifically."""
    
    def test_noun_generator_inheritance(self):
        """Test that NounGenerator inherits from BaseGenerator."""
        generator = NounGenerator()
        assert isinstance(generator, BaseGenerator)
    
    @patch('app.my_graph.generators.noun_generator.logger')
    def test_generate_flashcards_from_grammar_basic(self, mock_logger):
        """Test basic noun flashcard generation."""
        generator = NounGenerator()
        
        # Create a simple mock noun
        mock_noun = Mock(spec=Noun)
        mock_noun.dictionary_form = "стол"
        mock_noun.singular = {
            "nominative": "стол",
            "genitive": "стола",
            "dative": "столу"
        }
        mock_noun.plural = {
            "nominative": "столы",
            "genitive": "столов"
        }
        
        # Mock the methods that create flashcards
        with patch.object(generator, '_generate_singular_forms') as mock_singular:
            with patch.object(generator, '_generate_plural_forms') as mock_plural:
                with patch.object(generator, '_generate_property_flashcards') as mock_properties:
                    mock_singular.return_value = [Mock()]
                    mock_plural.return_value = [Mock(), Mock()]
                    mock_properties.return_value = [Mock()]
                    
                    flashcards = generator.generate_flashcards_from_grammar(mock_noun, "noun")
                    
                    assert len(flashcards) == 4  # 1 + 2 + 1
                    mock_singular.assert_called_once_with(mock_noun, "стол", {})
                    mock_plural.assert_called_once_with(mock_noun, "стол", {})
                    mock_properties.assert_called_once_with(mock_noun, "стол")
    
    def test_generate_flashcards_from_grammar_with_sentences(self):
        """Test noun generation with pre-generated sentences."""
        generator = NounGenerator()
        
        mock_noun = Mock(spec=Noun)
        mock_noun.dictionary_form = "книга"
        
        sentences = {
            "nominative_singular": "Это книга.",
            "genitive_singular": "У меня нет книги."
        }
        
        with patch.object(generator, '_generate_singular_forms') as mock_singular:
            with patch.object(generator, '_generate_plural_forms') as mock_plural:
                with patch.object(generator, '_generate_property_flashcards') as mock_properties:
                    mock_singular.return_value = []
                    mock_plural.return_value = []
                    mock_properties.return_value = []
                    
                    generator.generate_flashcards_from_grammar(mock_noun, "noun", sentences)
                    
                    # Check that sentences were passed to singular forms generator
                    mock_singular.assert_called_once_with(mock_noun, "книга", sentences)


class TestFlashcardGeneratorIntegration:
    """Integration tests for flashcard generation."""
    
    @patch('app.my_graph.flashcard_generator.flashcard_service')
    def test_end_to_end_flashcard_generation_and_saving(self, mock_service):
        """Test complete workflow from grammar object to saved flashcards."""
        # Mock successful database operations
        mock_service.db.add_flashcard.return_value = "flashcard_id_123"
        
        generator = FlashcardGenerator()
        
        # Create a mock noun with minimal required structure
        mock_noun = Mock(spec=Noun)
        mock_noun.dictionary_form = "тест"
        
        # Mock the noun generator to return test flashcards
        with patch.object(generator.noun_generator, 'generate_flashcards_from_grammar') as mock_gen:
            test_flashcards = [
                TwoSidedCard(front="Test front", back="Test back", title="Test card 1"),
                FillInTheBlank(text_with_blanks="Test {blank}", answers=["word"], title="Test card 2")
            ]
            mock_gen.return_value = test_flashcards
            
            # Generate flashcards
            flashcards = generator.generate_flashcards_from_grammar(mock_noun, "noun")
            
            # Save to database
            saved_count = generator.save_flashcards_to_database(flashcards)
            
            # Verify results
            assert len(flashcards) == 2
            assert saved_count == 2
            assert mock_service.db.add_flashcard.call_count == 2
    
    def test_flashcard_generation_error_recovery(self):
        """Test that generation errors don't crash the system."""
        generator = FlashcardGenerator()
        
        # Test with completely invalid input
        invalid_input = "not a grammar object"
        
        flashcards = generator.generate_flashcards_from_grammar(invalid_input, "invalid")
        
        # Should return empty list instead of crashing
        assert flashcards == []
    
    @patch('app.my_graph.flashcard_generator.flashcard_service')
    def test_save_empty_flashcard_list(self, mock_service):
        """Test saving an empty list of flashcards."""
        generator = FlashcardGenerator()
        
        saved_count = generator.save_flashcards_to_database([])
        
        assert saved_count == 0
        mock_service.db.add_flashcard.assert_not_called()
    
    def test_global_flashcard_generator_instance(self):
        """Test that the global instance is properly initialized."""
        from app.my_graph.flashcard_generator import flashcard_generator
        
        assert isinstance(flashcard_generator, FlashcardGenerator)
        assert hasattr(flashcard_generator, 'noun_generator')
        assert hasattr(flashcard_generator, 'service')
"""Tests for grammar analysis tool."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from app.my_graph.tools.grammar_analysis import analyze_russian_grammar_impl
from app.grammar.russian import WordClassification, Noun, Adjective, Verb, Pronoun, Number


class TestGrammarAnalysis:
    """Test cases for Russian grammar analysis functionality."""

    def test_analyze_russian_grammar_noun_success(self):
        """Test successful grammar analysis for a noun."""
        # Mock classification result
        mock_classification = WordClassification(
            word_type="noun",
            russian_word="дом",
            original_word="дом"
        )
        
        # Mock noun grammar result
        mock_noun = Noun(
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
        
        # Mock the entire analysis process
        with patch('app.my_graph.tools.grammar_analysis.ChatOpenAI') as mock_openai, \
             patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_noun_grammar_prompt') as mock_noun_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser') as mock_parser:
            
            # Mock chains to return our expected results
            mock_classification_chain = Mock()
            mock_classification_chain.invoke.return_value = mock_classification
            
            mock_noun_chain = Mock()
            mock_noun_chain.invoke.return_value = mock_noun
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            mock_intermediate2 = Mock()
            mock_intermediate2.__or__ = Mock(return_value=mock_noun_chain)
            mock_noun_prompt.__or__ = Mock(return_value=mock_intermediate2)
            
            result = analyze_russian_grammar_impl("дом")
            
            assert result["success"] is True
            assert result["word"] == "дом"
            assert "analysis" in result
            assert result["analysis"]["noun_grammar"] == mock_noun
            assert result["analysis"]["classification"] == mock_classification

    def test_analyze_russian_grammar_adjective_success(self):
        """Test successful grammar analysis for an adjective."""
        # Mock classification result
        mock_classification = WordClassification(
            word_type="adjective",
            russian_word="красивый",
            original_word="красивый"
        )
        
        # Mock adjective grammar result
        mock_adjective = Adjective(
            dictionary_form="красивый",
            english_translation="beautiful",
            masculine={
                "nom": "красивый",
                "gen": "красивого",
                "dat": "красивому",
                "acc": "красивый",
                "ins": "красивым",
                "pre": "красивом"
            },
            feminine={
                "nom": "красивая",
                "gen": "красивой",
                "dat": "красивой",
                "acc": "красивую",
                "ins": "красивой",
                "pre": "красивой"
            },
            neuter={
                "nom": "красивое",
                "gen": "красивого",
                "dat": "красивому",
                "acc": "красивое",
                "ins": "красивым",
                "pre": "красивом"
            },
            plural={
                "nom": "красивые",
                "gen": "красивых",
                "dat": "красивым",
                "acc": "красивые",
                "ins": "красивыми",
                "pre": "красивых"
            }
        )
        
        # Mock the entire analysis process
        with patch('app.my_graph.tools.grammar_analysis.ChatOpenAI') as mock_openai, \
             patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_adjective_grammar_prompt') as mock_adj_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser') as mock_parser:
            
            # Mock chains to return our expected results
            mock_classification_chain = Mock()
            mock_classification_chain.invoke.return_value = mock_classification
            
            mock_adjective_chain = Mock()
            mock_adjective_chain.invoke.return_value = mock_adjective
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            mock_intermediate2 = Mock()
            mock_intermediate2.__or__ = Mock(return_value=mock_adjective_chain)
            mock_adj_prompt.__or__ = Mock(return_value=mock_intermediate2)
            
            result = analyze_russian_grammar_impl("красивый")
            
            assert result["success"] is True
            assert result["word"] == "красивый"
            assert "analysis" in result
            assert result["analysis"]["adjective_grammar"] == mock_adjective
            assert result["analysis"]["classification"] == mock_classification

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_verb_success(self, mock_openai):
        """Test successful grammar analysis for a verb."""
        mock_classification = WordClassification(
            word_type="verb",
            russian_word="читать",
            original_word="читать"
        )
        
        mock_verb = Verb(
            dictionary_form="читать",
            english_translation="to read",
            aspect="imperfective",
            present_first_singular="читаю",
            present_second_singular="читаешь",
            present_third_singular="читает",
            present_first_plural="читаем",
            present_second_plural="читаете",
            present_third_plural="читают",
            past_masculine="читал",
            past_feminine="читала",
            past_neuter="читало",
            past_plural="читали"
        )
        
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        mock_verb_chain = Mock()
        mock_verb_chain.invoke.return_value = mock_verb
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_verb_grammar_prompt') as mock_verb_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            mock_intermediate2 = Mock()
            mock_intermediate2.__or__ = Mock(return_value=mock_verb_chain)
            mock_verb_prompt.__or__ = Mock(return_value=mock_intermediate2)
            
            result = analyze_russian_grammar_impl("читать")
            
            assert result["success"] is True
            assert result["word"] == "читать"
            assert result["analysis"]["verb_grammar"] == mock_verb

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_unsupported_word_type(self, mock_openai):
        """Test handling of unsupported word types like adverbs."""
        mock_classification = WordClassification(
            word_type="adverb",
            russian_word="быстро",
            original_word="быстро"
        )
        
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            result = analyze_russian_grammar_impl("быстро")
            
            assert result["success"] is True
            assert result["word"] == "быстро"
            assert result["word_type"] == "adverb"
            assert "detailed grammar analysis is not yet supported" in result["message"]

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_classification_error(self, mock_openai):
        """Test error handling during classification step."""
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.side_effect = Exception("API Error")
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            result = analyze_russian_grammar_impl("тест")
            
            assert result["success"] is False
            assert result["word"] == "тест"
            assert "error" in result
            assert "API Error" in result["error"]

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_grammar_analysis_error(self, mock_openai):
        """Test error handling during detailed grammar analysis."""
        mock_classification = WordClassification(
            word_type="noun",
            russian_word="тест",
            original_word="тест"
        )
        
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        mock_noun_chain = Mock()
        mock_noun_chain.invoke.side_effect = Exception("Invalid data")
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_noun_grammar_prompt') as mock_noun_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            mock_intermediate2 = Mock()
            mock_intermediate2.__or__ = Mock(return_value=mock_noun_chain)
            mock_noun_prompt.__or__ = Mock(return_value=mock_intermediate2)
            
            result = analyze_russian_grammar_impl("тест")
            
            assert result["success"] is False
            assert result["word"] == "тест"
            assert "error" in result

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_pronoun_success(self, mock_openai):
        """Test successful grammar analysis for a pronoun."""
        mock_classification = WordClassification(
            word_type="pronoun",
            russian_word="я",
            original_word="я"
        )
        
        mock_pronoun = Pronoun(
            dictionary_form="я",
            english_translation="I",
            singular={
                "nom": "я",
                "gen": "меня",
                "dat": "мне",
                "acc": "меня",
                "ins": "мной",
                "pre": "мне"
            }
        )
        
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        mock_pronoun_chain = Mock()
        mock_pronoun_chain.invoke.return_value = mock_pronoun
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_pronoun_grammar_prompt') as mock_pronoun_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            mock_intermediate2 = Mock()
            mock_intermediate2.__or__ = Mock(return_value=mock_pronoun_chain)
            mock_pronoun_prompt.__or__ = Mock(return_value=mock_intermediate2)
            
            result = analyze_russian_grammar_impl("я")
            
            assert result["success"] is True
            assert result["word"] == "я"
            assert result["analysis"]["pronoun_grammar"] == mock_pronoun

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_number_success(self, mock_openai):
        """Test successful grammar analysis for a number."""
        mock_classification = WordClassification(
            word_type="number",
            russian_word="один",
            original_word="один"
        )
        
        mock_number = Number(
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
            }
        )
        
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        mock_number_chain = Mock()
        mock_number_chain.invoke.return_value = mock_number
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_number_grammar_prompt') as mock_number_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            # Create a mock that returns our chains when __or__ is called
            mock_intermediate1 = Mock()
            mock_intermediate1.__or__ = Mock(return_value=mock_classification_chain)
            mock_class_prompt.__or__ = Mock(return_value=mock_intermediate1)
            
            mock_intermediate2 = Mock()
            mock_intermediate2.__or__ = Mock(return_value=mock_number_chain)
            mock_number_prompt.__or__ = Mock(return_value=mock_intermediate2)
            
            result = analyze_russian_grammar_impl("один")
            
            assert result["success"] is True
            assert result["word"] == "один"
            assert result["analysis"]["number_grammar"] == mock_number

    def test_analyze_russian_grammar_empty_input(self):
        """Test handling of empty input."""
        result = analyze_russian_grammar_impl("")
        
        # The function should return a result structure
        assert "success" in result
        assert result["word"] == ""
        # Either succeeds with minimal classification or fails with error
        if not result["success"]:
            assert "error" in result

    @patch('app.my_graph.tools.grammar_analysis.settings')
    def test_analyze_russian_grammar_settings_integration(self, mock_settings):
        """Test that the function uses settings correctly."""
        mock_settings.openai_api_key = "test-key"
        mock_settings.llm_model = "gpt-4"
        
        with patch('app.my_graph.tools.grammar_analysis.ChatOpenAI') as mock_openai:
            mock_llm = Mock()
            mock_openai.return_value = mock_llm
            
            # Mock the rest of the chain to avoid complex setup
            with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_prompt:
                mock_chain = Mock()
                mock_chain.invoke.side_effect = Exception("Test exception")
                mock_prompt.__or__ = Mock(return_value=mock_chain)
                
                result = analyze_russian_grammar_impl("тест")
                
                # Should have been called with correct settings
                mock_openai.assert_called_once()
                call_args = mock_openai.call_args
                assert call_args[1]['model'] == "gpt-4"
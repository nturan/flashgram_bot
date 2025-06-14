"""Simplified tests for grammar analysis tool."""

import pytest
from unittest.mock import Mock, patch

from app.my_graph.tools.grammar_analysis import analyze_russian_grammar_impl


class TestGrammarAnalysisSimple:
    """Simplified test cases for Russian grammar analysis functionality."""

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_basic_success(self, mock_openai):
        """Test basic successful grammar analysis."""
        from app.grammar.russian import WordClassification, Noun
        
        mock_classification = WordClassification(
            word_type="noun",
            russian_word="дом",
            original_word="дом"
        )
        
        mock_noun = Noun(
            dictionary_form="дом",
            gender="masculine",
            animacy=False,
            singular={"nom": "дом", "gen": "дома", "dat": "дому", "acc": "дом", "ins": "домом", "pre": "доме"},
            plural={"nom": "дома", "gen": "домов", "dat": "домам", "acc": "дома", "ins": "домами", "pre": "домах"},
            english_translation="house"
        )
        
        # Mock chains
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        mock_noun_chain = Mock()
        mock_noun_chain.invoke.return_value = mock_noun
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.get_noun_grammar_prompt') as mock_noun_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            mock_class_prompt.__or__ = Mock(return_value=mock_classification_chain)
            mock_noun_prompt.__or__ = Mock(return_value=mock_noun_chain)
            
            result = analyze_russian_grammar_impl("дом")
            
            assert result["success"] is True
            assert result["word"] == "дом"
            assert "analysis" in result

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_error(self, mock_openai):
        """Test error handling in grammar analysis."""
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.side_effect = Exception("API connection failed")
        
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

    @patch('app.my_graph.tools.grammar_analysis.ChatOpenAI')
    def test_analyze_russian_grammar_unsupported_type(self, mock_openai):
        """Test handling of unsupported word types."""
        from app.grammar.russian import WordClassification
        
        mock_classification = WordClassification(
            word_type="adverb",
            russian_word="быстро",
            original_word="быстро"
        )
        
        mock_classification_chain = Mock()
        mock_classification_chain.invoke.return_value = mock_classification
        
        with patch('app.my_graph.tools.grammar_analysis.initial_classification_prompt') as mock_class_prompt, \
             patch('app.my_graph.tools.grammar_analysis.PydanticOutputParser'):
            
            mock_class_prompt.__or__ = Mock(return_value=mock_classification_chain)
            
            result = analyze_russian_grammar_impl("быстро")
            
            assert result["success"] is True
            assert result["word"] == "быстро"
            assert "not yet supported" in result["message"]

    def test_analyze_russian_grammar_empty_input(self):
        """Test handling of empty input."""
        result = analyze_russian_grammar_impl("")
        
        # Should handle empty input gracefully
        assert "success" in result
        assert result["word"] == ""
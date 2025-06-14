"""Tests for dictionary form finder utilities."""

import pytest
from unittest.mock import Mock, patch
from app.my_graph.utils.dictionary_form_finder import (
    find_best_dictionary_form,
    get_word_validity_info,
    find_all_possible_dictionary_forms,
    validate_russian_word,
    get_dictionary_form,
    is_valid_russian_word
)
from app.my_graph.utils.hunspell_analyzer import MorphAnalysis


class TestDictionaryFormFinder:
    """Test the dictionary form finder utilities."""
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_find_best_dictionary_form_hunspell_available(self, mock_get_analyzer):
        """Test finding dictionary form when Hunspell is available."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        mock_analyzer.find_dictionary_form.return_value = 'читать'
        mock_get_analyzer.return_value = mock_analyzer
        
        result = find_best_dictionary_form('читает')
        
        assert result == 'читать'
        mock_analyzer.find_dictionary_form.assert_called_once_with('читает')
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_find_best_dictionary_form_hunspell_unavailable_with_grammar(self, mock_get_analyzer):
        """Test finding dictionary form when Hunspell is unavailable but grammar analysis available."""
        # Mock unavailable Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = False
        mock_get_analyzer.return_value = mock_analyzer
        
        # Mock grammar analysis with noun
        mock_noun = Mock()
        mock_noun.dictionary_form = 'дом'
        grammar_analysis = {
            'success': True,
            'analysis': {
                'noun_grammar': mock_noun,
                'adjective_grammar': None,
                'verb_grammar': None,
                'pronoun_grammar': None,
                'number_grammar': None
            }
        }
        
        result = find_best_dictionary_form('дома', grammar_analysis)
        
        assert result == 'дом'
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_find_best_dictionary_form_fallback_to_original(self, mock_get_analyzer):
        """Test fallback to original word when no other methods work."""
        # Mock unavailable Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = False
        mock_get_analyzer.return_value = mock_analyzer
        
        # No grammar analysis provided
        result = find_best_dictionary_form('тест')
        
        assert result == 'тест'
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_find_best_dictionary_form_grammar_priority(self, mock_get_analyzer):
        """Test that Hunspell takes priority over grammar analysis."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        mock_analyzer.find_dictionary_form.return_value = 'читать'
        mock_get_analyzer.return_value = mock_analyzer
        
        # Mock grammar analysis with different result
        mock_verb = Mock()
        mock_verb.dictionary_form = 'читание'  # Different form
        grammar_analysis = {
            'success': True,
            'analysis': {
                'verb_grammar': mock_verb,
                'noun_grammar': None,
                'adjective_grammar': None,
                'pronoun_grammar': None,
                'number_grammar': None
            }
        }
        
        result = find_best_dictionary_form('читает', grammar_analysis)
        
        # Should prefer Hunspell result
        assert result == 'читать'
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_get_word_validity_info_available(self, mock_get_analyzer):
        """Test getting word validity info when Hunspell is available."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        
        mock_analysis = MorphAnalysis(
            word='тест',
            is_valid=True,
            stems=['тест'],
            suggestions=[],
            dictionary_forms={'тест'}
        )
        mock_analyzer.analyze_word.return_value = mock_analysis
        mock_get_analyzer.return_value = mock_analyzer
        
        result = get_word_validity_info('тест')
        
        assert result['is_valid'] == True
        assert result['stems'] == ['тест']
        assert result['dictionary_forms'] == ['тест']
        assert result['suggestions'] == []
        assert result['hunspell_available'] == True
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_get_word_validity_info_unavailable(self, mock_get_analyzer):
        """Test getting word validity info when Hunspell is unavailable."""
        # Mock unavailable Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = False
        mock_get_analyzer.return_value = mock_analyzer
        
        result = get_word_validity_info('тест')
        
        assert result['is_valid'] is None
        assert result['suggestions'] == []
        assert result['hunspell_available'] == False
        assert 'not available' in result['message']
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_find_all_possible_dictionary_forms(self, mock_get_analyzer):
        """Test finding all possible dictionary forms."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        
        mock_analysis = MorphAnalysis(
            word='читает',
            is_valid=True,
            stems=['читать', 'чита'],
            suggestions=[],
            dictionary_forms={'читать', 'читание'}
        )
        mock_analyzer.analyze_word.return_value = mock_analysis
        mock_get_analyzer.return_value = mock_analyzer
        
        result = find_all_possible_dictionary_forms('читает')
        
        # Should include all unique forms
        assert 'читать' in result
        assert 'читание' in result
        assert 'чита' in result
        # Should remove duplicates
        assert len(result) == len(set(result))
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_validate_russian_word_valid(self, mock_get_analyzer):
        """Test validating a valid Russian word."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        mock_analyzer.is_word_valid.return_value = True
        mock_get_analyzer.return_value = mock_analyzer
        
        result = validate_russian_word('дом')
        
        assert result['is_valid'] == True
        assert result['word'] == 'дом'
        assert result['suggestions'] == []
        assert 'valid' in result['message']
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_validate_russian_word_invalid_with_suggestions(self, mock_get_analyzer):
        """Test validating an invalid Russian word with suggestions."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        mock_analyzer.is_word_valid.return_value = False
        mock_analyzer.get_suggestions.return_value = ['дом', 'дома', 'домой']
        mock_get_analyzer.return_value = mock_analyzer
        
        result = validate_russian_word('домм')
        
        assert result['is_valid'] == False
        assert result['word'] == 'домм'
        assert result['suggestions'] == ['дом', 'дома', 'домой']
        assert 'Suggestions:' in result['message']
        assert 'дом' in result['message']
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_validate_russian_word_invalid_no_suggestions(self, mock_get_analyzer):
        """Test validating an invalid Russian word without suggestions."""
        # Mock Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = True
        mock_analyzer.is_word_valid.return_value = False
        mock_analyzer.get_suggestions.return_value = []
        mock_get_analyzer.return_value = mock_analyzer
        
        result = validate_russian_word('xyzabc')
        
        assert result['is_valid'] == False
        assert result['word'] == 'xyzabc'
        assert result['suggestions'] == []
        assert 'no suggestions' in result['message']
    
    @patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer')
    def test_validate_russian_word_hunspell_unavailable(self, mock_get_analyzer):
        """Test validating a word when Hunspell is unavailable."""
        # Mock unavailable Hunspell analyzer
        mock_analyzer = Mock()
        mock_analyzer.is_available.return_value = False
        mock_get_analyzer.return_value = mock_analyzer
        
        result = validate_russian_word('тест')
        
        assert result['is_valid'] is None
        assert result['word'] == 'тест'
        assert result['suggestions'] == []
        assert 'not available' in result['message']
    
    @patch('app.my_graph.utils.dictionary_form_finder.find_best_dictionary_form')
    def test_get_dictionary_form_convenience(self, mock_find_best):
        """Test convenience function get_dictionary_form."""
        mock_find_best.return_value = 'тест'
        
        result = get_dictionary_form('тесты')
        
        assert result == 'тест'
        mock_find_best.assert_called_once_with('тесты')
    
    @patch('app.my_graph.utils.dictionary_form_finder.validate_russian_word')
    def test_is_valid_russian_word_convenience(self, mock_validate):
        """Test convenience function is_valid_russian_word."""
        mock_validate.return_value = {'is_valid': True}
        
        result = is_valid_russian_word('тест')
        
        assert result == True
        mock_validate.assert_called_once_with('тест')
    
    def test_find_best_dictionary_form_with_different_grammar_types(self):
        """Test finding dictionary form with different grammar types."""
        # Test with adjective grammar
        mock_adjective = Mock()
        mock_adjective.dictionary_form = 'красивый'
        grammar_analysis = {
            'success': True,
            'analysis': {
                'adjective_grammar': mock_adjective,
                'noun_grammar': None,
                'verb_grammar': None,
                'pronoun_grammar': None,
                'number_grammar': None
            }
        }
        
        with patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get_analyzer.return_value = mock_analyzer
            
            result = find_best_dictionary_form('красивого', grammar_analysis)
            assert result == 'красивый'
    
    def test_find_best_dictionary_form_empty_dictionary_form(self):
        """Test handling of empty dictionary_form in grammar analysis."""
        mock_noun = Mock()
        mock_noun.dictionary_form = '  '  # Empty/whitespace
        grammar_analysis = {
            'success': True,
            'analysis': {
                'noun_grammar': mock_noun,
                'adjective_grammar': None,
                'verb_grammar': None,
                'pronoun_grammar': None,
                'number_grammar': None
            }
        }
        
        with patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get_analyzer.return_value = mock_analyzer
            
            result = find_best_dictionary_form('тест', grammar_analysis)
            # Should fallback to original word
            assert result == 'тест'
    
    def test_find_best_dictionary_form_failed_grammar_analysis(self):
        """Test handling of failed grammar analysis."""
        grammar_analysis = {
            'success': False,
            'error': 'Some error'
        }
        
        with patch('app.my_graph.utils.dictionary_form_finder.get_hunspell_analyzer') as mock_get_analyzer:
            mock_analyzer = Mock()
            mock_analyzer.is_available.return_value = False
            mock_get_analyzer.return_value = mock_analyzer
            
            result = find_best_dictionary_form('тест', grammar_analysis)
            # Should fallback to original word
            assert result == 'тест'
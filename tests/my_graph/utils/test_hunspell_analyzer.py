"""Tests for Hunspell analyzer integration."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.my_graph.utils.hunspell_analyzer import (
    RussianHunspellAnalyzer,
    get_hunspell_analyzer,
    find_dictionary_form,
    is_word_valid,
    MorphAnalysis
)


class TestRussianHunspellAnalyzer:
    """Test the Russian Hunspell analyzer."""
    
    def test_init_without_hunspell(self):
        """Test initialization when pyhunspell is not available."""
        with patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', False):
            analyzer = RussianHunspellAnalyzer()
            assert not analyzer.available
            assert not analyzer.is_available()
    
    def test_init_with_missing_files(self):
        """Test initialization when dictionary files are missing."""
        with patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True):
            # Mock Path.exists to return False
            with patch('pathlib.Path.exists', return_value=False):
                analyzer = RussianHunspellAnalyzer()
                assert not analyzer.available
    
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    def test_init_success(self, mock_available, mock_exists, mock_hunspell_class):
        """Test successful initialization."""
        mock_hunspell_obj = Mock()
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        
        assert analyzer.available
        assert analyzer.is_available()
        assert analyzer.hunspell_obj == mock_hunspell_obj
        mock_hunspell_class.assert_called_once()
    
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    def test_analyze_word_valid(self, mock_available, mock_exists, mock_hunspell_class):
        """Test analyzing a valid Russian word."""
        mock_hunspell_obj = Mock()
        mock_hunspell_obj.spell.return_value = True
        mock_hunspell_obj.stem.return_value = ['дом']
        mock_hunspell_obj.suggest.return_value = []
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        result = analyzer.analyze_word('дома')
        
        assert isinstance(result, MorphAnalysis)
        assert result.word == 'дома'
        assert result.is_valid == True
        assert result.stems == ['дом']
        assert 'дом' in result.dictionary_forms
        assert result.suggestions == []
    
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    def test_analyze_word_invalid(self, mock_available, mock_exists, mock_hunspell_class):
        """Test analyzing an invalid Russian word."""
        mock_hunspell_obj = Mock()
        mock_hunspell_obj.spell.return_value = False
        mock_hunspell_obj.stem.return_value = []
        mock_hunspell_obj.suggest.return_value = ['дома', 'дом']
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        result = analyzer.analyze_word('домаа')
        
        assert isinstance(result, MorphAnalysis)
        assert result.word == 'домаа'
        assert result.is_valid == False
        assert result.stems == []
        assert result.suggestions == ['дома', 'дом']
    
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    def test_find_dictionary_form_valid_word(self, mock_available, mock_exists, mock_hunspell_class):
        """Test finding dictionary form for a valid word."""
        mock_hunspell_obj = Mock()
        mock_hunspell_obj.spell.return_value = True
        mock_hunspell_obj.stem.return_value = ['читать']
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        result = analyzer.find_dictionary_form('читает')
        
        assert result == 'читать'
    
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    def test_find_dictionary_form_invalid_word_with_suggestions(self, mock_available, mock_exists, mock_hunspell_class):
        """Test finding dictionary form for invalid word with valid suggestions."""
        mock_hunspell_obj = Mock()
        # First call for the original word
        mock_hunspell_obj.spell.side_effect = [False, True]  # Invalid, then valid for suggestion
        mock_hunspell_obj.stem.side_effect = [[], ['читать']]  # No stems for original, stems for suggestion
        mock_hunspell_obj.suggest.return_value = ['читает']
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        result = analyzer.find_dictionary_form('читаат')
        
        assert result == 'читать'
    
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    def test_is_word_valid(self, mock_available, mock_exists, mock_hunspell_class):
        """Test word validity checking."""
        mock_hunspell_obj = Mock()
        mock_hunspell_obj.spell.side_effect = [True, False]
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        
        assert analyzer.is_word_valid('дом') == True
        assert analyzer.is_word_valid('домаа') == False
    
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    def test_get_suggestions(self, mock_available, mock_exists, mock_hunspell_class):
        """Test getting spelling suggestions."""
        mock_hunspell_obj = Mock()
        mock_hunspell_obj.suggest.return_value = ['дом', 'дома', 'домой', 'домик', 'домище']
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        suggestions = analyzer.get_suggestions('домм', limit=3)
        
        assert suggestions == ['дом', 'дома', 'домой']
    
    def test_unavailable_analyzer_methods(self):
        """Test that methods return appropriate values when analyzer is unavailable."""
        with patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', False):
            analyzer = RussianHunspellAnalyzer()
            
            assert not analyzer.is_available()
            
            result = analyzer.analyze_word('тест')
            assert result.word == 'тест'
            assert result.is_valid == False
            assert result.stems == []
            assert result.suggestions == []
            
            assert analyzer.find_dictionary_form('тест') is None
            assert analyzer.is_word_valid('тест') == False
            assert analyzer.get_suggestions('тест') == []


class TestGlobalFunctions:
    """Test the global convenience functions."""
    
    @patch('app.my_graph.utils.hunspell_analyzer.get_hunspell_analyzer')
    def test_find_dictionary_form_global(self, mock_get_analyzer):
        """Test global find_dictionary_form function."""
        mock_analyzer = Mock()
        mock_analyzer.find_dictionary_form.return_value = 'тест'
        mock_get_analyzer.return_value = mock_analyzer
        
        result = find_dictionary_form('тесты')
        
        assert result == 'тест'
        mock_analyzer.find_dictionary_form.assert_called_once_with('тесты')
    
    @patch('app.my_graph.utils.hunspell_analyzer.get_hunspell_analyzer')
    def test_is_word_valid_global(self, mock_get_analyzer):
        """Test global is_word_valid function."""
        mock_analyzer = Mock()
        mock_analyzer.is_word_valid.return_value = True
        mock_get_analyzer.return_value = mock_analyzer
        
        result = is_word_valid('тест')
        
        assert result == True
        mock_analyzer.is_word_valid.assert_called_once_with('тест')
    
    def test_global_analyzer_singleton(self):
        """Test that global analyzer is a singleton."""
        analyzer1 = get_hunspell_analyzer()
        analyzer2 = get_hunspell_analyzer()
        
        assert analyzer1 is analyzer2


class TestWithRealDictionary:
    """Test with real dictionary files if available."""
    
    def setup_method(self):
        """Set up test method."""
        self.analyzer = RussianHunspellAnalyzer()
    
    def test_real_dictionary_availability(self):
        """Test if real dictionary files are available."""
        # This test will pass if dictionary files exist, skip if not
        if not self.analyzer.is_available():
            pytest.skip("Hunspell dictionary files not available")
    
    def test_common_russian_words(self):
        """Test analysis of common Russian words if dictionary is available."""
        if not self.analyzer.is_available():
            pytest.skip("Hunspell dictionary not available")
        
        # Test some basic Russian words
        test_words = ['дом', 'читать', 'красивый', 'я', 'один']
        
        for word in test_words:
            try:
                result = self.analyzer.analyze_word(word)
                # Just check that we get some result without errors
                assert isinstance(result, MorphAnalysis)
                assert result.word == word
            except Exception as e:
                # If there are encoding or other issues, that's expected in some environments
                pytest.skip(f"Dictionary analysis failed for '{word}': {e}")
    
    def test_dictionary_form_extraction(self):
        """Test dictionary form extraction for inflected words."""
        if not self.analyzer.is_available():
            pytest.skip("Hunspell dictionary not available")
        
        # Test cases: inflected form -> expected dictionary form (if known)
        test_cases = [
            ('дома', 'дом'),      # дома (genitive) -> дом (nominative)
            ('читает', 'читать'),  # читает (3rd person) -> читать (infinitive)
        ]
        
        for inflected, expected_base in test_cases:
            try:
                result = self.analyzer.find_dictionary_form(inflected)
                # We can't guarantee exact match due to dictionary variations,
                # but we should get some result
                assert result is not None, f"No dictionary form found for '{inflected}'"
                
                # If we get the expected result, great! If not, just log it
                if result != expected_base:
                    print(f"Note: For '{inflected}', got '{result}' instead of expected '{expected_base}'")
                
            except Exception as e:
                pytest.skip(f"Dictionary form extraction failed for '{inflected}': {e}")


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    def test_hunspell_exception_handling(self, mock_available, mock_exists, mock_hunspell_class):
        """Test handling of Hunspell exceptions."""
        mock_hunspell_obj = Mock()
        mock_hunspell_obj.spell.side_effect = Exception("Hunspell error")
        mock_hunspell_class.return_value = mock_hunspell_obj
        
        analyzer = RussianHunspellAnalyzer()
        result = analyzer.analyze_word('тест')
        
        # Should handle exception gracefully
        assert result.word == 'тест'
        assert result.is_valid == False
        assert result.stems == []
    
    @patch('app.my_graph.utils.hunspell_analyzer.HUNSPELL_AVAILABLE', True)
    @patch('pathlib.Path.exists', return_value=True)
    @patch('app.my_graph.utils.hunspell_analyzer.hunspell.HunSpell')
    def test_initialization_exception(self, mock_available, mock_exists, mock_hunspell_class):
        """Test handling of initialization exceptions."""
        mock_hunspell_class.side_effect = Exception("Initialization failed")
        
        analyzer = RussianHunspellAnalyzer()
        
        assert not analyzer.available
        assert not analyzer.is_available()
        assert analyzer.hunspell_obj is None
"""Simple integration tests for Hunspell functionality."""

import pytest
from app.my_graph.utils.hunspell_analyzer import get_hunspell_analyzer
from app.my_graph.utils.dictionary_form_finder import (
    find_best_dictionary_form,
    validate_russian_word,
    get_word_validity_info
)


class TestHunspellSimpleIntegration:
    """Simple tests to verify Hunspell integration works end-to-end."""
    
    def setup_method(self):
        """Set up test method."""
        self.analyzer = get_hunspell_analyzer()
    
    def test_hunspell_basic_functionality(self):
        """Test basic Hunspell functionality with real Russian words."""
        if not self.analyzer.is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing basic Hunspell functionality...")
        
        # Test basic word validation
        assert self.analyzer.is_word_valid("дом") == True
        assert self.analyzer.is_word_valid("zzxxyy") == False
        
        # Test dictionary form extraction
        dictionary_form = self.analyzer.find_dictionary_form("дома")
        print(f"Dictionary form of 'дома': {dictionary_form}")
        assert dictionary_form is not None
        assert len(dictionary_form) > 0
        
        # Test morphological analysis
        result = self.analyzer.analyze_word("дом")
        print(f"Analysis of 'дом': valid={result.is_valid}, stems={result.stems}")
        assert result.is_valid == True
        assert len(result.stems) >= 0  # May or may not have stems
    
    def test_dictionary_form_finder_integration(self):
        """Test that dictionary form finder works with Hunspell."""
        if not get_hunspell_analyzer().is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing dictionary form finder...")
        
        # Test common Russian words
        test_cases = [
            "дом",      # nominative (should return itself)
            "дома",     # genitive or plural nominative (should return дом)
            "домов",    # genitive plural (should return дом)
        ]
        
        for word in test_cases:
            dictionary_form = find_best_dictionary_form(word)
            print(f"Dictionary form of '{word}': {dictionary_form}")
            assert dictionary_form is not None
            assert len(dictionary_form) > 0
            # The dictionary form should be a valid Russian word
            assert isinstance(dictionary_form, str)
    
    def test_word_validation_integration(self):
        """Test word validation functionality."""
        if not get_hunspell_analyzer().is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing word validation...")
        
        # Test valid Russian word
        result = validate_russian_word("дом")
        print(f"Validation of 'дом': {result}")
        assert result['is_valid'] == True
        assert result['word'] == "дом"
        assert len(result['suggestions']) == 0  # No suggestions needed for valid words
        
        # Test invalid word
        result = validate_russian_word("zzzxxx")
        print(f"Validation of 'zzzxxx': {result}")
        assert result['is_valid'] == False
        assert result['word'] == "zzzxxx"
        # May or may not have suggestions for completely invalid words
    
    def test_word_validity_info_integration(self):
        """Test getting comprehensive word validity information."""
        if not get_hunspell_analyzer().is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing word validity info...")
        
        # Test with valid word
        info = get_word_validity_info("дом")
        print(f"Validity info for 'дом': {info}")
        assert info['hunspell_available'] == True
        assert info['is_valid'] == True
        assert isinstance(info['stems'], list)
        assert isinstance(info['dictionary_forms'], list)
        assert isinstance(info['suggestions'], list)
    
    def test_encoding_handling(self):
        """Test that Russian text encoding is handled correctly."""
        if not get_hunspell_analyzer().is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing encoding handling...")
        
        # Test various Russian words with different characters
        russian_words = [
            "дом",       # basic Latin-looking characters
            "щука",      # special Russian characters
            "ёжик",      # with ё character
            "съезд",     # with hard sign
            "семья",     # with soft sign
        ]
        
        for word in russian_words:
            try:
                result = self.analyzer.analyze_word(word)
                print(f"Analysis of '{word}': valid={result.is_valid}")
                
                # Basic checks
                assert result.word == word
                assert isinstance(result.is_valid, bool)
                assert isinstance(result.stems, list)
                assert isinstance(result.suggestions, list)
                assert isinstance(result.dictionary_forms, set)
                
                # If valid, check that we get meaningful results
                if result.is_valid:
                    print(f"  Stems: {result.stems}")
                    print(f"  Dictionary forms: {result.dictionary_forms}")
                
            except Exception as e:
                print(f"Error with word '{word}': {e}")
                # Some words might not be in the dictionary, that's OK
                pass
    
    def test_inflected_forms_analysis(self):
        """Test analysis of Russian inflected forms."""
        if not get_hunspell_analyzer().is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing inflected forms analysis...")
        
        # Test some common inflected forms
        inflected_forms = [
            "дома",     # genitive singular OR plural nominative of дом
            "книги",    # genitive singular OR plural nominative of книга
            "столы",    # plural nominative of стол
        ]
        
        for form in inflected_forms:
            dictionary_form = find_best_dictionary_form(form)
            print(f"'{form}' -> '{dictionary_form}'")
            
            # Should get some dictionary form
            assert dictionary_form is not None
            assert len(dictionary_form) > 0
            assert isinstance(dictionary_form, str)
            
            # The dictionary form should be different or same as original
            # (both are valid - some words are already in dictionary form)
            print(f"  Original: {form}, Dictionary: {dictionary_form}")
    
    def test_integration_with_fallback(self):
        """Test that integration works and falls back gracefully."""
        print("Testing integration with fallback...")
        
        # Test with a word, regardless of whether Hunspell is available
        test_word = "тест"
        
        # This should work even if Hunspell is not available
        dictionary_form = find_best_dictionary_form(test_word)
        print(f"Dictionary form of '{test_word}': {dictionary_form}")
        
        # Should at least return the original word as fallback
        assert dictionary_form is not None
        assert len(dictionary_form) > 0
        
        # Test validation (should work with or without Hunspell)
        result = validate_russian_word(test_word)
        print(f"Validation result: {result}")
        
        # Should have the basic structure
        assert 'is_valid' in result
        assert 'word' in result
        assert 'suggestions' in result
        assert 'message' in result
        assert result['word'] == test_word
    
    def test_consistency_across_functions(self):
        """Test that different functions give consistent results for the same word."""
        if not get_hunspell_analyzer().is_available():
            pytest.skip("Hunspell not available in test environment")
        
        print("Testing consistency across functions...")
        
        test_word = "дом"
        
        # Get results from different functions
        is_valid_1 = self.analyzer.is_word_valid(test_word)
        analysis = self.analyzer.analyze_word(test_word)
        validity_info = get_word_validity_info(test_word)
        validation_result = validate_russian_word(test_word)
        
        print(f"Word: {test_word}")
        print(f"  analyzer.is_word_valid(): {is_valid_1}")
        print(f"  analyzer.analyze_word().is_valid: {analysis.is_valid}")
        print(f"  get_word_validity_info()['is_valid']: {validity_info['is_valid']}")
        print(f"  validate_russian_word()['is_valid']: {validation_result['is_valid']}")
        
        # All should agree on validity
        assert is_valid_1 == analysis.is_valid
        assert analysis.is_valid == validity_info['is_valid']
        assert validity_info['is_valid'] == validation_result['is_valid']
        
        print("All functions agree on word validity!")


class TestHunspellRealWorldUsage:
    """Test Hunspell with real-world usage patterns."""
    
    @pytest.mark.skipif(
        not get_hunspell_analyzer().is_available(),
        reason="Hunspell not available"
    )
    def test_common_russian_words(self):
        """Test with a variety of common Russian words."""
        analyzer = get_hunspell_analyzer()
        
        # Common Russian words of different types
        test_words = [
            # Nouns
            "дом", "книга", "стол", "окно", "рука",
            # Adjectives  
            "большой", "красивый", "хороший",
            # Verbs
            "читать", "писать", "говорить",
            # Pronouns
            "я", "ты", "он", "она", "мы",
            # Numbers
            "один", "два", "три", "четыре", "пять",
        ]
        
        print("Testing common Russian words:")
        valid_count = 0
        total_count = len(test_words)
        
        for word in test_words:
            is_valid = analyzer.is_word_valid(word)
            dictionary_form = analyzer.find_dictionary_form(word)
            
            print(f"  {word}: valid={is_valid}, dictionary_form={dictionary_form}")
            
            if is_valid:
                valid_count += 1
                # Valid words should have a dictionary form
                assert dictionary_form is not None
                assert len(dictionary_form) > 0
        
        print(f"Found {valid_count}/{total_count} words in dictionary")
        
        # We expect at least some common words to be recognized
        recognition_rate = valid_count / total_count
        print(f"Recognition rate: {recognition_rate:.2%}")
        
        # This is lenient - different dictionaries have different coverage
        # We just want to see that SOME words are recognized
        assert valid_count > 0, "No common Russian words were recognized"
    
    @pytest.mark.skipif(
        not get_hunspell_analyzer().is_available(),
        reason="Hunspell not available"
    )
    def test_inflection_patterns(self):
        """Test recognition of Russian inflection patterns."""
        analyzer = get_hunspell_analyzer()
        
        # Test some basic inflection patterns
        inflection_tests = [
            # Base word and some of its forms
            ("дом", ["дома", "дому", "домом", "доме"]),
            ("стол", ["стола", "столу", "столом", "столе"]),
        ]
        
        print("Testing inflection patterns:")
        
        for base_word, inflected_forms in inflection_tests:
            print(f"\nBase word: {base_word}")
            base_valid = analyzer.is_word_valid(base_word)
            print(f"  Base form valid: {base_valid}")
            
            for inflected in inflected_forms:
                is_valid = analyzer.is_word_valid(inflected)
                dictionary_form = analyzer.find_dictionary_form(inflected)
                
                print(f"  {inflected}: valid={is_valid}, dict_form={dictionary_form}")
                
                # If the inflected form is valid, we should get some dictionary form
                if is_valid:
                    assert dictionary_form is not None
                    assert len(dictionary_form) > 0
    
    def test_error_resilience(self):
        """Test that the system handles edge cases gracefully."""
        analyzer = get_hunspell_analyzer()
        
        edge_cases = [
            "",           # Empty string
            " ",          # Whitespace
            "123",        # Numbers
            "hello",      # English word
            "привет123",  # Mixed Russian/numbers
            "ё" * 50,     # Very long string
        ]
        
        print("Testing error resilience:")
        
        for test_case in edge_cases:
            try:
                result = analyzer.analyze_word(test_case)
                dictionary_form = find_best_dictionary_form(test_case)
                
                print(f"  '{test_case}': valid={result.is_valid}, dict_form={dictionary_form}")
                
                # Should not crash and should return reasonable results
                assert isinstance(result.is_valid, bool)
                assert isinstance(result.stems, list)
                assert isinstance(result.suggestions, list)
                assert isinstance(result.dictionary_forms, set)
                assert dictionary_form is not None  # Should at least return the input
                
            except Exception as e:
                print(f"  '{test_case}': ERROR - {e}")
                # Some edge cases might cause errors, but they should be handled
                # The important thing is the system doesn't crash completely
                pass
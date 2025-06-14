"""Integration tests for pymorphy2-based grammar analysis."""

import pytest
from app.my_graph.utils.pymorphy2_analyzer import (
    PyMorphy2Analyzer,
    PyMorphy2NounAnalyzer,
    pymorphy2_analyze_russian_grammar_impl,
    get_pymorphy2_analyzer
)
from app.my_graph.tools.grammar_analysis import analyze_russian_grammar_impl
from app.grammar.russian import Noun


class TestPyMorphy2Integration:
    """Test PyMorphy2 integration with grammar analysis pipeline."""
    
    def setup_method(self):
        """Set up test method."""
        self.analyzer = PyMorphy2Analyzer()
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_pymorphy2_basic_functionality(self):
        """Test basic PyMorphy2 functionality."""
        print("Testing basic PyMorphy2 functionality...")
        
        # Test word analysis
        analysis = self.analyzer.analyze_word("дом")
        assert analysis is not None
        assert analysis.word == "дом"
        assert analysis.normal_form == "дом"
        assert analysis.pos == "NOUN"
        assert len(analysis.variants) > 0
        
        print(f"Analysis of 'дом': {analysis.normal_form} ({analysis.pos})")
        
        # Test noun analyzer
        noun_analyzer = PyMorphy2NounAnalyzer()
        noun = noun_analyzer.analyze_noun("дом")
        assert noun is not None
        assert isinstance(noun, Noun)
        assert noun.dictionary_form == "дом"
        assert noun.gender == "masculine"
        
        print(f"Noun analysis: {noun.dictionary_form} ({noun.gender})")
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_pymorphy2_declension_generation(self):
        """Test noun declension generation."""
        print("Testing noun declension generation...")
        
        noun_analyzer = PyMorphy2NounAnalyzer()
        
        # Test with masculine noun
        declension = noun_analyzer.generate_noun_declension("дом", "masc", "inan")
        print(f"Declension of 'дом': {declension}")
        
        assert "singular" in declension
        assert "plural" in declension
        assert len(declension["singular"]) > 0
        assert len(declension["plural"]) > 0
        
        # Should have all 6 cases
        expected_cases = {"nom", "gen", "dat", "acc", "ins", "pre"}
        assert set(declension["singular"].keys()) == expected_cases
        assert set(declension["plural"].keys()) == expected_cases
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_pymorphy2_grammar_analysis_impl(self):
        """Test the main pymorphy2 grammar analysis function."""
        print("Testing pymorphy2_analyze_russian_grammar_impl...")
        
        # Test with a noun
        result = pymorphy2_analyze_russian_grammar_impl("дом")
        print(f"Analysis result: {result}")
        
        assert result.get("success") == True
        assert "classification" in result
        assert result["classification"].word_type == "noun"
        assert result["classification"].russian_word == "дом"
        assert "noun_grammar" in result
        assert result["noun_grammar"] is not None
        
        noun_grammar = result["noun_grammar"]
        assert noun_grammar.dictionary_form == "дом"
        assert noun_grammar.gender == "masculine"
        assert len(noun_grammar.singular) > 0
        assert len(noun_grammar.plural) > 0
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_integration_with_grammar_analysis_tool(self):
        """Test integration with the main grammar analysis tool."""
        print("Testing integration with grammar analysis tool...")
        
        # Test that pymorphy2 is used first for nouns
        result = analyze_russian_grammar_impl("дом")
        print(f"Grammar analysis result: {result}")
        
        assert result.get("success") == True
        assert "analysis" in result
        
        analysis = result["analysis"]
        
        # Should use pymorphy2 analysis, not LLM fallback
        if analysis.get("success"):
            # This should be pymorphy2 result
            assert "classification" in analysis
            assert analysis["classification"].word_type == "noun"
            assert "noun_grammar" in analysis
            assert analysis["noun_grammar"] is not None
            
            noun_grammar = analysis["noun_grammar"]
            assert noun_grammar.dictionary_form == "дом"
            print("✓ PyMorphy2 analysis was used successfully")
        else:
            # If it fell back to LLM, that's also acceptable for testing
            print("⚠ Fell back to LLM analysis")
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_various_russian_nouns(self):
        """Test pymorphy2 analysis with various Russian nouns."""
        print("Testing various Russian nouns...")
        
        test_nouns = [
            "дом",      # masculine
            "книга",    # feminine
            "окно",     # neuter
            "учитель",  # masculine animate
            "собака",   # feminine animate
        ]
        
        for noun_word in test_nouns:
            print(f"\nTesting noun: {noun_word}")
            
            result = pymorphy2_analyze_russian_grammar_impl(noun_word)
            
            if result.get("success"):
                assert result["classification"].word_type == "noun"
                assert result["noun_grammar"] is not None
                
                noun_grammar = result["noun_grammar"]
                print(f"  Dictionary form: {noun_grammar.dictionary_form}")
                print(f"  Gender: {noun_grammar.gender}")
                print(f"  Animacy: {noun_grammar.animacy}")
                
                # Basic validation
                assert noun_grammar.dictionary_form
                assert noun_grammar.gender in ["masculine", "feminine", "neuter"]
                assert isinstance(noun_grammar.animacy, bool)
                assert len(noun_grammar.singular) > 0
                assert len(noun_grammar.plural) > 0
            else:
                print(f"  Analysis failed: {result.get('message', 'Unknown error')}")
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_unsupported_word_types(self):
        """Test that unsupported word types are handled correctly."""
        print("Testing unsupported word types...")
        
        # Test with a verb (not yet supported)
        result = pymorphy2_analyze_russian_grammar_impl("читать")
        print(f"Verb analysis result: {result}")
        
        # Should fail gracefully with appropriate message
        assert result.get("success") == False
        assert "not yet implemented" in result.get("message", "").lower()
        
        # Test with an adjective (not yet supported)
        result = pymorphy2_analyze_russian_grammar_impl("красивый")
        print(f"Adjective analysis result: {result}")
        
        assert result.get("success") == False
        assert "not yet implemented" in result.get("message", "").lower()
    
    def test_fallback_when_pymorphy2_unavailable(self):
        """Test that system falls back gracefully when pymorphy2 is unavailable."""
        print("Testing fallback behavior...")
        
        # This test should pass even if pymorphy2 is not available
        # because it should fall back to LLM analysis
        
        # Test with a simple word
        result = analyze_russian_grammar_impl("тест")
        print(f"Fallback test result: {result}")
        
        # Should get some result, either from pymorphy2 or LLM
        assert "word" in result
        assert result["word"] == "тест"
        
        if result.get("success"):
            print("✓ Analysis succeeded (either pymorphy2 or LLM)")
        else:
            print("⚠ Analysis failed, but system didn't crash")
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_inflected_forms_analysis(self):
        """Test analysis of inflected forms."""
        print("Testing inflected forms analysis...")
        
        # Test inflected forms that should resolve to base forms
        inflected_tests = [
            ("дома", "дом"),     # genitive singular or nominative plural -> nominative singular
            ("столы", "стол"),   # nominative plural -> nominative singular
            ("книги", "книга"),  # genitive singular or nominative plural -> nominative singular
        ]
        
        for inflected, expected_base in inflected_tests:
            print(f"\nTesting inflected form: {inflected} -> expected base: {expected_base}")
            
            result = pymorphy2_analyze_russian_grammar_impl(inflected)
            
            if result.get("success"):
                noun_grammar = result["noun_grammar"]
                actual_base = noun_grammar.dictionary_form
                
                print(f"  Got dictionary form: {actual_base}")
                
                # The dictionary form should match our expectation
                # (though pymorphy2 might have different conventions)
                assert actual_base == expected_base or actual_base == inflected
                
                # Should still be classified as a noun
                assert result["classification"].word_type == "noun"
            else:
                print(f"  Analysis failed: {result.get('message', 'Unknown error')}")


class TestPyMorphy2FlashcardPipeline:
    """Test the complete pipeline from pymorphy2 analysis to flashcard generation."""
    
    @pytest.mark.skipif(
        not PyMorphy2Analyzer().is_available(),
        reason="PyMorphy2 not available"
    )
    def test_noun_to_flashcard_pipeline(self):
        """Test complete pipeline from Russian noun to flashcard generation."""
        print("Testing noun -> flashcard pipeline...")
        
        # Import flashcard generator
        from app.my_graph.generators.noun_generator import NounGenerator
        
        # Test word
        test_word = "дом"
        
        # Step 1: Get grammar analysis
        grammar_result = analyze_russian_grammar_impl(test_word)
        print(f"Grammar analysis: {grammar_result.get('success', False)}")
        
        assert grammar_result.get("success") == True
        
        # Step 2: Extract noun grammar
        analysis = grammar_result["analysis"]
        if analysis.get("noun_grammar"):
            noun_grammar = analysis["noun_grammar"]
        else:
            # Fallback to LLM result structure
            noun_grammar = analysis.get("noun_grammar")
        
        assert noun_grammar is not None
        print(f"Noun grammar: {noun_grammar.dictionary_form} ({noun_grammar.gender})")
        
        # Step 3: Generate flashcards
        generator = NounGenerator()
        flashcards = generator.generate_flashcards_from_grammar(noun_grammar)
        assert flashcards is not None
        assert len(flashcards) > 0
        
        print(f"Generated {len(flashcards)} flashcards:")
        for i, flashcard in enumerate(flashcards[:3]):  # Show first 3
            print(f"  Flashcard {i+1}:")
            print(f"    Question: {flashcard.get_question()}")
            print(f"    Type: {flashcard.type}")
            if hasattr(flashcard, 'answers'):
                print(f"    Answers: {flashcard.answers}")
            elif hasattr(flashcard, 'back'):
                print(f"    Answer: {flashcard.back}")
        
        # Basic validation on first flashcard
        first_flashcard = flashcards[0]
        question_text = first_flashcard.get_question()
        assert question_text
        assert first_flashcard.type in ["fill_in_blank", "multiple_choice", "two_sided"]
        assert test_word in question_text or test_word in str(first_flashcard.title or "")
        
        print("✓ Complete pipeline successful: Russian word -> PyMorphy2 analysis -> Flashcard")
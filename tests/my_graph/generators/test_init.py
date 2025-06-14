"""Tests for generators __init__.py imports."""

import pytest


class TestGeneratorsInit:
    """Test cases for generators module imports."""

    def test_import_base_generator(self):
        """Test importing BaseGenerator."""
        from app.my_graph.generators import BaseGenerator
        assert BaseGenerator is not None

    def test_import_noun_generator(self):
        """Test importing NounGenerator."""
        from app.my_graph.generators import NounGenerator
        assert NounGenerator is not None

    def test_import_adjective_generator(self):
        """Test importing AdjectiveGenerator."""
        from app.my_graph.generators import AdjectiveGenerator
        assert AdjectiveGenerator is not None

    def test_import_verb_generator(self):
        """Test importing VerbGenerator."""
        from app.my_graph.generators import VerbGenerator
        assert VerbGenerator is not None

    def test_import_pronoun_generator(self):
        """Test importing PronounGenerator."""
        from app.my_graph.generators import PronounGenerator
        assert PronounGenerator is not None

    def test_import_number_generator(self):
        """Test importing NumberGenerator."""
        from app.my_graph.generators import NumberGenerator
        assert NumberGenerator is not None

    def test_all_exports(self):
        """Test that __all__ contains all expected exports."""
        from app.my_graph.generators import __all__
        
        expected_exports = [
            "BaseGenerator",
            "NounGenerator", 
            "AdjectiveGenerator",
            "VerbGenerator",
            "PronounGenerator",
            "NumberGenerator"
        ]
        
        assert set(__all__) == set(expected_exports)

    def test_import_all_at_once(self):
        """Test importing all generators at once."""
        from app.my_graph.generators import (
            BaseGenerator,
            NounGenerator,
            AdjectiveGenerator,
            VerbGenerator,
            PronounGenerator,
            NumberGenerator
        )
        
        # Verify all classes are available
        assert BaseGenerator is not None
        assert NounGenerator is not None
        assert AdjectiveGenerator is not None
        assert VerbGenerator is not None
        assert PronounGenerator is not None
        assert NumberGenerator is not None

    def test_generator_inheritance(self):
        """Test that all generators inherit from BaseGenerator."""
        from app.my_graph.generators import (
            BaseGenerator,
            NounGenerator,
            AdjectiveGenerator,
            VerbGenerator,
            PronounGenerator,
            NumberGenerator
        )
        
        # Check inheritance
        assert issubclass(NounGenerator, BaseGenerator)
        assert issubclass(AdjectiveGenerator, BaseGenerator)
        assert issubclass(VerbGenerator, BaseGenerator)
        assert issubclass(PronounGenerator, BaseGenerator)
        assert issubclass(NumberGenerator, BaseGenerator)

    def test_generator_instantiation(self):
        """Test that all generators can be instantiated."""
        from app.my_graph.generators import (
            BaseGenerator,
            NounGenerator,
            AdjectiveGenerator,
            VerbGenerator,
            PronounGenerator,
            NumberGenerator
        )
        
        # Test instantiation
        base_gen = BaseGenerator()
        noun_gen = NounGenerator()
        adj_gen = AdjectiveGenerator()
        verb_gen = VerbGenerator()
        pronoun_gen = PronounGenerator()
        number_gen = NumberGenerator()
        
        # Verify instances
        assert isinstance(base_gen, BaseGenerator)
        assert isinstance(noun_gen, NounGenerator)
        assert isinstance(adj_gen, AdjectiveGenerator)
        assert isinstance(verb_gen, VerbGenerator)
        assert isinstance(pronoun_gen, PronounGenerator)
        assert isinstance(number_gen, NumberGenerator)
        
        # Verify inheritance
        assert isinstance(noun_gen, BaseGenerator)
        assert isinstance(adj_gen, BaseGenerator)
        assert isinstance(verb_gen, BaseGenerator)
        assert isinstance(pronoun_gen, BaseGenerator)
        assert isinstance(number_gen, BaseGenerator)

    def test_module_docstring(self):
        """Test that the module has a proper docstring."""
        import app.my_graph.generators as generators_module
        
        assert generators_module.__doc__ is not None
        assert "generators" in generators_module.__doc__.lower()

    def test_direct_module_access(self):
        """Test direct access to generators through module."""
        import app.my_graph.generators as generators
        
        # Test direct access
        assert hasattr(generators, 'BaseGenerator')
        assert hasattr(generators, 'NounGenerator')
        assert hasattr(generators, 'AdjectiveGenerator')
        assert hasattr(generators, 'VerbGenerator')
        assert hasattr(generators, 'PronounGenerator')
        assert hasattr(generators, 'NumberGenerator')

    def test_star_import(self):
        """Test that star import works correctly."""
        # This is a bit tricky to test directly, but we can verify
        # that the __all__ list matches what's actually exported
        import app.my_graph.generators as generators
        
        # Get all public attributes that don't start with underscore
        public_attrs = [attr for attr in dir(generators) 
                       if not attr.startswith('_') and 
                       attr[0].isupper()]  # Classes start with uppercase
        
        # Should match __all__ (minus any imports that aren't in __all__)
        all_exports = generators.__all__
        
        # All items in __all__ should be in public attributes
        for export in all_exports:
            assert export in public_attrs
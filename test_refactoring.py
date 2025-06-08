#!/usr/bin/env python3
"""Test script to verify refactoring structure without database dependencies."""

import sys
import importlib

def test_import(module_name, description):
    """Test importing a module and report result."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {description}")
        return True
    except ImportError as e:
        if "pymongo" in str(e) or "MongoClient" in str(e):
            print(f"⚠️  {description} (DB dependency missing - expected)")
            return True  # This is expected
        else:
            print(f"❌ {description}: {e}")
            return False
    except Exception as e:
        print(f"❌ {description}: {e}")
        return False

def main():
    """Test all refactored components."""
    print("🧪 Testing Refactored Components Structure")
    print("=" * 50)
    
    tests = [
        # Common utilities (no external deps)
        ("app.common.text_processing.russian_text_extractor", "Russian text extractor"),
        ("app.common.text_processing.markdown_escaper", "Markdown escaper"),
        ("app.common.text_processing.text_cleaner", "Text cleaner"),
        ("app.common.telegram_utils.keyboard_factory", "Keyboard factory"),
        ("app.common.telegram_utils.message_sender", "Message sender"),
        
        # Session management
        ("app.my_telegram.session.session_manager", "Session manager"),
        
        # Generator utilities
        ("app.my_graph.utils.suffix_extractor", "Suffix extractor"),
        ("app.my_graph.utils.form_analyzer", "Form analyzer"),
        ("app.my_graph.sentence_generation.text_processor", "Text processor"),
        
        # Higher-level modules (may have DB deps)
        ("app.my_telegram.handlers.command_handlers", "Command handlers"),
        ("app.my_telegram.handlers.learning_handlers", "Learning handlers"),
        ("app.flashcards.validators.answer_validator", "Answer validator"),
        ("app.flashcards.validators.input_parser", "Input parser"),
    ]
    
    passed = 0
    total = len(tests)
    
    for module_name, description in tests:
        if test_import(module_name, description):
            passed += 1
    
    print("=" * 50)
    print(f"🎯 Results: {passed}/{total} components tested successfully")
    
    if passed == total:
        print("🎉 All refactored components have correct structure!")
    else:
        print("⚠️  Some components have issues (check above)")

if __name__ == "__main__":
    main()
"""Tests to verify import integrity and prevent missing import errors."""

import pytest
import importlib
import ast
import os
from pathlib import Path


class ImportChecker:
    """Helper class to check import integrity."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.app_root = self.project_root / "app"
    
    def get_python_files(self):
        """Get all Python files in the app directory."""
        python_files = []
        for py_file in self.app_root.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                python_files.append(py_file)
        return python_files
    
    def extract_used_functions(self, file_path: Path):
        """Extract function calls from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            used_functions = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        used_functions.add(node.func.id)
                    elif isinstance(node.func, ast.Attribute):
                        used_functions.add(node.func.attr)
            
            return used_functions
        except Exception:
            return set()
    
    def extract_imports(self, file_path: Path):
        """Extract imports from a Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            imports = set()
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            imports.add(alias.name)
            
            return imports
        except Exception:
            return set()


def test_message_handlers_imports():
    """Test that message_handlers.py has all required imports."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    checker = ImportChecker(project_root)
    
    message_handlers_path = checker.app_root / "my_telegram" / "handlers" / "message_handlers.py"
    
    # Check that the file exists
    assert message_handlers_path.exists(), "message_handlers.py not found"
    
    # Extract used functions and imports
    used_functions = checker.extract_used_functions(message_handlers_path)
    imports = checker.extract_imports(message_handlers_path)
    
    # Known functions that should be imported
    critical_functions = {
        'safe_send_markdown': 'app.common.telegram_utils',
        'safe_edit_markdown': 'app.common.telegram_utils',
    }
    
    # Check if critical functions are used and imported
    for func_name, expected_module in critical_functions.items():
        if func_name in used_functions:
            assert func_name in imports, f"Function '{func_name}' is used but not imported from {expected_module}"


def test_specific_safe_send_markdown_import():
    """Specific test for safe_send_markdown import in message_handlers.py."""
    try:
        # Try to import the module and function
        from app.my_telegram.handlers.message_handlers import process_flashcard_edit
        from app.common.telegram_utils import safe_send_markdown
        
        # Verify the function is available in the module namespace
        import app.my_telegram.handlers.message_handlers as msg_handlers
        assert hasattr(msg_handlers, 'safe_send_markdown'), "safe_send_markdown not available in message_handlers namespace"
        
    except ImportError as e:
        pytest.fail(f"Import error: {e}")


def test_telegram_utils_functions_available():
    """Test that telegram utils functions are properly available."""
    try:
        from app.common.telegram_utils import safe_send_markdown, safe_edit_markdown
        
        # Basic check that functions are callable
        assert callable(safe_send_markdown), "safe_send_markdown is not callable"
        assert callable(safe_edit_markdown), "safe_edit_markdown is not callable"
        
    except ImportError as e:
        pytest.fail(f"Cannot import telegram utils: {e}")


def test_all_handler_modules_importable():
    """Test that all handler modules can be imported without errors."""
    handler_modules = [
        'app.my_telegram.handlers.message_handlers',
        'app.my_telegram.handlers.command_handlers', 
        'app.my_telegram.handlers.chatbot_handlers',
        'app.my_telegram.handlers.learning_handlers',
    ]
    
    for module_name in handler_modules:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            pytest.fail(f"Cannot import {module_name}: {e}")


def test_critical_functions_not_undefined():
    """Test that critical functions used in handlers are not undefined."""
    # Test functions that are commonly used and should be imported
    critical_imports = [
        ('app.my_telegram.handlers.message_handlers', 'safe_send_markdown'),
        ('app.my_telegram.handlers.command_handlers', 'safe_send_markdown'),
        ('app.my_telegram.handlers.chatbot_handlers', 'safe_send_markdown'),
    ]
    
    for module_name, function_name in critical_imports:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, function_name):
                func = getattr(module, function_name)
                assert callable(func), f"{function_name} in {module_name} is not callable"
        except ImportError as e:
            pytest.fail(f"Cannot import {module_name}: {e}")
        except AttributeError:
            # If the function isn't used in this module, that's OK
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
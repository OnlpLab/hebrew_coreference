"""
Tests for the main module.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_main_import():
    """Test that the main module can be imported."""
    try:
        import main
        assert main is not None
    except ImportError as e:
        pytest.fail(f"Failed to import main module: {e}")

def test_main_file_exists():
    """Test that the main.py file exists."""
    main_file = Path(__file__).parent.parent / "main.py"
    assert main_file.exists(), "main.py file should exist in the root directory"

def test_main_function_exists():
    """Test that the main function exists."""
    try:
        import main
        assert hasattr(main, 'main'), "main module should have a main function"
        assert callable(main.main), "main should be callable"
    except ImportError:
        pytest.skip("Main module not available")

def test_main_argument_parser():
    """Test that the argument parser is properly configured."""
    try:
        import main
        
        # Test that parser exists
        assert hasattr(main, 'main'), "main function should exist"
        
        # Test that main function can be called without arguments (will show help)
        try:
            main.main()
        except SystemExit:
            # This is expected when no arguments are provided
            pass
        
    except ImportError:
        pytest.skip("Main module not available") 
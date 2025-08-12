"""
Tests for the configuration module.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_config_import():
    """Test that the config module can be imported."""
    try:
        import config
        assert config is not None
    except ImportError as e:
        pytest.fail(f"Failed to import config module: {e}")

def test_config_variables():
    """Test that essential config variables are defined."""
    try:
        import config
        
        # Check if basic config structure exists
        assert hasattr(config, '__file__'), "Config module should have __file__ attribute"
        
        # Check if any config variables are defined
        config_vars = [var for var in dir(config) if not var.startswith('_')]
        assert len(config_vars) > 0, "Config module should have some configuration variables"
        
    except ImportError:
        pytest.skip("Config module not available")

def test_config_file_exists():
    """Test that the config.py file exists."""
    config_file = Path(__file__).parent.parent / "config.py"
    assert config_file.exists(), "config.py file should exist in the root directory" 
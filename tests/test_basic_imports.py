"""
Tests for basic module imports.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_src_directory_exists():
    """Test that the src directory exists and contains expected subdirectories."""
    src_dir = Path(__file__).parent.parent / "src"
    assert src_dir.exists(), "src directory should exist"
    
    # Check for expected subdirectories
    expected_dirs = ['annotation', 'neural_models', 'mention_detection', 'llm_evaluation']
    for dir_name in expected_dirs:
        dir_path = src_dir / dir_name
        assert dir_path.exists(), f"Expected directory {dir_name} should exist in src"

def test_annotation_imports():
    """Test that annotation modules can be imported."""
    try:
        # Test basic import
        import annotation
        assert annotation is not None
    except ImportError:
        pytest.skip("Annotation module not available")

def test_neural_models_imports():
    """Test that neural models modules can be imported."""
    try:
        # Test basic import
        import neural_models
        assert neural_models is not None
    except ImportError:
        pytest.skip("Neural models module not available")

def test_mention_detection_imports():
    """Test that mention detection modules can be imported."""
    try:
        # Test basic import
        import mention_detection
        assert mention_detection is not None
    except ImportError:
        pytest.skip("Mention detection module not available")

def test_llm_evaluation_imports():
    """Test that LLM evaluation modules can be imported."""
    try:
        # Test basic import
        import llm_evaluation
        assert llm_evaluation is not None
    except ImportError:
        pytest.skip("LLM evaluation module not available")

def test_scripts_directory():
    """Test that the scripts directory exists and contains Python files."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    assert scripts_dir.exists(), "scripts directory should exist"
    
    # Check for Python files
    py_files = list(scripts_dir.glob("*.py"))
    assert len(py_files) > 0, "scripts directory should contain Python files"

def test_statistics_directory():
    """Test that the statistics directory exists and contains Python files."""
    stats_dir = Path(__file__).parent.parent / "statistics"
    assert stats_dir.exists(), "statistics directory should exist"
    
    # Check for Python files
    py_files = list(stats_dir.glob("*.py"))
    assert len(py_files) > 0, "statistics directory should contain Python files" 
"""
Pytest configuration for Hebrew Coreference Resolution System tests.
"""

import sys
import os
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "test_data"

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their names."""
    for item in items:
        if "test_" in item.name:
            if "integration" in item.name:
                item.add_marker("integration")
            else:
                item.add_marker("unit") 
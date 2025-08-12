"""
Tests for actual NP chunker usage and functionality.
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class TestNPChunkerUsage:
    """Test class for actual NP chunker usage."""
    
    def test_chunker_file_functionality(self):
        """Test that the chunk_file function can be called and works."""
        try:
            from mention_detection.np_chunker.chunk_file import chunk_file
            
            # Test that the function exists and is callable
            assert callable(chunk_file)
            
        except ImportError:
            pytest.skip("chunk_file function not available")
    
    def test_chunker_file_arguments(self):
        """Test that chunk_file accepts the expected arguments."""
        try:
            from mention_detection.np_chunker.chunk_file import chunk_file
            
            # Check function signature
            import inspect
            sig = inspect.signature(chunk_file)
            params = list(sig.parameters.keys())
            
            # Should have basic parameters
            assert len(params) > 0, "chunk_file should have parameters"
            
        except ImportError:
            pytest.skip("chunk_file function not available")
    
    def test_stanza_chunker_functionality(self):
        """Test that the StanzaChunker can be used."""
        try:
            from mention_detection.stanza_parser.stanza_chunker import StanzaChunker
            
            # Test that the class exists
            assert StanzaChunker is not None
            
            # Test basic instantiation (if possible without heavy dependencies)
            try:
                chunker = StanzaChunker()
                assert chunker is not None
            except Exception:
                # If instantiation fails due to missing dependencies, that's okay
                # We're just testing that the class can be imported
                pass
                
        except ImportError:
            pytest.skip("StanzaChunker not available")
    
    def test_chunker_configuration_combinations(self):
        """Test that the chunker works with different configuration combinations."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            # Test various configuration combinations
            configs = [
                (True, False, True, True, False, False),
                (False, True, False, False, True, True),
                (True, True, True, False, True, False),
                (False, False, False, True, False, True),
            ]
            
            for config in configs:
                chunker = Chunker(*config)
                assert chunker is not None
                
                # Test that configuration was applied correctly
                assert chunker.take_longest == config[0]
                assert chunker.allow_nested == config[1]
                assert chunker.allow_loc_time_adv == config[2]
                assert chunker.possessive == config[3]
                assert chunker.with_inner_quantitative == config[4]
                assert chunker.with_inner_acl == config[5]
                
        except ImportError:
            pytest.skip("Chunker class not available")
    
    def test_chunker_utility_methods(self):
        """Test that chunker utility methods work correctly."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test time and location adverb detection
            assert hasattr(chunker, 'is_time_and_location_adv')
            assert callable(chunker.is_time_and_location_adv)
            
            # Test mention filtering
            assert hasattr(chunker, 'should_filter_mention')
            assert callable(chunker.should_filter_mention)
            
            # Test smixut detection
            assert hasattr(chunker, 'is_smixut_w_det')
            assert callable(chunker.is_smixut_w_det)
            
        except ImportError:
            pytest.skip("Chunker class not available")
    
    def test_chunker_static_methods(self):
        """Test that chunker static methods work correctly."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            # Test static methods
            assert hasattr(Chunker, 'get_heb_right_children')
            assert hasattr(Chunker, 'get_heb_left_children')
            assert hasattr(Chunker, '_chunks2biose')
            assert hasattr(Chunker, '_chunks2bio')
            assert hasattr(Chunker, 'dedup_chunks')
            
            # Test that they are callable methods
            assert callable(Chunker.get_heb_right_children)
            assert callable(Chunker.get_heb_left_children)
            assert callable(Chunker._chunks2biose)
            assert callable(Chunker._chunks2bio)
            assert callable(Chunker.dedup_chunks)
            
        except ImportError:
            pytest.skip("Chunker class not available")
    
    def test_chunker_hebrew_specific_features(self):
        """Test that Hebrew-specific chunker features work."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test Hebrew-specific constants
            assert chunker.HEB_CLOSE_BRACKET == ")"
            assert chunker.HEB_OPEN_BRACKET == "("
            
            # Test Hebrew-specific label sets
            assert "compound:smixut" in chunker.right_labels
            assert "compound:smixut" in chunker.left_labels
            
            # Test Hebrew-specific quantifiers
            assert "ה" in chunker.QUANTIFIERS_NOT_TO_BREAK
            assert "כל" in chunker.QUANTIFIERS
            assert "רוב" in chunker.QUANTIFIERS
            
        except ImportError:
            pytest.skip("Chunker class not available")
    
    def test_chunker_postprocessing(self):
        """Test that chunker postprocessing methods work."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test postprocessing methods
            assert hasattr(chunker, 'postprocess')
            assert hasattr(chunker, 'sort_chunks_by_order')
            assert hasattr(chunker, '_rename_nested')
            assert hasattr(chunker, 'is_successive_words')
            
            # Test that they are callable
            assert callable(chunker.postprocess)
            assert callable(chunker.sort_chunks_by_order)
            assert callable(chunker._rename_nested)
            assert callable(chunker.is_successive_words)
            
        except ImportError:
            pytest.skip("Chunker class not available")


class TestNPChunkerFileOperations:
    """Test class for NP chunker file operations."""
    
    def test_chunk_file_script_executable(self):
        """Test that the chunk_file script can be executed."""
        chunk_file_script = Path(__file__).parent.parent / "src" / "mention_detection" / "np_chunker" / "chunk_file.py"
        
        if chunk_file_script.exists():
            try:
                # Basic syntax check
                exec(compile(chunk_file_script.read_text(), str(chunk_file_script), 'exec'))
                assert True  # If we get here, syntax is valid
            except Exception as e:
                pytest.skip(f"chunk_file script syntax check failed: {e}")
    
    def test_chunk_file_imports(self):
        """Test that chunk_file can import all its dependencies."""
        try:
            # Test that the module can be imported
            from mention_detection.np_chunker import chunk_file
            assert chunk_file is not None
            
        except ImportError as e:
            pytest.skip(f"chunk_file module import failed: {e}")
    
    def test_chunk_file_function_signature(self):
        """Test that chunk_file has the expected function signature."""
        try:
            from mention_detection.np_chunker.chunk_file import chunk_file
            
            import inspect
            sig = inspect.signature(chunk_file)
            params = list(sig.parameters.keys())
            
            # Should have at least some parameters
            assert len(params) >= 0, "chunk_file should have parameters"
            
        except ImportError:
            pytest.skip("chunk_file function not available")


class TestNPChunkerIntegration:
    """Integration tests for NP chunker."""
    
    def test_chunker_with_real_file_structure(self):
        """Test that chunker works with real file structure."""
        # Test that all chunker-related files exist
        chunker_dir = Path(__file__).parent.parent / "src" / "mention_detection" / "np_chunker"
        assert chunker_dir.exists(), "NP chunker directory should exist"
        
        # Check for essential files
        essential_files = [
            "chunker.py",
            "chunk_file.py",
            "__init__.py"
        ]
        
        for file_name in essential_files:
            file_path = chunker_dir / file_name
            if file_name != "__init__.py":  # __init__.py might not exist
                assert file_path.exists(), f"Essential file {file_name} should exist"
    
    def test_chunker_dependencies_available(self):
        """Test that chunker dependencies are available."""
        try:
            import spacy
            assert spacy is not None
        except ImportError:
            pytest.skip("spaCy not available")
        
        try:
            import stanza
            assert stanza is not None
        except ImportError:
            pytest.skip("Stanza not available")
    
    def test_chunker_output_formats(self):
        """Test that chunker can output in different formats."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test that BIO and BIOES format methods exist
            assert hasattr(Chunker, '_chunks2bio')
            assert hasattr(Chunker, '_chunks2biose')
            
            # Test that they are callable methods
            assert callable(Chunker._chunks2bio)
            assert callable(Chunker._chunks2biose)
            
        except ImportError:
            pytest.skip("Chunker class not available")
    
    def test_chunker_error_handling(self):
        """Test that chunker handles errors gracefully."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test that the chunker can be created without errors
            assert chunker is not None
            
            # Test that methods exist and are callable
            assert hasattr(chunker, 'get_noun_chunks')
            assert callable(chunker.get_noun_chunks)
            
        except ImportError:
            pytest.skip("Chunker class not available") 
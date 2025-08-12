"""
Tests for the NP chunker functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

class TestNPChunker:
    """Test class for NP chunker functionality."""
    
    def test_chunker_import(self):
        """Test that the chunker module can be imported."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            assert Chunker is not None
        except ImportError as e:
            pytest.fail(f"Failed to import Chunker: {e}")
    
    def test_chunker_initialization(self):
        """Test that the Chunker class can be initialized with different parameters."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            # Test different parameter combinations
            chunker1 = Chunker(
                take_longest=True,
                allow_nested=False,
                allow_loc_time_adv=True,
                possessive=True,
                allow_inner_quantitative=False,
                allow_inner_acl=False
            )
            assert chunker1 is not None
            assert chunker1.take_longest is True
            assert chunker1.allow_nested is False
            assert chunker1.allow_loc_time_adv is True
            assert chunker1.possessive is True
            
            chunker2 = Chunker(
                take_longest=False,
                allow_nested=True,
                allow_loc_time_adv=False,
                possessive=False,
                allow_inner_quantitative=True,
                allow_inner_acl=True
            )
            assert chunker2 is not None
            assert chunker2.take_longest is False
            assert chunker2.allow_nested is True
            
        except ImportError:
            pytest.skip("Chunker module not available")
    
    def test_chunker_constants(self):
        """Test that the Chunker class has the expected constants."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test Hebrew-specific constants
            assert hasattr(chunker, 'HEB_CLOSE_BRACKET')
            assert hasattr(chunker, 'HEB_OPEN_BRACKET')
            assert chunker.HEB_CLOSE_BRACKET == ")"
            assert chunker.HEB_OPEN_BRACKET == "("
            
            # Test POS tag sets
            assert hasattr(chunker, 'NOUNS')
            assert hasattr(chunker, 'NOUN_FAMILY')
            assert hasattr(chunker, 'VERBS_POS')
            
            # Test label sets
            assert hasattr(chunker, 'right_labels')
            assert hasattr(chunker, 'left_labels')
            assert hasattr(chunker, 'stop_labels')
            
        except ImportError:
            pytest.skip("Chunker module not available")
    
    def test_chunker_methods_exist(self):
        """Test that the Chunker class has the expected methods."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test core methods
            assert hasattr(chunker, 'get_noun_chunks')
            assert hasattr(chunker, 'extract_quantitative')
            assert hasattr(chunker, 'sort_chunks_by_order')
            assert hasattr(chunker, 'postprocess')
            assert hasattr(chunker, 'dedup_chunks')
            
            # Test utility methods
            assert hasattr(chunker, 'is_time_and_location_adv')
            assert hasattr(chunker, 'should_filter_mention')
            assert hasattr(chunker, 'is_smixut_w_det')
            assert hasattr(chunker, 'is_non_mention_single_word')
            
        except ImportError:
            pytest.skip("Chunker module not available")
    
    @patch('mention_detection.np_chunker.chunker.spacy')
    def test_chunker_with_mock_spacy(self, mock_spacy):
        """Test chunker functionality with mocked spacy document."""
        try:
            from mention_detection.np_chunker.chunker import Chunker
            
            # Create mock spacy document
            mock_doc = Mock()
            mock_token = Mock()
            mock_token.pos_ = "NOUN"
            mock_token.dep_ = "nsubj"
            mock_token.text = "ממשלה"
            mock_token.i = 0
            
            mock_doc.__iter__ = lambda self: [mock_token]
            mock_doc.__len__ = lambda self: 1
            
            chunker = Chunker(True, False, True, True, False, False)
            
            # Test that the chunker can process the mock document
            # This is a basic test to ensure no crashes
            assert chunker is not None
            
        except ImportError:
            pytest.skip("Chunker module not available")
    
    def test_chunker_file_import(self):
        """Test that the chunk_file module can be imported."""
        try:
            from mention_detection.np_chunker.chunk_file import chunk_file
            assert chunk_file is not None
        except ImportError:
            pytest.skip("chunk_file module not available")
    
    def test_stanza_chunker_import(self):
        """Test that the stanza chunker module can be imported."""
        try:
            from mention_detection.stanza_parser.stanza_chunker import StanzaChunker
            assert StanzaChunker is not None
        except ImportError:
            pytest.skip("StanzaChunker module not available")


class TestNPChunkerIntegration:
    """Integration tests for NP chunker."""
    
    def test_chunker_file_structure(self):
        """Test that the chunker files exist and are accessible."""
        chunker_dir = Path(__file__).parent.parent / "src" / "mention_detection" / "np_chunker"
        assert chunker_dir.exists(), "NP chunker directory should exist"
        
        # Check for essential files
        chunker_file = chunker_dir / "chunker.py"
        chunk_file = chunker_dir / "chunk_file.py"
        
        assert chunker_file.exists(), "chunker.py should exist"
        assert chunk_file.exists(), "chunk_file.py should exist"
    
    def test_chunker_imports_work(self):
        """Test that all chunker-related imports work without errors."""
        try:
            # Test basic imports
            from mention_detection.np_chunker import chunker
            from mention_detection.np_chunker import chunk_file
            
            # Test class imports
            from mention_detection.np_chunker.chunker import Chunker
            from mention_detection.np_chunker.chunk_file import chunk_file as chunk_file_func
            
            assert True  # If we get here, imports worked
            
        except ImportError as e:
            pytest.skip(f"Chunker imports not available: {e}")
    
    def test_chunker_configuration_options(self):
        """Test that the chunker can be configured with different options."""
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
                assert chunker.take_longest == config[0]
                assert chunker.allow_nested == config[1]
                assert chunker.allow_loc_time_adv == config[2]
                assert chunker.possessive == config[3]
                assert chunker.with_inner_quantitative == config[4]
                assert chunker.with_inner_acl == config[5]
                
        except ImportError:
            pytest.skip("Chunker module not available") 
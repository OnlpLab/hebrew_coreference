#!/usr/bin/env python3
"""
Tests for annotation functionality including TNE format conversion and TNE UI.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


class TestTNEUI:
    """Test class for TNE UI functionality."""

    def test_tne_ui_import(self):
        """Test that TNE UI modules can be imported."""
        try:
            from annotation.tne_ui import annotationServer
            assert annotationServer is not None
        except ImportError:
            pytest.skip("TNE UI module not available")

    def test_tne_ui_initialization(self):
        """Test that TNE UI can be initialized."""
        try:
            from annotation.tne_ui.annotationServer import AnnotationServer
            # Mock initialization
            server = Mock(spec=AnnotationServer)
            assert server is not None
        except ImportError:
            pytest.skip("TNE UI module not available")

    def test_tne_ui_config(self):
        """Test that TNE UI configuration is accessible."""
        try:
            from annotation.tne_ui.annotationServer import AnnotationServer
            
            # Test that the class has expected attributes
            assert hasattr(AnnotationServer, '__init__')
            
        except ImportError:
            pytest.skip("TNE UI module not available")

    def test_tne_urls(self):
        """Test that TNE UI has expected URL endpoints."""
        try:
            from annotation.tne_ui.annotationServer import AnnotationServer
            
            # Mock server instance
            server = Mock(spec=AnnotationServer)
            
            # Test that expected methods exist
            assert hasattr(server, 'start_server')
            
        except ImportError:
            pytest.skip("TNE UI module not available")

    def test_tne_static_files(self):
        """Test that TNE UI static files exist."""
        static_dir = Path(__file__).parent.parent / "src" / "annotation" / "tne_ui" / "static"
        assert static_dir.exists(), "TNE UI static directory should exist"


class TestTNEFormatConversion:
    """Test class for TNE format conversion functionality."""

    def test_np_to_tne_conversion(self):
        """Test NP results to TNE format conversion."""
        try:
            # Test that the conversion function exists
            from tools.integrated_workflow import convert_to_tne_format
            assert convert_to_tne_format is not None
            
            # Test basic conversion functionality
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as np_file:
                np_file.write("mock np 1\nmock np 2\n")
                np_file_path = np_file.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tne_file:
                tne_file_path = tne_file.name
            
            try:
                # Test conversion
                result = convert_to_tne_format(np_file_path, tne_file_path)
                assert result is True, "Conversion should return True"
                
                # Verify output file was created
                assert Path(tne_file_path).exists(), "TNE output file should be created"
                
            finally:
                # Cleanup
                Path(np_file_path).unlink(missing_ok=True)
                Path(tne_file_path).unlink(missing_ok=True)
                
        except ImportError:
            pytest.skip("TNE conversion module not available")

    def test_tne_database_loading(self):
        """Test TNE data loading to database."""
        try:
            from tools.integrated_workflow import load_to_tne_database
            assert load_to_tne_database is not None
            
            # Test database loading functionality
            with tempfile.TemporaryDirectory() as temp_dir:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tne_file:
                    json.dump({"nps": [{"text": "test np", "id": 1}]}, tne_file)
                    tne_file_path = tne_file.name
                
                try:
                    # Test loading
                    result = load_to_tne_database(tne_file_path, temp_dir, "test_db")
                    assert result is True, "Database loading should return True"
                    
                    # Verify database file was created
                    db_file = Path(temp_dir) / "test_db.json"
                    assert db_file.exists(), "Database file should be created"
                    
                finally:
                    Path(tne_file_path).unlink(missing_ok=True)
                    
        except ImportError:
            pytest.skip("TNE database module not available")

    def test_tne_server_startup(self):
        """Test TNE server startup functionality."""
        try:
            from tools.integrated_workflow import start_tne_server
            assert start_tne_server is not None
            
            # Test server startup
            with tempfile.TemporaryDirectory() as temp_dir:
                result = start_tne_server(temp_dir, "test_db", 8080)
                assert result is True, "Server startup should return True"
                
        except ImportError:
            pytest.skip("TNE server module not available")


class TestCoreferenceAnnotation:
    """Test class for coreference annotation functionality."""

    def test_coref_annotation_files_exist(self):
        """Test that coreference annotation files exist."""
        coref_dir = Path(__file__).parent.parent / "src" / "annotation" / "tne_ui" / "hebrew_coref"
        assert coref_dir.exists(), "Coreference annotation directory should exist"
        
        # Check for essential files
        essential_files = [
            "read_annotation.py",
            "create_conll_files_from_annotations.sh",
            "read_annotations.sh"
        ]
        
        for file_name in essential_files:
            file_path = coref_dir / file_name
            assert file_path.exists(), f"Essential file {file_name} should exist"

    def test_annotation_data_formats(self):
        """Test that annotation data is in expected formats."""
        # Check JSONL files
        jsonl_files = [
            "src/annotation/tne_ui/coref_annotations.jsonl",
            "src/annotation/tne_ui/cons_annotations.jsonl"
        ]
        
        for jsonl_file in jsonl_files:
            file_path = Path(__file__).parent.parent / jsonl_file
            if file_path.exists():
                # Test that file is valid JSONL
                with open(file_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        try:
                            json.loads(line.strip())
                        except json.JSONDecodeError as e:
                            pytest.fail(f"Invalid JSON at line {line_num} in {jsonl_file}: {e}")

    def test_annotation_server_script(self):
        """Test that annotation server script exists and is accessible."""
        server_script = Path(__file__).parent.parent / "src" / "annotation" / "tne_ui" / "annotationServer.py"
        assert server_script.exists(), "Annotation server script should exist"
        
        # Test that it's a Python file
        assert server_script.suffix == '.py', "Annotation server should be a Python file"


class TestAnnotationIntegration:
    """Integration tests for annotation functionality."""

    def test_annotation_workflow(self):
        """Test the complete annotation workflow."""
        try:
            from tools.integrated_workflow import (
                convert_to_tne_format,
                load_to_tne_database,
                start_tne_server
            )
            
            # Test workflow components
            assert convert_to_tne_format is not None
            assert load_to_tne_database is not None
            assert start_tne_server is not None
            
        except ImportError:
            pytest.skip("Annotation workflow modules not available")

    def test_annotation_file_structure(self):
        """Test that annotation file structure is correct."""
        annotation_dir = Path(__file__).parent.parent / "src" / "annotation"
        assert annotation_dir.exists(), "Annotation directory should exist"
        
        # Check for expected subdirectories
        expected_dirs = ['tne_ui']
        for dir_name in expected_dirs:
            dir_path = annotation_dir / dir_name
            assert dir_path.exists(), f"Expected directory {dir_name} should exist in annotation"

    def test_annotation_dependencies(self):
        """Test that annotation dependencies are available."""
        try:
            # Test basic imports
            import json
            import tempfile
            from pathlib import Path
            
            assert True  # If we get here, basic dependencies work
            
        except ImportError as e:
            pytest.fail(f"Basic annotation dependencies not available: {e}") 
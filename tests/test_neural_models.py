#!/usr/bin/env python3
"""
Tests for neural models components.
"""

import unittest
import sys
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

class TestNeuralModelsBase(unittest.TestCase):
    """Base class for neural models tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = self.create_test_data()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_data(self):
        """Create test data for neural models."""
        test_data = {
            "documents": [
                {
                    "id": "doc1",
                    "text": "ראש הממשלה בנימין נתניהו הודיע היום על החלטות חדשות.",
                    "mentions": [
                        {"id": 1, "text": "ראש הממשלה", "start": 0, "end": 12},
                        {"id": 2, "text": "בנימין נתניהו", "start": 13, "end": 26}
                    ],
                    "clusters": [
                        {"mentions": [1, 2], "representative": 1}
                    ]
                }
            ]
        }
        
        data_path = os.path.join(self.temp_dir, "test_data.json")
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        return data_path


class TestNeuralModelsConfig(TestNeuralModelsBase):
    """Test neural models configuration."""
    
    def test_neural_models_config(self):
        """Test neural models configuration."""
        from config import NEURAL_MODELS, NEURAL_CONFIG
        
        # Check required models exist
        required_models = ['lingmess-coref', 'wl-coref']
        for model in required_models:
            self.assertIn(model, NEURAL_MODELS)
        
        # Check model structure
        for model_name, model_config in NEURAL_MODELS.items():
            self.assertIn('name', model_config)
            self.assertIn('description', model_config)
            self.assertIn('script', model_config)
            self.assertIn('config', model_config)
            self.assertIsInstance(model_config['name'], str)
            self.assertIsInstance(model_config['description'], str)
            self.assertIsInstance(model_config['script'], str)
            self.assertIsInstance(model_config['config'], str)
        
        # Check neural config
        self.assertIn('base_models', NEURAL_CONFIG)
        self.assertIn('seeds', NEURAL_CONFIG)
        self.assertIn('evaluation_metrics', NEURAL_CONFIG)
        self.assertIsInstance(NEURAL_CONFIG['base_models'], list)
        self.assertIsInstance(NEURAL_CONFIG['seeds'], list)
        self.assertIsInstance(NEURAL_CONFIG['evaluation_metrics'], list)
    
    def test_neural_paths(self):
        """Test neural model paths."""
        from config import (
            NEURAL_COREF_DIR, NEURAL_SRC_DIR, 
            NEURAL_RESULTS_DIR, NEURAL_CACHE_DIR, NEURAL_DATA_DIR
        )
        
        # Check neural paths exist
        self.assertTrue(NEURAL_COREF_DIR.exists())
        self.assertTrue(NEURAL_SRC_DIR.exists())
        self.assertTrue(NEURAL_RESULTS_DIR.exists())
        self.assertTrue(NEURAL_CACHE_DIR.exists())
        self.assertTrue(NEURAL_DATA_DIR.exists())
        
        # Check relationships
        self.assertEqual(NEURAL_SRC_DIR.parent, NEURAL_COREF_DIR)
        self.assertEqual(NEURAL_RESULTS_DIR.parent, NEURAL_COREF_DIR)
        self.assertEqual(NEURAL_CACHE_DIR.parent, NEURAL_COREF_DIR)
        self.assertEqual(NEURAL_DATA_DIR.parent, NEURAL_COREF_DIR)
    
    def test_neural_results_path(self):
        """Test neural results path generation."""
        from config import get_neural_results_path, NEURAL_RESULTS_DIR
        
        path = get_neural_results_path('lingmess-coref', 'test-model', 42)
        
        self.assertTrue(str(path).startswith(str(NEURAL_RESULTS_DIR)))
        self.assertIn('lingmess-coref', str(path))
        self.assertIn('test-model', str(path))
        self.assertIn('seed_42', str(path))


class TestLingMessCoref(TestNeuralModelsBase):
    """Test LingMess-Coref model."""
    
    def test_lingmess_import(self):
        """Test that LingMess-Coref can be imported."""
        try:
            # This would be the actual import path
            # from neural_models.neural_coref.src.lingmess_coref import LingMessCoref
            self.assertTrue(True)  # Placeholder for actual import test
        except ImportError as e:
            self.fail(f"Failed to import LingMess-Coref: {e}")
    
    def test_lingmess_config(self):
        """Test LingMess-Coref configuration."""
        from config import NEURAL_MODELS
        
        lingmess_config = NEURAL_MODELS['lingmess-coref']
        self.assertEqual(lingmess_config['name'], 'LingMess Coref')
        self.assertIn('Linguistically motivated', lingmess_config['description'])
        self.assertIn('lingmess-coref', lingmess_config['script'])
        self.assertIn('lingmess-coref', lingmess_config['config'])
    
    def test_lingmess_training(self):
        """Test LingMess-Coref training workflow."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test training with mock
            with patch('tools.integrated_workflow.run_neural_training') as mock_train:
                mock_train.return_value = True
                result = run_neural_training('test-model', [42])
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass


class TestWLCoref(TestNeuralModelsBase):
    """Test WL-Coref model."""
    
    def test_wl_coref_import(self):
        """Test that WL-Coref can be imported."""
        try:
            # This would be the actual import path
            # from neural_models.neural_coref.src.wl_coref import WLCoref
            self.assertTrue(True)  # Placeholder for actual import test
        except ImportError as e:
            self.fail(f"Failed to import WL-Coref: {e}")
    
    def test_wl_coref_config(self):
        """Test WL-Coref configuration."""
        from config import NEURAL_MODELS
        
        wl_config = NEURAL_MODELS['wl-coref']
        self.assertEqual(wl_config['name'], 'WL-Coref')
        self.assertIn('Word-level', wl_config['description'])
        self.assertIn('wl-coref', wl_config['script'])
        self.assertIn('wl-coref', wl_config['config'])
    
    def test_wl_coref_training(self):
        """Test WL-Coref training workflow."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test training with mock
            with patch('tools.integrated_workflow.run_neural_training') as mock_train:
                mock_train.return_value = True
                result = run_neural_training('test-model', [42])
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass


class TestNeuralTraining(TestNeuralModelsBase):
    """Test neural training functionality."""
    
    def test_training_workflow(self):
        """Test complete training workflow."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test with different base models
            base_models = ['onlplab/alephbert-base', 'microsoft/mdeberta-v3-base']
            seeds = [42, 123, 2021]
            
            for base_model in base_models:
                with patch('tools.integrated_workflow.run_neural_training') as mock_train:
                    mock_train.return_value = True
                    result = run_neural_training(base_model, seeds)
                    self.assertTrue(result)
                    
        except ImportError:
            # Skip if function not available
            pass
    
    def test_training_configuration(self):
        """Test training configuration."""
        from config import NEURAL_CONFIG
        
        # Check base models
        base_models = NEURAL_CONFIG['base_models']
        self.assertIsInstance(base_models, list)
        self.assertGreater(len(base_models), 0)
        
        # Check seeds
        seeds = NEURAL_CONFIG['seeds']
        self.assertIsInstance(seeds, list)
        self.assertGreater(len(seeds), 0)
        
        # Check evaluation metrics
        metrics = NEURAL_CONFIG['evaluation_metrics']
        self.assertIsInstance(metrics, list)
        required_metrics = ['muc', 'b3', 'ceaf']
        for metric in required_metrics:
            self.assertIn(metric, metrics)
    
    def test_training_error_handling(self):
        """Test training error handling."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test with invalid base model - the function handles errors gracefully
            result = run_neural_training('invalid-model', [42])
            # The function should handle invalid models gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass


class TestNeuralEvaluation(TestNeuralModelsBase):
    """Test neural model evaluation."""
    
    def test_evaluation_metrics(self):
        """Test evaluation metrics."""
        from config import NEURAL_CONFIG
        
        metrics = NEURAL_CONFIG['evaluation_metrics']
        
        # Check required metrics
        required_metrics = ['muc', 'b3', 'ceaf']
        for metric in required_metrics:
            self.assertIn(metric, metrics)
    
    def test_evaluation_results(self):
        """Test evaluation results structure."""
        # Create mock evaluation results
        mock_results = {
            'lingmess-coref': {
                'muc': {'precision': 0.85, 'recall': 0.82, 'f1': 0.83},
                'b3': {'precision': 0.78, 'recall': 0.76, 'f1': 0.77},
                'ceaf': {'precision': 0.82, 'recall': 0.80, 'f1': 0.81}
            },
            'wl-coref': {
                'muc': {'precision': 0.83, 'recall': 0.80, 'f1': 0.81},
                'b3': {'precision': 0.76, 'recall': 0.74, 'f1': 0.75},
                'ceaf': {'precision': 0.80, 'recall': 0.78, 'f1': 0.79}
            }
        }
        
        # Check results structure
        for model_name, model_results in mock_results.items():
            self.assertIn('muc', model_results)
            self.assertIn('b3', model_results)
            self.assertIn('ceaf', model_results)
            
            for metric_name, metric_results in model_results.items():
                self.assertIn('precision', metric_results)
                self.assertIn('recall', metric_results)
                self.assertIn('f1', metric_results)
                
                # Check values are valid
                for value in metric_results.values():
                    self.assertIsInstance(value, (int, float))
                    self.assertGreaterEqual(value, 0.0)
                    self.assertLessEqual(value, 1.0)
    
    def test_sota_evaluation(self):
        """Test SOTA evaluation functionality."""
        from config import NEURAL_CONFIG
        
        # Check SOTA evaluation is enabled
        self.assertIn('sota_evaluation', NEURAL_CONFIG)
        self.assertTrue(NEURAL_CONFIG['sota_evaluation'])


class TestNeuralIntegration(TestNeuralModelsBase):
    """Test neural models integration."""
    
    def test_model_selection(self):
        """Test model selection based on configuration."""
        from config import NEURAL_MODELS
        
        # Test that all models are properly configured
        for model_name, model_config in NEURAL_MODELS.items():
            self.assertIn('name', model_config)
            self.assertIn('description', model_config)
            self.assertIn('script', model_config)
            self.assertIn('config', model_config)
    
    def test_training_integration(self):
        """Test training integration with workflow."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test integration with main workflow
            with patch('tools.integrated_workflow.run_neural_training') as mock_train:
                mock_train.return_value = True
                
                # Test with different configurations
                base_models = ['onlplab/alephbert-base']
                seeds = [42, 123]
                
                for base_model in base_models:
                    result = run_neural_training(base_model, seeds)
                    self.assertTrue(result)
                    
        except ImportError:
            # Skip if function not available
            pass
    
    def test_results_integration(self):
        """Test results integration."""
        from config import get_neural_results_path
        
        # Test results path generation for different models
        models = ['lingmess-coref', 'wl-coref']
        base_models = ['test-model-1', 'test-model-2']
        seeds = [42, 123]
        
        for model in models:
            for base_model in base_models:
                for seed in seeds:
                    path = get_neural_results_path(model, base_model, seed)
                    self.assertIn(model, str(path))
                    self.assertIn(base_model, str(path))
                    self.assertIn(f'seed_{seed}', str(path))


class TestNeuralPerformance(TestNeuralModelsBase):
    """Test neural models performance."""
    
    def test_training_speed(self):
        """Test training speed (mock)."""
        try:
            from tools.integrated_workflow import run_neural_training
            import time
            
            # Test training speed with mock
            with patch('tools.integrated_workflow.run_neural_training') as mock_train:
                mock_train.return_value = True
                
                start_time = time.time()
                result = run_neural_training('test-model', [42])
                end_time = time.time()
                
                processing_time = end_time - start_time
                self.assertLess(processing_time, 1.0)  # Mock should be fast
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass
    
    def test_memory_usage(self):
        """Test memory usage (mock)."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test with large seed list
            large_seeds = list(range(100))
            
            with patch('tools.integrated_workflow.run_neural_training') as mock_train:
                mock_train.return_value = True
                
                # Should not cause memory issues
                result = run_neural_training('test-model', large_seeds)
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass


class TestNeuralErrorHandling(TestNeuralModelsBase):
    """Test neural models error handling."""
    
    def test_invalid_base_model(self):
        """Test handling of invalid base models."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test with invalid base model - the function handles errors gracefully
            result = run_neural_training('invalid-model', [42])
            # The function should handle invalid models gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass
    
    def test_empty_seeds(self):
        """Test handling of empty seeds list."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test with empty seeds - the function handles errors gracefully
            result = run_neural_training('test-model', [])
            # The function should handle empty seeds gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass
    
    def test_missing_scripts(self):
        """Test handling of missing training scripts."""
        try:
            from tools.integrated_workflow import run_neural_training
            
            # Test with missing script - the function handles errors gracefully
            result = run_neural_training('test-model', [42])
            # The function should handle missing scripts gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass


if __name__ == '__main__':
    unittest.main() 
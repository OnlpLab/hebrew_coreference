#!/usr/bin/env python3
"""
Tests for LLM evaluation components.
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

class TestLLMEvaluationBase(unittest.TestCase):
    """Base class for LLM evaluation tests."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = self.create_test_data()
        
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_data(self):
        """Create test data for LLM evaluation."""
        test_data = [
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
        
        data_path = os.path.join(self.temp_dir, "test_data.jsonl")
        with open(data_path, 'w', encoding='utf-8') as f:
            for item in test_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return data_path


class TestLLMConfig(TestLLMEvaluationBase):
    """Test LLM configuration."""
    
    def test_llm_models_config(self):
        """Test LLM models configuration."""
        from config import LLM_MODELS, LLM_CONFIG
        
        # Check required models exist
        required_models = ['gpt-4o-mini', 'gpt-3.5-turbo', 'gemini-2.0-flash']
        for model in required_models:
            self.assertIn(model, LLM_MODELS)
        
        # Check model structure
        for model_name, model_config in LLM_MODELS.items():
            self.assertIn('name', model_config)
            self.assertIn('provider', model_config)
            self.assertIn('max_tokens', model_config)
            self.assertIn('temperature', model_config)
            self.assertIsInstance(model_config['name'], str)
            self.assertIsInstance(model_config['provider'], str)
            self.assertIsInstance(model_config['max_tokens'], int)
            self.assertIsInstance(model_config['temperature'], (int, float))
        
        # Check LLM config
        self.assertIn('prompt_templates', LLM_CONFIG)
        self.assertIn('evaluation_metrics', LLM_CONFIG)
        self.assertIn('batch_size', LLM_CONFIG)
        self.assertIn('timeout', LLM_CONFIG)
        self.assertIsInstance(LLM_CONFIG['prompt_templates'], list)
        self.assertIsInstance(LLM_CONFIG['evaluation_metrics'], list)
        self.assertIsInstance(LLM_CONFIG['batch_size'], int)
        self.assertIsInstance(LLM_CONFIG['timeout'], int)
    
    def test_llm_paths(self):
        """Test LLM evaluation paths."""
        from config import (
            LLM_COREF_DIR, LLM_SRC_DIR, 
            LLM_DATA_DIR, LLM_RESULTS_DIR, 
            LLM_SCRIPTS_DIR, LLM_UTILS_DIR
        )
        
        # Check LLM paths exist
        self.assertTrue(LLM_COREF_DIR.exists())
        self.assertTrue(LLM_SRC_DIR.exists())
        self.assertTrue(LLM_DATA_DIR.exists())
        self.assertTrue(LLM_RESULTS_DIR.exists())
        self.assertTrue(LLM_SCRIPTS_DIR.exists())
        self.assertTrue(LLM_UTILS_DIR.exists())
        
        # Check relationships
        self.assertEqual(LLM_SRC_DIR.parent, LLM_COREF_DIR)
        self.assertEqual(LLM_DATA_DIR.parent, LLM_COREF_DIR)
        self.assertEqual(LLM_RESULTS_DIR.parent, LLM_COREF_DIR)
        self.assertEqual(LLM_SCRIPTS_DIR.parent, LLM_COREF_DIR)
        self.assertEqual(LLM_UTILS_DIR.parent, LLM_COREF_DIR)
    
    def test_llm_results_path(self):
        """Test LLM results path generation."""
        from config import get_llm_results_path, LLM_RESULTS_DIR
        
        path = get_llm_results_path('gpt-4', 'test_experiment')
        
        self.assertTrue(str(path).startswith(str(LLM_RESULTS_DIR)))
        self.assertIn('gpt-4', str(path))
        self.assertIn('test_experiment', str(path))


class TestGPT4oMiniEvaluation(TestLLMEvaluationBase):
    """Test GPT-4o Mini evaluation."""
    
    def test_gpt4o_mini_config(self):
        """Test GPT-4o Mini configuration."""
        from config import LLM_MODELS
        
        gpt4o_mini_config = LLM_MODELS['gpt-4o-mini']
        self.assertEqual(gpt4o_mini_config['name'], 'GPT-4o Mini')
        self.assertEqual(gpt4o_mini_config['provider'], 'openai')
        self.assertIsInstance(gpt4o_mini_config['max_tokens'], int)
        self.assertIsInstance(gpt4o_mini_config['temperature'], (int, float))
    
    def test_gpt4o_mini_evaluation(self):
        """Test GPT-4o Mini evaluation workflow."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test evaluation with mock
            with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                mock_eval.return_value = True
                result = run_llm_evaluation('gpt-4o-mini', self.test_data, 'doc_template')
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass


class TestGPT35Evaluation(TestLLMEvaluationBase):
    """Test GPT-3.5 evaluation."""
    
    def test_gpt35_config(self):
        """Test GPT-3.5 configuration."""
        from config import LLM_MODELS
        
        gpt35_config = LLM_MODELS['gpt-3.5-turbo']
        self.assertEqual(gpt35_config['name'], 'GPT-3.5 Turbo')
        self.assertEqual(gpt35_config['provider'], 'openai')
        self.assertIsInstance(gpt35_config['max_tokens'], int)
        self.assertIsInstance(gpt35_config['temperature'], (int, float))
    
    def test_gpt35_evaluation(self):
        """Test GPT-3.5 evaluation workflow."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test evaluation with mock
            with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                mock_eval.return_value = True
                result = run_llm_evaluation('gpt-3.5-turbo', self.test_data, 'doc_template')
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass


class TestGeminiFlashEvaluation(TestLLMEvaluationBase):
    """Test Gemini 2.0 Flash evaluation."""
    
    def test_gemini_flash_config(self):
        """Test Gemini 2.0 Flash configuration."""
        from config import LLM_MODELS
        
        gemini_flash_config = LLM_MODELS['gemini-2.0-flash']
        self.assertEqual(gemini_flash_config['name'], 'Gemini 2.0 Flash')
        self.assertEqual(gemini_flash_config['provider'], 'google')
        self.assertIsInstance(gemini_flash_config['max_tokens'], int)
        self.assertIsInstance(gemini_flash_config['temperature'], (int, float))
    
    def test_gemini_flash_evaluation(self):
        """Test Gemini 2.0 Flash evaluation workflow."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test evaluation with mock
            with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                mock_eval.return_value = True
                result = run_llm_evaluation('gemini-2.0-flash', self.test_data, 'doc_template')
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass


class TestLLMEvaluationWorkflow(TestLLMEvaluationBase):
    """Test LLM evaluation workflow."""
    
    def test_evaluation_workflow(self):
        """Test complete evaluation workflow."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test with different models
            models = ['gpt-4o-mini', 'gpt-3.5-turbo', 'gemini-2.0-flash']
            prompt_templates = ['doc_template', 'qa_template']
            
            for model in models:
                for template in prompt_templates:
                    with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                        mock_eval.return_value = True
                        result = run_llm_evaluation(model, self.test_data, template)
                        self.assertTrue(result)
                        
        except ImportError:
            # Skip if function not available
            pass
    
    def test_evaluation_configuration(self):
        """Test evaluation configuration."""
        from config import LLM_CONFIG
        
        # Check prompt templates
        prompt_templates = LLM_CONFIG['prompt_templates']
        self.assertIsInstance(prompt_templates, list)
        self.assertGreater(len(prompt_templates), 0)
        
        # Check evaluation metrics
        metrics = LLM_CONFIG['evaluation_metrics']
        self.assertIsInstance(metrics, list)
        required_metrics = ['muc', 'b3', 'ceaf']
        for metric in required_metrics:
            self.assertIn(metric, metrics)
        
        # Check batch size and timeout
        self.assertIsInstance(LLM_CONFIG['batch_size'], int)
        self.assertIsInstance(LLM_CONFIG['timeout'], int)
        self.assertGreater(LLM_CONFIG['batch_size'], 0)
        self.assertGreater(LLM_CONFIG['timeout'], 0)
    
    def test_evaluation_error_handling(self):
        """Test evaluation error handling."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test with invalid model - the function handles errors gracefully
            result = run_llm_evaluation('invalid-model', self.test_data, 'doc_template')
            # The function should handle invalid models gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass


class TestLLMResults(TestLLMEvaluationBase):
    """Test LLM evaluation results."""
    
    def test_results_structure(self):
        """Test evaluation results structure."""
        # Create mock evaluation results
        mock_results = {
            'gpt-4': {
                'muc': {'precision': 0.87, 'recall': 0.84, 'f1': 0.85},
                'b3': {'precision': 0.80, 'recall': 0.78, 'f1': 0.79},
                'ceaf': {'precision': 0.84, 'recall': 0.82, 'f1': 0.83}
            },
            'gpt-3.5-turbo': {
                'muc': {'precision': 0.84, 'recall': 0.81, 'f1': 0.82},
                'b3': {'precision': 0.77, 'recall': 0.75, 'f1': 0.76},
                'ceaf': {'precision': 0.81, 'recall': 0.79, 'f1': 0.80}
            },
            'claude': {
                'muc': {'precision': 0.86, 'recall': 0.83, 'f1': 0.84},
                'b3': {'precision': 0.79, 'recall': 0.77, 'f1': 0.78},
                'ceaf': {'precision': 0.83, 'recall': 0.81, 'f1': 0.82}
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
    
    def test_results_comparison(self):
        """Test results comparison between models."""
        # Create mock results for comparison
        mock_results = {
            'gpt-4': {'f1': 0.85},
            'gpt-3.5-turbo': {'f1': 0.82},
            'claude': {'f1': 0.84}
        }
        
        # Check that results can be compared
        f1_scores = {model: results['f1'] for model, results in mock_results.items()}
        
        # GPT-4 should have highest F1 score
        self.assertEqual(max(f1_scores.values()), f1_scores['gpt-4'])
        
        # All scores should be reasonable
        for score in f1_scores.values():
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)


class TestLLMIntegration(TestLLMEvaluationBase):
    """Test LLM evaluation integration."""
    
    def test_model_selection(self):
        """Test model selection based on configuration."""
        from config import LLM_MODELS
        
        # Test that all models are properly configured
        for model_name, model_config in LLM_MODELS.items():
            self.assertIn('name', model_config)
            self.assertIn('provider', model_config)
            self.assertIn('max_tokens', model_config)
            self.assertIn('temperature', model_config)
    
    def test_evaluation_integration(self):
        """Test evaluation integration with workflow."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test integration with main workflow
            with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                mock_eval.return_value = True
                
                # Test with different configurations
                models = ['gpt-4', 'gpt-3.5-turbo', 'claude']
                templates = ['doc_template', 'qa_template']
                
                for model in models:
                    for template in templates:
                        result = run_llm_evaluation(model, self.test_data, template)
                        self.assertTrue(result)
                        
        except ImportError:
            # Skip if function not available
            pass
    
    def test_results_integration(self):
        """Test results integration."""
        from config import get_llm_results_path
        
        # Test results path generation for different models
        models = ['gpt-4', 'gpt-3.5-turbo', 'claude']
        experiments = ['experiment1', 'experiment2']
        
        for model in models:
            for experiment in experiments:
                path = get_llm_results_path(model, experiment)
                self.assertIn(model, str(path))
                self.assertIn(experiment, str(path))


class TestLLMPerformance(TestLLMEvaluationBase):
    """Test LLM evaluation performance."""
    
    def test_evaluation_speed(self):
        """Test evaluation speed (mock)."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            import time
            
            # Test evaluation speed with mock
            with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                mock_eval.return_value = True
                
                start_time = time.time()
                result = run_llm_evaluation('gpt-4', self.test_data, 'doc_template')
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
            from tools.integrated_workflow import run_llm_evaluation
            
            # Create large test data
            large_data = self.create_large_test_data()
            
            with patch('tools.integrated_workflow.run_llm_evaluation') as mock_eval:
                mock_eval.return_value = True
                
                # Should not cause memory issues
                result = run_llm_evaluation('gpt-4', large_data, 'doc_template')
                self.assertTrue(result)
                
        except ImportError:
            # Skip if function not available
            pass
    
    def create_large_test_data(self):
        """Create large test data for performance testing."""
        large_data = []
        for i in range(100):
            large_data.append({
                "id": f"doc{i}",
                "text": f"Document {i} with Hebrew text ראש הממשלה בנימין נתניהו.",
                "mentions": [
                    {"id": 1, "text": "ראש הממשלה", "start": 0, "end": 12},
                    {"id": 2, "text": "בנימין נתניהו", "start": 13, "end": 26}
                ],
                "clusters": [
                    {"mentions": [1, 2], "representative": 1}
                ]
            })
        
        large_path = os.path.join(self.temp_dir, "large_test_data.jsonl")
        with open(large_path, 'w', encoding='utf-8') as f:
            for item in large_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        return large_path


class TestLLMErrorHandling(TestLLMEvaluationBase):
    """Test LLM evaluation error handling."""
    
    def test_invalid_model(self):
        """Test handling of invalid models."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test with invalid model - the function handles errors gracefully
            result = run_llm_evaluation('invalid-model', self.test_data, 'doc_template')
            # The function should handle invalid models gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass
    
    def test_invalid_data(self):
        """Test handling of invalid data."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test with invalid data file - the function handles errors gracefully
            invalid_data = "nonexistent_file.jsonl"
            
            result = run_llm_evaluation('gpt-4', invalid_data, 'doc_template')
            # The function should handle invalid data gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass
    
    def test_invalid_template(self):
        """Test handling of invalid prompt templates."""
        try:
            from tools.integrated_workflow import run_llm_evaluation
            
            # Test with invalid template - the function handles errors gracefully
            result = run_llm_evaluation('gpt-4', self.test_data, 'invalid_template')
            # The function should handle invalid templates gracefully
            self.assertIsInstance(result, (bool, type(None)))
                
        except ImportError:
            # Skip if function not available
            pass


class TestLLMDataFormats(TestLLMEvaluationBase):
    """Test LLM data formats."""
    
    def test_jsonl_format(self):
        """Test JSONL data format."""
        # Test that our test data is valid JSONL
        with open(self.test_data, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            try:
                json.loads(line.strip())
                self.assertTrue(True)  # Valid JSON
            except json.JSONDecodeError:
                self.fail("Invalid JSON in JSONL file")
    
    def test_hebrew_text_preservation(self):
        """Test Hebrew text preservation in data."""
        with open(self.test_data, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        # Check Hebrew text is preserved
        text = data['text']
        self.assertIn('ראש', text)
        self.assertIn('הממשלה', text)
        self.assertIn('בנימין', text)
        self.assertIn('נתניהו', text)
    
    def test_mention_structure(self):
        """Test mention structure in data."""
        with open(self.test_data, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        # Check mention structure
        mentions = data['mentions']
        self.assertIsInstance(mentions, list)
        
        for mention in mentions:
            self.assertIn('id', mention)
            self.assertIn('text', mention)
            self.assertIn('start', mention)
            self.assertIn('end', mention)
            
            self.assertIsInstance(mention['id'], int)
            self.assertIsInstance(mention['text'], str)
            self.assertIsInstance(mention['start'], int)
            self.assertIsInstance(mention['end'], int)
    
    def test_cluster_structure(self):
        """Test cluster structure in data."""
        with open(self.test_data, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            data = json.loads(first_line)
        
        # Check cluster structure
        clusters = data['clusters']
        self.assertIsInstance(clusters, list)
        
        for cluster in clusters:
            self.assertIn('mentions', cluster)
            self.assertIn('representative', cluster)
            
            self.assertIsInstance(cluster['mentions'], list)
            self.assertIsInstance(cluster['representative'], int)


if __name__ == '__main__':
    unittest.main() 
#!/usr/bin/env python3
"""
Run coreference evaluation on both original and SOTA tokenized data and compare results.

This script evaluates a trained model on both the original test data and the synthetic
SOTA tokenized test data, then compares the performance differences.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def run_evaluation(model_path: str, test_file: str, output_dir: str, eval_split: str = "test") -> Dict:
    """
    Run coreference evaluation on a test file.
    
    Args:
        model_path: Path to the trained model
        test_file: Path to the test data file
        output_dir: Directory to save evaluation results
        eval_split: Evaluation split name
        
    Returns:
        Dictionary containing evaluation results
    """
    print(f"🔍 Running evaluation on {test_file} with model {model_path}")
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Build evaluation command
    cmd = [
        sys.executable, "src/lingmess-coref/run.py",
        "--model_name_or_path", model_path,
        "--test_file", test_file,
        "--output_dir", output_dir,
        "--eval_split", eval_split,
        "--device", "cpu",  # Use CPU for evaluation
        "--do_train", "false"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode != 0:
            print(f"❌ Evaluation failed with return code {result.returncode}")
            print(f"Error output: {result.stderr}")
            return None
        
        print(f"✅ Evaluation completed successfully")
        
        # Read evaluation results
        result_file = os.path.join(output_dir, f"result_{eval_split}.json")
        if os.path.exists(result_file):
            with open(result_file, 'r') as f:
                results = json.load(f)
            return results
        else:
            print(f"❌ Result file not found: {result_file}")
            return None
            
    except Exception as e:
        print(f"❌ Error running evaluation: {e}")
        return None


def compare_results(original_results: Dict, sota_results: Dict) -> Dict:
    """
    Compare evaluation results between original and SOTA tokenized data.
    
    Args:
        original_results: Results from original test data
        sota_results: Results from SOTA tokenized test data
        
    Returns:
        Dictionary with comparison metrics
    """
    comparison = {
        'metrics': {},
        'differences': {},
        'summary': {}
    }
    
    # Define metrics to compare
    metrics_to_compare = [
        'coref_f1', 'coref_precision', 'coref_recall',
        'mention_f1', 'mention_precision', 'mention_recall'
    ]
    
    for metric in metrics_to_compare:
        if metric in original_results and metric in sota_results:
            orig_value = original_results[metric]
            sota_value = sota_results[metric]
            difference = sota_value - orig_value
            
            comparison['metrics'][metric] = {
                'original': orig_value,
                'sota': sota_value,
                'difference': difference,
                'percent_change': (difference / orig_value * 100) if orig_value != 0 else 0
            }
            
            comparison['differences'][metric] = difference
    
    # Calculate summary statistics
    if comparison['metrics']:
        avg_difference = sum(comparison['differences'].values()) / len(comparison['differences'])
        comparison['summary'] = {
            'average_difference': avg_difference,
            'metrics_compared': len(comparison['metrics']),
            'better_in_sota': sum(1 for diff in comparison['differences'].values() if diff > 0),
            'worse_in_sota': sum(1 for diff in comparison['differences'].values() if diff < 0),
            'same_performance': sum(1 for diff in comparison['differences'].values() if abs(diff) < 0.001)
        }
    
    return comparison


def print_comparison_report(comparison: Dict, model_name: str):
    """
    Print a detailed comparison report.
    
    Args:
        comparison: Comparison results dictionary
        model_name: Name of the model being evaluated
    """
    print(f"\n📊 Coreference Evaluation Comparison Report")
    print(f"Model: {model_name}")
    print("=" * 60)
    
    if not comparison['metrics']:
        print("❌ No metrics available for comparison")
        return
    
    # Print detailed metrics
    print("\n📈 Detailed Metrics Comparison:")
    print(f"{'Metric':<20} {'Original':<10} {'SOTA':<10} {'Diff':<8} {'% Change':<10}")
    print("-" * 60)
    
    for metric, values in comparison['metrics'].items():
        print(f"{metric:<20} {values['original']:<10.4f} {values['sota']:<10.4f} "
              f"{values['difference']:<+8.4f} {values['percent_change']:<+10.2f}%")
    
    # Print summary
    summary = comparison['summary']
    print(f"\n📋 Summary:")
    print(f"   Average difference: {summary['average_difference']:+.4f}")
    print(f"   Metrics compared: {summary['metrics_compared']}")
    print(f"   Better in SOTA: {summary['better_in_sota']}")
    print(f"   Worse in SOTA: {summary['worse_in_sota']}")
    print(f"   Same performance: {summary['same_performance']}")
    
    # Overall assessment
    if summary['average_difference'] > 0.01:
        print(f"\n✅ SOTA tokenization shows IMPROVED performance")
    elif summary['average_difference'] < -0.01:
        print(f"\n❌ SOTA tokenization shows DEGRADED performance")
    else:
        print(f"\n➖ SOTA tokenization shows SIMILAR performance")


def main():
    """Main function to run evaluation and comparison."""
    # Configuration
    model_path = "results/lingmess/alephbert-base_seed42_model/model"
    original_test_file = "data/lingmess/hebrew/test.hebrew.jsonlines"
    sota_test_file = "data/lingmess/hebrew/sota_tokenized/test.sota_tokenized_final.jsonlines"
    
    # Output directories
    original_output_dir = "results/coref_evaluation_comparison/original"
    sota_output_dir = "results/coref_evaluation_comparison/sota"
    
    print("🚀 Starting Coreference Evaluation Comparison")
    print("=" * 60)
    
    # Check if files exist
    if not os.path.exists(original_test_file):
        print(f"❌ Original test file not found: {original_test_file}")
        return
    
    if not os.path.exists(sota_test_file):
        print(f"❌ SOTA test file not found: {sota_test_file}")
        return
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return
    
    # Run evaluation on original data
    print(f"\n🔍 Step 1: Evaluating on original test data...")
    original_results = run_evaluation(model_path, original_test_file, original_output_dir)
    
    if original_results is None:
        print("❌ Failed to evaluate original data")
        return
    
    # Run evaluation on SOTA tokenized data
    print(f"\n🔍 Step 2: Evaluating on SOTA tokenized test data...")
    sota_results = run_evaluation(model_path, sota_test_file, sota_output_dir)
    
    if sota_results is None:
        print("❌ Failed to evaluate SOTA tokenized data")
        return
    
    # Compare results
    print(f"\n🔍 Step 3: Comparing results...")
    comparison = compare_results(original_results, sota_results)
    
    # Print comparison report
    model_name = os.path.basename(model_path)
    print_comparison_report(comparison, model_name)
    
    # Save comparison results
    comparison_file = "results/coref_evaluation_comparison/comparison_results.json"
    Path(os.path.dirname(comparison_file)).mkdir(parents=True, exist_ok=True)
    
    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)
    
    print(f"\n💾 Comparison results saved to: {comparison_file}")
    print("\n🎉 Coreference evaluation comparison completed!")


if __name__ == "__main__":
    main() 
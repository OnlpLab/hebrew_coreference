#!/usr/bin/env python3
"""
Simple Comparison Script for Hebrew Coreference Resolution

This script specifically compares the mistakes between:
- LLM vs Neural models
- Different tokenization strategies (gold, SOTA, raw)
- Focuses on document 240 as requested
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict

def load_jsonl_file(file_path: str) -> Dict:
    """Load a single JSONL file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                return json.loads(line.strip())
    except FileNotFoundError:
        print(f"Warning: File not found: {file_path}")
        return {}
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return {}

def extract_mentions_from_clusters(clusters: List[List[int]], tokens: List[str]) -> List[Tuple[int, int, str]]:
    """Extract mention spans and text from clusters"""
    mentions = []
    for cluster in clusters:
        if len(cluster) >= 2:
            start, end = cluster[0], cluster[1]
            # Handle case where start and end might be lists
            if isinstance(start, list):
                start = start[0]
            if isinstance(end, list):
                end = end[0]
            
            # Ensure we have valid indices
            if start < len(tokens) and end < len(tokens) and start <= end:
                text = ' '.join(tokens[start:end+1])
                mentions.append((start, end, text))
    return mentions

def calculate_metrics(gold_mentions: List[Tuple[int, int, str]], pred_mentions: List[Tuple[int, int, str]]) -> Dict:
    """Calculate precision, recall, and F1"""
    gold_set = set((start, end) for start, end, _ in gold_mentions)
    pred_set = set((start, end) for start, end, _ in pred_mentions)
    
    correct = len(gold_set.intersection(pred_set))
    precision = correct / len(pred_set) if pred_set else 0.0
    recall = correct / len(gold_set) if gold_set else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'gold_count': len(gold_set),
        'pred_count': len(pred_set),
        'correct': correct,
        'missing': len(gold_set - pred_set),
        'extra': len(pred_set - gold_set)
    }

def analyze_mistakes(gold_mentions: List[Tuple[int, int, str]], pred_mentions: List[Tuple[int, int, str]], tokens: List[str]) -> Dict:
    """Analyze specific types of mistakes"""
    gold_set = set((start, end) for start, end, _ in gold_mentions)
    pred_set = set((start, end) for start, end, _ in pred_mentions)
    
    missing = gold_set - pred_set
    extra = pred_set - gold_set
    
    # Get text for missing mentions
    missing_details = []
    for start, end in missing:
        if start < len(tokens) and end < len(tokens):
            text = ' '.join(tokens[start:end+1])
            missing_details.append(f"{start}-{end}: {text}")
    
    # Get text for extra mentions
    extra_details = []
    for start, end in extra:
        if start < len(tokens) and end < len(tokens):
            text = ' '.join(tokens[start:end+1])
            extra_details.append(f"{start}-{end}: {text}")
    
    return {
        'missing_mentions': missing_details,
        'extra_mentions': extra_details,
        'missing_count': len(missing),
        'extra_count': len(extra)
    }

def main():
    # Base paths
    base_path = Path("/Users/s0g0a87/studies/hebrew coreference/error_analysis/error_analysis_data")
    doc_id = "240"
    
    print(f"=== Hebrew Coreference Error Analysis for Document {doc_id} ===\n")
    
    # Load gold annotation from neural output (since it contains both gold and predicted)
    print("Loading gold annotation...")
    gold_mentions = []
    tokens = []
    
    # Try to get gold clusters from neural output
    neural_gold_file = base_path / "neural" / "gold" / f"neural_gold_tokenization_{doc_id}.jsonl"
    if neural_gold_file.exists():
        neural_gold_data = load_jsonl_file(str(neural_gold_file))
        if 'clusters' in neural_gold_data and 'tokens' in neural_gold_data:
            # Use the clusters as gold (they should be the gold annotations)
            gold_mentions = extract_mentions_from_clusters(neural_gold_data['clusters'], neural_gold_data['tokens'])
            tokens = neural_gold_data['tokens']
            print(f"Gold mentions: {len(gold_mentions)}")
        else:
            print("Warning: Neural gold file doesn't contain expected data structure")
            return
    else:
        print("Error: Neural gold file not found")
        return
    
    # Load LLM results
    print("\nLoading LLM results...")
    llm_results = {}
    
    # LLM with raw tokenization
    llm_raw_file = base_path / "llm" / "raw" / f"llm_raw_{doc_id}.jsonl"
    if llm_raw_file.exists():
        llm_raw_data = load_jsonl_file(str(llm_raw_file))
        if 'predicted_clusters' in llm_raw_data:
            pred_mentions = extract_mentions_from_clusters(llm_raw_data['predicted_clusters'], tokens)
            metrics = calculate_metrics(gold_mentions, pred_mentions)
            mistakes = analyze_mistakes(gold_mentions, pred_mentions, tokens)
            llm_results['raw'] = {'metrics': metrics, 'mistakes': mistakes, 'mentions': pred_mentions}
            print(f"LLM Raw: {metrics['f1']:.3f} F1")
    
    # LLM with gold tokenization
    llm_gold_file = base_path / "llm" / "tokenized" / f"llm_gold_tok_{doc_id}.jsonl"
    if llm_gold_file.exists():
        llm_gold_data = load_jsonl_file(str(llm_gold_file))
        if 'predicted_clusters' in llm_gold_data:
            pred_mentions = extract_mentions_from_clusters(llm_gold_data['predicted_clusters'], tokens)
            metrics = calculate_metrics(gold_mentions, pred_mentions)
            mistakes = analyze_mistakes(gold_mentions, pred_mentions, tokens)
            llm_results['gold_tok'] = {'metrics': metrics, 'mistakes': mistakes, 'mentions': pred_mentions}
            print(f"LLM Gold Tokenization: {metrics['f1']:.3f} F1")
    
    # LLM with SOTA tokenization
    llm_sota_file = base_path / "llm" / "sota_tokenized" / f"llm_sota_tok_{doc_id}.jsonl"
    if llm_sota_file.exists():
        llm_sota_data = load_jsonl_file(str(llm_sota_file))
        if 'predicted_clusters' in llm_sota_data:
            pred_mentions = extract_mentions_from_clusters(llm_sota_data['predicted_clusters'], tokens)
            metrics = calculate_metrics(gold_mentions, pred_mentions)
            mistakes = analyze_mistakes(gold_mentions, pred_mentions, tokens)
            llm_results['sota_tok'] = {'metrics': metrics, 'mistakes': mistakes, 'mentions': pred_mentions}
            print(f"LLM SOTA Tokenization: {metrics['f1']:.3f} F1")
    
    # Load Neural results
    print("\nLoading Neural results...")
    neural_results = {}
    
    # Neural with gold tokenization
    neural_gold_file = base_path / "neural" / "gold" / f"neural_gold_tokenization_{doc_id}.jsonl"
    if neural_gold_file.exists():
        neural_gold_data = load_jsonl_file(str(neural_gold_file))
        if 'clusters' in neural_gold_data:
            pred_mentions = extract_mentions_from_clusters(neural_gold_data['clusters'], neural_gold_data['tokens'])
            metrics = calculate_metrics(gold_mentions, pred_mentions)
            mistakes = analyze_mistakes(gold_mentions, pred_mentions, tokens)
            neural_results['gold_tok'] = {'metrics': metrics, 'mistakes': mistakes, 'mentions': pred_mentions}
            print(f"Neural Gold Tokenization: {metrics['f1']:.3f} F1")
    
    # Neural with SOTA tokenization
    neural_sota_file = base_path / "neural" / "sota_tokenized" / f"neural_sota_tokenization_{doc_id}.jsonl"
    if neural_sota_file.exists():
        neural_sota_data = load_jsonl_file(str(neural_sota_file))
        if 'clusters' in neural_sota_data:
            pred_mentions = extract_mentions_from_clusters(neural_sota_data['clusters'], neural_sota_data['tokens'])
            metrics = calculate_metrics(gold_mentions, pred_mentions)
            mistakes = analyze_mistakes(gold_mentions, pred_mentions, tokens)
            neural_results['sota_tok'] = {'metrics': metrics, 'mistakes': mistakes, 'mentions': pred_mentions}
            print(f"Neural SOTA Tokenization: {metrics['f1']:.3f} F1")
    
    # Generate comparison report
    print("\n" + "="*60)
    print("COMPARISON REPORT")
    print("="*60)
    
    # Compare approaches
    approaches = {
        'LLM Raw': llm_results.get('raw'),
        'LLM Gold Tokenization': llm_results.get('gold_tok'),
        'LLM SOTA Tokenization': llm_results.get('sota_tok'),
        'Neural Gold Tokenization': neural_results.get('gold_tok'),
        'Neural SOTA Tokenization': neural_results.get('sota_tok')
    }
    
    # Find best performing approach
    best_approach = None
    best_f1 = 0.0
    
    for name, data in approaches.items():
        if data:
            f1 = data['metrics']['f1']
            print(f"\n{name}:")
            print(f"  F1: {f1:.3f}")
            print(f"  Precision: {data['metrics']['precision']:.3f}")
            print(f"  Recall: {data['metrics']['recall']:.3f}")
            print(f"  Missing: {data['metrics']['missing']}")
            print(f"  Extra: {data['metrics']['extra']}")
            
            if f1 > best_f1:
                best_f1 = f1
                best_approach = name
    
    if best_approach:
        print(f"\n{'='*60}")
        print(f"BEST PERFORMING APPROACH: {best_approach} (F1: {best_f1:.3f})")
        print(f"{'='*60}")
    
    # Detailed mistake analysis
    print("\nDETAILED MISTAKE ANALYSIS")
    print("-" * 40)
    
    for name, data in approaches.items():
        if data and data['mistakes']['missing_count'] > 0:
            print(f"\n{name} - Missing Mentions ({data['mistakes']['missing_count']}):")
            for mention in data['mistakes']['missing_mentions'][:5]:  # Show first 5
                print(f"  {mention}")
            if data['mistakes']['missing_count'] > 5:
                print(f"  ... and {data['mistakes']['missing_count'] - 5} more")
        
        if data and data['mistakes']['extra_count'] > 0:
            print(f"\n{name} - Extra Mentions ({data['mistakes']['extra_count']}):")
            for mention in data['mistakes']['extra_mentions'][:5]:  # Show first 5
                print(f"  {mention}")
            if data['mistakes']['extra_count'] > 5:
                print(f"  ... and {data['mistakes']['extra_count'] - 5} more")
    
    # Save detailed results to file
    output_file = base_path / f"comparison_results_{doc_id}.json"
    results_to_save = {
        'gold_mentions': [(start, end, text) for start, end, text in gold_mentions],
        'approaches': {}
    }
    
    for name, data in approaches.items():
        if data:
            results_to_save['approaches'][name] = {
                'metrics': data['metrics'],
                'mentions': [(start, end, text) for start, end, text in data['mentions']]
            }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_to_save, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: {output_file}")

if __name__ == "__main__":
    main() 
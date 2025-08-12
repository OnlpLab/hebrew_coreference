#!/usr/bin/env python3
"""
CONLLU Mention Counter Script for Hebrew NP Chunker

This script counts actual mentions from the final train-dev-test CONLLU files,
comparing with_singleton vs no_singleton versions.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from collections import defaultdict, Counter
import re
from typing import Dict, List, Tuple, Any
import argparse

# Set matplotlib to use a non-interactive backend
plt.switch_backend('Agg')

class CONLLUMentionCounter:
    def __init__(self, data_root: str = "../data/corpus/coreference_final_split"):
        self.data_root = Path(data_root)
        
    def count_mentions_in_conllu_file(self, file_path: Path) -> Tuple[int, int, int]:
        """Count mentions in a single CONLLU file."""
        sentences = 0
        tokens = 0
        mentions = 0
        last_sentence_id = -1
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 5:  # Ensure we have the mention column
                    try:
                        sentence_id = int(parts[1])  # Second column is sentence ID
                        token_id = int(parts[2])     # Third column is token ID
                        mention_annotation = parts[4]  # Fifth column has mention info
                        
                        if sentence_id != last_sentence_id:
                            sentences += 1
                            last_sentence_id = sentence_id
                        tokens += 1
                        
                        # Count mentions (anything with parentheses)
                        if mention_annotation != '_' and '(' in mention_annotation:
                            mentions += 1
                            
                    except ValueError:
                        continue
        
        return sentences, tokens, mentions
    
    def analyze_conllu_splits(self, split_type: str = "no_singleton") -> Dict[str, Any]:
        """Analyze CONLLU files for actual mention counts."""
        splits = ["train", "dev", "test"]
        stats = {}
        
        for split in splits:
            split_path = self.data_root / "gold_splits" / split_type / split
            if not split_path.exists():
                print(f"Warning: {split_path} does not exist")
                continue
                
            files = list(split_path.glob("*.conllu"))
            print(f"Analyzing {len(files)} files in {split} split ({split_type})...")
            
            doc_stats = []
            total_sentences = 0
            total_tokens = 0
            total_mentions = 0
            
            for file_path in files:
                doc_id = file_path.stem
                sentences, tokens, mentions = self.count_mentions_in_conllu_file(file_path)
                
                doc_stats.append({
                    'doc_id': doc_id,
                    'sentences': sentences,
                    'tokens': tokens,
                    'mentions': mentions
                })
                total_sentences += sentences
                total_tokens += tokens
                total_mentions += mentions
            
            # Calculate statistics
            sentences_per_doc = [d['sentences'] for d in doc_stats]
            tokens_per_doc = [d['tokens'] for d in doc_stats]
            mentions_per_doc = [d['mentions'] for d in doc_stats]
            
            stats[split] = {
                'num_documents': len(files),
                'num_sentences': total_sentences,
                'num_tokens': total_tokens,
                'num_mentions': total_mentions,
                'avg_sentences_per_doc': np.mean(sentences_per_doc),
                'median_sentences_per_doc': np.median(sentences_per_doc),
                'avg_tokens_per_doc': np.mean(tokens_per_doc),
                'median_tokens_per_doc': np.median(tokens_per_doc),
                'avg_mentions_per_doc': np.mean(mentions_per_doc),
                'median_mentions_per_doc': np.median(mentions_per_doc),
                'doc_stats': doc_stats
            }
        
        return stats
    
    def compare_singleton_vs_no_singleton(self) -> Dict[str, Any]:
        """Compare mention statistics between with_singleton and no_singleton versions."""
        print("Analyzing with_singleton version...")
        with_singleton_stats = self.analyze_conllu_splits("with_singleton")
        
        print("\nAnalyzing no_singleton version...")
        no_singleton_stats = self.analyze_conllu_splits("no_singleton")
        
        # Calculate singleton counts (difference between versions)
        singleton_stats = {}
        for split in ['train', 'dev', 'test']:
            if split in with_singleton_stats and split in no_singleton_stats:
                with_singleton_mentions = with_singleton_stats[split]['num_mentions']
                no_singleton_mentions = no_singleton_stats[split]['num_mentions']
                singleton_mentions = with_singleton_mentions - no_singleton_mentions
                
                singleton_stats[split] = {
                    'num_singleton_mentions': singleton_mentions,
                    'singleton_percentage': (singleton_mentions / with_singleton_mentions * 100) if with_singleton_mentions > 0 else 0
                }
        
        return {
            'with_singleton': with_singleton_stats,
            'no_singleton': no_singleton_stats,
            'singleton_analysis': singleton_stats
        }
    
    def print_comparison_statistics(self, comparison_data: Dict[str, Any]):
        """Print comparison statistics between singleton versions."""
        print("=" * 100)
        print("CONLLU MENTION STATISTICS COMPARISON")
        print("=" * 100)
        
        for split in ['train', 'dev', 'test']:
            if split in comparison_data['no_singleton']:
                print(f"\n{split.upper()} SPLIT:")
                print("-" * 60)
                
                no_singleton = comparison_data['no_singleton'][split]
                with_singleton = comparison_data['with_singleton'][split]
                singleton_info = comparison_data['singleton_analysis'][split]
                
                print(f"NO SINGLETON:")
                print(f"  Documents: {no_singleton['num_documents']}")
                print(f"  Sentences: {no_singleton['num_sentences']:,}")
                print(f"  Tokens: {no_singleton['num_tokens']:,}")
                print(f"  Mentions: {no_singleton['num_mentions']:,}")
                print(f"  Avg mentions/doc: {no_singleton['avg_mentions_per_doc']:.1f}")
                
                print(f"\nWITH SINGLETON:")
                print(f"  Documents: {with_singleton['num_documents']}")
                print(f"  Sentences: {with_singleton['num_sentences']:,}")
                print(f"  Tokens: {with_singleton['num_tokens']:,}")
                print(f"  Mentions: {with_singleton['num_mentions']:,}")
                print(f"  Avg mentions/doc: {with_singleton['avg_mentions_per_doc']:.1f}")
                
                print(f"\nSINGLETON ANALYSIS:")
                print(f"  Singleton mentions: {singleton_info['num_singleton_mentions']:,}")
                print(f"  Singleton percentage: {singleton_info['singleton_percentage']:.1f}%")
        
        # Overall statistics
        print(f"\n📈 OVERALL STATISTICS:")
        print("-" * 60)
        
        total_no_singleton = sum([comparison_data['no_singleton'][split]['num_mentions'] for split in ['train', 'dev', 'test']])
        total_with_singleton = sum([comparison_data['with_singleton'][split]['num_mentions'] for split in ['train', 'dev', 'test']])
        total_singletons = total_with_singleton - total_no_singleton
        
        print(f"Total mentions (no singleton): {total_no_singleton:,}")
        print(f"Total mentions (with singleton): {total_with_singleton:,}")
        print(f"Total singleton mentions: {total_singletons:,}")
        print(f"Singleton percentage: {total_singletons/total_with_singleton*100:.1f}%")
    
    def save_comparison_statistics(self, comparison_data: Dict[str, Any], output_file: str = "conllu_mention_comparison.json"):
        """Save comparison statistics to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(comparison_data, f, indent=2, ensure_ascii=False)
        
        print(f"Comparison statistics saved to {output_file}")
    
    def run_comparison_analysis(self, output_dir: str = "outputs/conllu_mention_analysis"):
        """Run the complete comparison analysis."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("Starting CONLLU mention comparison analysis...")
        
        # Run comparison
        comparison_data = self.compare_singleton_vs_no_singleton()
        
        # Print results
        self.print_comparison_statistics(comparison_data)
        
        # Save results
        output_file = output_path / "conllu_mention_comparison.json"
        self.save_comparison_statistics(comparison_data, str(output_file))
        
        print(f"\nComparison analysis complete! Results saved to {output_dir}")

def main():
    """Main function to run the CONLLU mention counter analysis."""
    parser = argparse.ArgumentParser(description='Count mentions in CONLLU files')
    parser.add_argument('--data-root', default='../data/corpus/coreference_final_split', 
                       help='Root directory for CONLLU files')
    parser.add_argument('--output-dir', default='outputs/conllu_mention_analysis',
                       help='Output directory for results')
    
    args = parser.parse_args()
    
    counter = CONLLUMentionCounter(args.data_root)
    counter.run_comparison_analysis(args.output_dir)

if __name__ == "__main__":
    main() 
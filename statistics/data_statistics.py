#!/usr/bin/env python3
"""
Data Statistics Script for Hebrew NP Chunker

This script analyzes the final train-dev-test data and generates comprehensive statistics
including document counts, sentence counts, token counts, agreement scores, and visualizations.
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

class DataStatisticsAnalyzer:
    def __init__(self, data_root: str = "../data/corpus/coreference_final_split"):
        self.data_root = Path(data_root)
        self.results = {}
        
    def analyze_conllu_files(self, split_type: str = "with_singleton") -> Dict[str, Any]:
        """Analyze CONLLU files for document, sentence, and token statistics."""
        splits = ["train", "dev", "test"]
        stats = {}
        
        for split in splits:
            split_path = self.data_root / "gold_splits" / split_type / split
            if not split_path.exists():
                print(f"Warning: {split_path} does not exist")
                continue
                
            files = list(split_path.glob("*.conllu"))
            print(f"Analyzing {len(files)} files in {split} split...")
            
            doc_stats = []
            total_sentences = 0
            total_tokens = 0
            
            for file_path in files:
                doc_id = file_path.stem
                sentences, tokens = self._analyze_conllu_file(file_path)
                doc_stats.append({
                    'doc_id': doc_id,
                    'sentences': sentences,
                    'tokens': tokens
                })
                total_sentences += sentences
                total_tokens += tokens
            
            # Calculate statistics
            sentences_per_doc = [d['sentences'] for d in doc_stats]
            tokens_per_doc = [d['tokens'] for d in doc_stats]
            
            stats[split] = {
                'num_documents': len(files),
                'num_sentences': total_sentences,
                'num_tokens': total_tokens,
                'avg_sentences_per_doc': np.mean(sentences_per_doc),
                'median_sentences_per_doc': np.median(sentences_per_doc),
                'avg_tokens_per_doc': np.mean(tokens_per_doc),
                'median_tokens_per_doc': np.median(tokens_per_doc),
                'doc_stats': doc_stats
            }
        
        return stats
    
    def _analyze_conllu_file(self, file_path: Path) -> Tuple[int, int]:
        """Analyze a single CONLLU file and return sentence and token counts."""
        sentences = set()
        tokens = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        sentence_id = int(parts[1])  # Second column is sentence ID
                        token_id = int(parts[2])     # Third column is token ID
                        sentences.add(sentence_id)
                        tokens += 1
                    except ValueError:
                        continue
        
        return len(sentences), tokens
    
    def analyze_agreement_data(self) -> Dict[str, Any]:
        """Analyze agreement data from annotation results."""
        agreement_stats = {}
        
        # Analyze coref agreement
        coref_path = Path("src/annotation/tne_ui/annotation_results/coref")
        if coref_path.exists():
            agreement_stats['coref'] = self._analyze_coref_agreement(coref_path)
        
        # Analyze mention agreement
        mention_path = Path("src/annotation/tne_ui/annotation_results/mention")
        if mention_path.exists():
            agreement_stats['mention'] = self._analyze_mention_agreement(mention_path)
        
        return agreement_stats
    
    def _analyze_coref_agreement(self, coref_path: Path) -> Dict[str, Any]:
        """Analyze coreference agreement data."""
        annotators_file = coref_path / "annotators.txt"
        output_file = coref_path / "output.jsonl"
        
        if not annotators_file.exists() or not output_file.exists():
            return {}
        
        # Read annotators
        with open(annotators_file, 'r', encoding='utf-8') as f:
            annotators = [line.strip() for line in f if line.strip()]
        
        # Read agreement data
        agreement_scores = []
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if 'agreement_score' in data:
                        agreement_scores.append(data['agreement_score'])
                except json.JSONDecodeError:
                    continue
        
        if not agreement_scores:
            return {}
        
        return {
            'avg_agreement': np.mean(agreement_scores),
            'median_agreement': np.median(agreement_scores),
            'std_agreement': np.std(agreement_scores),
            'min_agreement': np.min(agreement_scores),
            'max_agreement': np.max(agreement_scores),
            'num_annotators': len(set(annotators)),
            'total_annotations': len(annotators),
            'agreement_scores': agreement_scores
        }
    
    def _analyze_mention_agreement(self, mention_path: Path) -> Dict[str, Any]:
        """Analyze mention agreement data."""
        annotators_file = mention_path / "annotators.txt"
        output_file = mention_path / "output.jsonl"
        
        if not annotators_file.exists() or not output_file.exists():
            return {}
        
        # Read annotators
        with open(annotators_file, 'r', encoding='utf-8') as f:
            annotators = [line.strip() for line in f if line.strip()]
        
        # Read agreement data
        agreement_scores = []
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    if 'agreement_score' in data:
                        agreement_scores.append(data['agreement_score'])
                except json.JSONDecodeError:
                    continue
        
        if not agreement_scores:
            return {}
        
        return {
            'avg_agreement': np.mean(agreement_scores),
            'median_agreement': np.median(agreement_scores),
            'std_agreement': np.std(agreement_scores),
            'min_agreement': np.min(agreement_scores),
            'max_agreement': np.max(agreement_scores),
            'num_annotators': len(set(annotators)),
            'total_annotations': len(annotators),
            'agreement_scores': agreement_scores
        }
    
    def create_agreement_improvement_plot(self, agreement_data: Dict[str, Any], output_path: str = "agreement_improvement.png"):
        """Create a plot showing agreement improvement over time."""
        # Create subplots for coref and mention agreement
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Create meaningful content using available data
        # Plot 1: Agreement Score Summary
        if agreement_data:
            # Create a summary of agreement scores if available
            scores = []
            labels = []
            
            if 'coref' in agreement_data and agreement_data['coref']:
                coref = agreement_data['coref']
                if 'avg_agreement' in coref:
                    scores.append(coref['avg_agreement'])
                    labels.append('Coref Avg')
                if 'max_agreement' in coref:
                    scores.append(coref['max_agreement'])
                    labels.append('Coref Max')
            
            if 'mention' in agreement_data and agreement_data['mention']:
                mention = agreement_data['mention']
                if 'avg_agreement' in mention:
                    scores.append(mention['avg_agreement'])
                    labels.append('Mention Avg')
                if 'max_agreement' in mention:
                    scores.append(mention['max_agreement'])
                    labels.append('Mention Max')
            
            if scores:
                bars = ax1.bar(labels, scores, color=['blue', 'lightblue', 'green', 'lightgreen'][:len(scores)], alpha=0.7)
                ax1.set_title('Agreement Score Summary', fontsize=14, fontweight='bold')
                ax1.set_ylabel('Agreement Score', fontsize=12)
                ax1.set_ylim(0, 1)
                ax1.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar, score in zip(bars, scores):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                            f'{score:.3f}', ha='center', va='bottom')
            else:
                # Fallback content
                ax1.text(0.5, 0.5, 'No Agreement Data\nAvailable', 
                        ha='center', va='center', transform=ax1.transAxes, fontsize=12)
                ax1.set_title('Agreement Score Summary', fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3)
        else:
            # Fallback content
            ax1.text(0.5, 0.5, 'No Agreement Data\nAvailable', 
                    ha='center', va='center', transform=ax1.transAxes, fontsize=12)
            ax1.set_title('Agreement Score Summary', fontsize=14, fontweight='bold')
            ax1.grid(True, alpha=0.3)
        
        # Plot 2: Agreement Statistics Overview
        if agreement_data:
            stats_data = []
            stats_labels = []
            
            if 'coref' in agreement_data and agreement_data['coref']:
                coref = agreement_data['coref']
                if 'num_annotators' in coref:
                    stats_data.append(coref['num_annotators'])
                    stats_labels.append('Coref\nAnnotators')
                if 'total_scores' in coref:
                    stats_data.append(coref['total_scores'])
                    stats_labels.append('Coref\nScores')
            
            if 'mention' in agreement_data and agreement_data['mention']:
                mention = agreement_data['mention']
                if 'num_annotators' in mention:
                    stats_data.append(mention['num_annotators'])
                    stats_labels.append('Mention\nAnnotators')
                if 'total_scores' in mention:
                    stats_data.append(mention['total_scores'])
                    stats_labels.append('Mention\nScores')
            
            if stats_data:
                bars = ax2.bar(stats_labels, stats_data, color=['orange', 'red', 'purple', 'brown'][:len(stats_data)], alpha=0.7)
                ax2.set_title('Annotation Statistics Overview', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Count', fontsize=12)
                ax2.grid(True, alpha=0.3)
                
                # Add value labels on bars
                for bar, value in zip(bars, stats_data):
                    height = bar.get_height()
                    ax2.text(bar.get_x() + bar.get_width()/2., height + max(stats_data)*0.01,
                            f'{value}', ha='center', va='bottom')
            else:
                # Fallback content
                ax2.text(0.5, 0.5, 'No Statistics Data\nAvailable', 
                        ha='center', va='center', transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Annotation Statistics Overview', fontsize=14, fontweight='bold')
                ax2.grid(True, alpha=0.3)
        else:
            # Fallback content
            ax2.text(0.5, 0.5, 'No Statistics Data\nAvailable', 
                    ha='center', va='center', transform=ax2.transAxes, fontsize=12)
            ax2.set_title('Annotation Statistics Overview', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Agreement improvement plot saved to {output_path}")
    
    def print_statistics(self, data_stats: Dict[str, Any], agreement_stats: Dict[str, Any]):
        """Print comprehensive statistics."""
        print("=" * 80)
        print("HEBREW NP CHUNKER - DATA STATISTICS")
        print("=" * 80)
        
        # Data statistics
        print("\n📊 DATA STATISTICS")
        print("-" * 40)
        
        total_docs = 0
        total_sentences = 0
        total_tokens = 0
        
        for split in ['train', 'dev', 'test']:
            if split in data_stats:
                stats = data_stats[split]
                print(f"\n{split.upper()} SPLIT:")
                print(f"  Number of documents: {stats['num_documents']}")
                print(f"  Number of sentences: {stats['num_sentences']}")
                print(f"  Number of tokens: {stats['num_tokens']}")
                print(f"  Average sentences per document: {stats['avg_sentences_per_doc']:.2f}")
                print(f"  Median sentences per document: {stats['median_sentences_per_doc']:.2f}")
                print(f"  Average tokens per document: {stats['avg_tokens_per_doc']:.2f}")
                print(f"  Median tokens per document: {stats['median_tokens_per_doc']:.2f}")
                
                total_docs += stats['num_documents']
                total_sentences += stats['num_sentences']
                total_tokens += stats['num_tokens']
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"  Total documents: {total_docs}")
        print(f"  Total sentences: {total_sentences}")
        print(f"  Total tokens: {total_tokens}")
        
        # Agreement statistics
        print("\n🤝 AGREEMENT STATISTICS")
        print("-" * 40)
        
        if 'coref' in agreement_stats and agreement_stats['coref']:
            coref = agreement_stats['coref']
            print(f"\nCoreference Agreement:")
            print(f"  Average agreement: {coref['avg_agreement']:.3f}")
            print(f"  Median agreement: {coref['median_agreement']:.3f}")
            print(f"  Standard deviation: {coref['std_agreement']:.3f}")
            print(f"  Min agreement: {coref['min_agreement']:.3f}")
            print(f"  Max agreement: {coref['max_agreement']:.3f}")
            print(f"  Number of annotators: {coref['num_annotators']}")
            print(f"  Total annotations: {coref['total_annotations']}")
        
        if 'mention' in agreement_stats and agreement_stats['mention']:
            mention = agreement_stats['mention']
            print(f"\nMention Agreement:")
            print(f"  Average agreement: {mention['avg_agreement']:.3f}")
            print(f"  Median agreement: {mention['median_agreement']:.3f}")
            print(f"  Standard deviation: {mention['std_agreement']:.3f}")
            print(f"  Min agreement: {mention['min_agreement']:.3f}")
            print(f"  Max agreement: {mention['max_agreement']:.3f}")
            print(f"  Number of annotators: {mention['num_annotators']}")
            print(f"  Total annotations: {mention['total_annotations']}")
        
        print("\n" + "=" * 80)
    
    def save_statistics_to_file(self, data_stats: Dict[str, Any], agreement_stats: Dict[str, Any], output_file: str = "data_statistics.json"):
        """Save statistics to a JSON file."""
        combined_stats = {
            'data_statistics': data_stats,
            'agreement_statistics': agreement_stats,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(combined_stats, f, indent=2, ensure_ascii=False)
        
        print(f"Statistics saved to {output_file}")
    
    def run_analysis(self, output_dir: str = "outputs/statistics"):
        """Run the complete analysis."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("Starting data statistics analysis...")
        
        # Analyze data statistics
        print("Analyzing CONLLU files...")
        data_stats = self.analyze_conllu_files()
        
        # Analyze agreement data
        print("Analyzing agreement data...")
        agreement_stats = self.analyze_agreement_data()
        
        # Print statistics
        self.print_statistics(data_stats, agreement_stats)
        
        # Create agreement improvement plot
        print("Creating agreement improvement plot...")
        self.create_agreement_improvement_plot(
            agreement_stats, 
            output_path / "agreement_improvement.png"
        )
        
        # Save statistics to file
        self.save_statistics_to_file(
            data_stats, 
            agreement_stats, 
            output_path / "data_statistics.json"
        )
        
        print(f"\nAnalysis complete! Results saved to {output_path}")
        return data_stats, agreement_stats


def main():
    parser = argparse.ArgumentParser(description='Analyze Hebrew NP Chunker data statistics')
    parser.add_argument('--data-root', default='../data/corpus/coreference_final_split',
                       help='Root directory for data files')
    parser.add_argument('--output-dir', default='outputs/statistics',
                       help='Output directory for results')
    parser.add_argument('--split-type', default='with_singleton',
                       choices=['with_singleton', 'no_singleton'],
                       help='Type of data split to analyze')
    
    args = parser.parse_args()
    
    # Create analyzer and run analysis
    analyzer = DataStatisticsAnalyzer(args.data_root)
    analyzer.run_analysis(args.output_dir)


if __name__ == "__main__":
    main() 
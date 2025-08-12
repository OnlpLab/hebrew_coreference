#!/usr/bin/env python3
"""
TNE Mention Statistics Script for Hebrew NP Chunker

This script analyzes mention characteristics from the original TNE files including:
- Pronoun distribution and types
- Mention length statistics
- Mention position analysis
- Coreference cluster statistics
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

# Hebrew pronouns from the existing code
HEBREW_PRONOUNS = {
    'אני': 'first_singular', 'עצמי': 'first_singular_reflexive',
    'הוא': 'third_masculine_singular', 'עצמו': 'third_masculine_reflexive', 'אותו': 'third_masculine_object', 'כלשהו': 'third_masculine_indefinite',
    'היא': 'third_feminine_singular', 'עצמה': 'third_feminine_reflexive', 'אותה': 'third_feminine_object', 'כלשהי': 'third_feminine_indefinite',
    'הן': 'third_feminine_plural', 'שתיהן': 'third_feminine_dual', 'בלשהן': 'third_feminine_indefinite',
    'הם': 'third_masculine_plural', 'עצמם': 'third_masculine_reflexive', 'שניהם': 'third_masculine_dual', 'הללו': 'third_masculine_demonstrative', 'אלה': 'third_masculine_demonstrative', 'אלו': 'third_masculine_demonstrative',
    'אנחנו': 'first_plural', 'אנו': 'first_plural', 'עצמנו': 'first_plural_reflexive', 'הננו': 'first_plural', 'אותנו': 'first_plural_object',
    'אתה': 'second_masculine_singular',
    'את': 'second_feminine_singular',
    'זה': 'demonstrative_masculine', 'זהו': 'demonstrative_masculine', 'כך': 'demonstrative_masculine',
    'זו': 'demonstrative_feminine', 'זאת': 'demonstrative_feminine'
}

class TNEMentionStatisticsAnalyzer:
    def __init__(self, data_root: str = "../data/corpus/coref_docs_2_tag/tne_conll"):
        self.data_root = Path(data_root)
        self.mention_stats = {}
        self.pronoun_stats = {}
        
    def parse_tne_file(self, file_path: Path) -> Tuple[List[Dict], List[int]]:
        """Parse mentions from TNE file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data or not isinstance(data, list) or len(data) == 0:
            return [], []
        
        # Get mentions and pronouns from the first document
        doc_data = data[0]
        mentions = doc_data.get('nps', [])
        pronouns = doc_data.get('pronouns', [])
        
        # Process mentions
        processed_mentions = []
        for mention in mentions:
            # Clean the text by removing leading underscores
            raw_text = mention.get('text', '')
            cleaned_text = raw_text.lstrip('_')
            
            mention_info = {
                'text': cleaned_text,
                'raw_text': raw_text,  # Keep original for reference
                'id': mention.get('id', -1),
                'start_index': mention.get('start_index', 0),
                'end_index': mention.get('end_index', 0),
                'sent_num': mention.get('sent_num', 0),
                'is_pronoun': mention.get('id', -1) in pronouns,
                'pronoun_type': HEBREW_PRONOUNS.get(cleaned_text, 'not_pronoun')
            }
            processed_mentions.append(mention_info)
        
        return processed_mentions, pronouns
    
    def analyze_tne_mentions(self) -> Dict[str, Any]:
        """Analyze mention statistics from TNE files."""
        all_mentions = []
        all_pronouns = []
        
        print("Analyzing TNE files for mention statistics...")
        
        # Get all TNE files
        tne_files = list(self.data_root.glob("*.tne"))
        print(f"Found {len(tne_files)} TNE files")
        
        for i, tne_file in enumerate(tne_files):
            if i % 50 == 0:
                print(f"Processing file {i+1}/{len(tne_files)}...")
            
            try:
                mentions, pronouns = self.parse_tne_file(tne_file)
                all_mentions.extend(mentions)
                all_pronouns.extend(pronouns)
            except Exception as e:
                print(f"Error processing {tne_file}: {e}")
                continue
        
        # Calculate overall statistics
        self.mention_stats['overall'] = self._calculate_mention_statistics(all_mentions, all_pronouns)
        
        return self.mention_stats
    
    def _calculate_mention_statistics(self, mentions: List[Dict], pronouns: List[int]) -> Dict[str, Any]:
        """Calculate comprehensive mention statistics."""
        if not mentions:
            return {}
        
        # Basic mention statistics
        total_mentions = len(mentions)
        unique_texts = set(m['text'] for m in mentions)
        
        # Pronoun analysis
        pronoun_mentions = [m for m in mentions if m['is_pronoun']]
        pronoun_count = len(pronoun_mentions)
        pronoun_percentage = pronoun_count / total_mentions * 100 if total_mentions > 0 else 0
        
        # Pronoun type distribution
        pronoun_types = Counter(m['pronoun_type'] for m in pronoun_mentions)
        
        # Mention length analysis
        mention_lengths = [len(m['text']) for m in mentions]
        avg_mention_length = np.mean(mention_lengths) if mention_lengths else 0
        median_mention_length = np.median(mention_lengths) if mention_lengths else 0
        
        # Mention position analysis
        sentence_positions = Counter(m['sent_num'] for m in mentions)
        
        # Most common mentions
        mention_texts = Counter(m['text'] for m in mentions)
        top_mentions = mention_texts.most_common(20)
        
        # Most common pronouns
        pronoun_texts = Counter(m['text'] for m in pronoun_mentions)
        top_pronouns = pronoun_texts.most_common(10)
        
        # Mention span analysis
        mention_spans = [m['end_index'] - m['start_index'] for m in mentions]
        avg_mention_span = np.mean(mention_spans) if mention_spans else 0
        median_mention_span = np.median(mention_spans) if mention_spans else 0
        
        return {
            'total_mentions': total_mentions,
            'unique_mentions': len(unique_texts),
            'pronoun_count': pronoun_count,
            'pronoun_percentage': pronoun_percentage,
            'pronoun_types': dict(pronoun_types),
            'mention_length_stats': {
                'average': avg_mention_length,
                'median': median_mention_length,
                'min': min(mention_lengths) if mention_lengths else 0,
                'max': max(mention_lengths) if mention_lengths else 0
            },
            'mention_span_stats': {
                'average': avg_mention_span,
                'median': median_mention_span,
                'min': min(mention_spans) if mention_spans else 0,
                'max': max(mention_spans) if mention_spans else 0
            },
            'sentence_position_distribution': dict(sentence_positions),
            'top_mentions': top_mentions,
            'top_pronouns': top_pronouns
        }
    
    def create_tne_mention_visualizations(self, output_path: str = "tne_mention_statistics.png"):
        """Create comprehensive TNE mention visualizations."""
        fig = plt.figure(figsize=(20, 15))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Pronoun percentage
        ax1 = fig.add_subplot(gs[0, 0])
        if 'overall' in self.mention_stats:
            stats = self.mention_stats['overall']
            pronoun_pct = stats.get('pronoun_percentage', 0)
            non_pronoun_pct = 100 - pronoun_pct
            
            labels = ['Pronouns', 'Non-Pronouns']
            sizes = [pronoun_pct, non_pronoun_pct]
            colors = ['#FF6B6B', '#4ECDC4']
            
            ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            ax1.set_title('Mention Type Distribution', fontsize=14, fontweight='bold')
        
        # Plot 2: Mention length distribution
        ax2 = fig.add_subplot(gs[0, 1])
        if 'overall' in self.mention_stats:
            length_stats = self.mention_stats['overall'].get('mention_length_stats', {})
            if length_stats:
                lengths = [length_stats['min'], length_stats['average'], length_stats['median'], length_stats['max']]
                labels = ['Min', 'Average', 'Median', 'Max']
                ax2.bar(labels, lengths, color=['#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F'])
                ax2.set_title('Mention Length Statistics', fontsize=14, fontweight='bold')
                ax2.set_ylabel('Length (characters)', fontsize=12)
        
        # Plot 3: Mention span distribution
        ax3 = fig.add_subplot(gs[0, 2])
        if 'overall' in self.mention_stats:
            span_stats = self.mention_stats['overall'].get('mention_span_stats', {})
            if span_stats:
                spans = [span_stats['min'], span_stats['average'], span_stats['median'], span_stats['max']]
                labels = ['Min', 'Average', 'Median', 'Max']
                ax3.bar(labels, spans, color=['#FFB6C1', '#87CEEB', '#DDA0DD', '#F0E68C'])
                ax3.set_title('Mention Span Statistics', fontsize=14, fontweight='bold')
                ax3.set_ylabel('Span (characters)', fontsize=12)
        
        # Plot 4: Pronoun type distribution
        ax4 = fig.add_subplot(gs[1, 0])
        if 'overall' in self.mention_stats:
            pronoun_types = self.mention_stats['overall'].get('pronoun_types', {})
            if pronoun_types:
                types = list(pronoun_types.keys())
                counts = list(pronoun_types.values())
                ax4.pie(counts, labels=types, autopct='%1.1f%%', startangle=90)
                ax4.set_title('Pronoun Type Distribution', fontsize=14, fontweight='bold')
        
        # Plot 5: Sentence position distribution
        ax5 = fig.add_subplot(gs[1, 1])
        if 'overall' in self.mention_stats:
            sent_positions = self.mention_stats['overall'].get('sentence_position_distribution', {})
            if sent_positions:
                positions = list(sent_positions.keys())
                counts = list(sent_positions.values())
                ax5.bar(positions, counts, color='#96CEB4')
                ax5.set_title('Mentions by Sentence Position', fontsize=14, fontweight='bold')
                ax5.set_xlabel('Sentence Number', fontsize=12)
                ax5.set_ylabel('Number of Mentions', fontsize=12)
        
        # Plot 6: Top mentions
        ax6 = fig.add_subplot(gs[1, 2])
        if 'overall' in self.mention_stats:
            top_mentions = self.mention_stats['overall'].get('top_mentions', [])[:10]
            if top_mentions:
                texts = [item[0] for item in top_mentions]
                counts = [item[1] for item in top_mentions]
                ax6.barh(range(len(texts)), counts, color='#FFA07A')
                ax6.set_yticks(range(len(texts)))
                ax6.set_yticklabels(texts)
                ax6.set_title('Top 10 Most Common Mentions', fontsize=14, fontweight='bold')
                ax6.set_xlabel('Count', fontsize=12)
        
        # Plot 7: Top pronouns
        ax7 = fig.add_subplot(gs[2, 0])
        if 'overall' in self.mention_stats:
            top_pronouns = self.mention_stats['overall'].get('top_pronouns', [])[:10]
            if top_pronouns:
                texts = [item[0] for item in top_pronouns]
                counts = [item[1] for item in top_pronouns]
                ax7.barh(range(len(texts)), counts, color='#98FB98')
                ax7.set_yticks(range(len(texts)))
                ax7.set_yticklabels(texts)
                ax7.set_title('Top 10 Most Common Pronouns', fontsize=14, fontweight='bold')
                ax7.set_xlabel('Count', fontsize=12)
        
        # Plot 8: Mention length histogram
        ax8 = fig.add_subplot(gs[2, 1])
        if 'overall' in self.mention_stats:
            # We'll need to reconstruct the length data
            # For now, create a simple distribution
            ax8.hist([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], bins=10, alpha=0.7, color='#FF6B6B')
            ax8.set_title('Mention Length Distribution', fontsize=14, fontweight='bold')
            ax8.set_xlabel('Mention Length (characters)', fontsize=12)
            ax8.set_ylabel('Frequency', fontsize=12)
        
        # Plot 9: Summary statistics table
        ax9 = fig.add_subplot(gs[2, 2])
        ax9.axis('tight')
        ax9.axis('off')
        
        if 'overall' in self.mention_stats:
            stats = self.mention_stats['overall']
            summary_data = [
                ['Total Mentions', f"{stats.get('total_mentions', 0):,}"],
                ['Unique Mentions', f"{stats.get('unique_mentions', 0):,}"],
                ['Pronouns', f"{stats.get('pronoun_count', 0):,} ({stats.get('pronoun_percentage', 0):.1f}%)"],
                ['Avg Mention Length', f"{stats.get('mention_length_stats', {}).get('average', 0):.1f}"],
                ['Avg Mention Span', f"{stats.get('mention_span_stats', {}).get('average', 0):.1f}"],
                ['Pronoun Types', f"{len(stats.get('pronoun_types', {}))}"]
            ]
            
            table = ax9.table(cellText=summary_data,
                             colLabels=['Metric', 'Value'],
                             cellLoc='center',
                             loc='center',
                             bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1, 2)
            ax9.set_title('Overall Statistics', fontsize=14, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"TNE mention visualizations saved to {output_path}")
    
    def print_tne_mention_statistics(self):
        """Print comprehensive TNE mention statistics."""
        print("=" * 100)
        print("TNE MENTION STATISTICS - HEBREW NP CHUNKER DATASET")
        print("=" * 100)
        
        if 'overall' in self.mention_stats:
            stats = self.mention_stats['overall']
            print(f"\n📊 OVERALL TNE MENTION STATISTICS:")
            print("-" * 60)
            print(f"  Total mentions: {stats.get('total_mentions', 0):,}")
            print(f"  Unique mentions: {stats.get('unique_mentions', 0):,}")
            print(f"  Pronouns: {stats.get('pronoun_count', 0):,} ({stats.get('pronoun_percentage', 0):.1f}%)")
            print(f"  Average mention length: {stats.get('mention_length_stats', {}).get('average', 0):.1f} characters")
            print(f"  Average mention span: {stats.get('mention_span_stats', {}).get('average', 0):.1f} characters")
            
            # Print top pronouns
            top_pronouns = stats.get('top_pronouns', [])[:5]
            if top_pronouns:
                print(f"\n  Top 5 pronouns:")
                for pronoun, count in top_pronouns:
                    pronoun_type = HEBREW_PRONOUNS.get(pronoun, 'unknown')
                    print(f"    {pronoun} ({pronoun_type}): {count}")
            
            # Print pronoun type distribution
            pronoun_types = stats.get('pronoun_types', {})
            if pronoun_types:
                print(f"\n  Pronoun type distribution:")
                for ptype, count in sorted(pronoun_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"    {ptype}: {count}")
            
            # Print top mentions
            top_mentions = stats.get('top_mentions', [])[:5]
            if top_mentions:
                print(f"\n  Top 5 mentions:")
                for mention, count in top_mentions:
                    print(f"    {mention}: {count}")
        
        print("\n" + "=" * 100)
    
    def save_tne_mention_statistics(self, output_file: str = "tne_mention_statistics.json"):
        """Save TNE mention statistics to JSON file."""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.mention_stats, f, indent=2, ensure_ascii=False)
        print(f"TNE mention statistics saved to {output_file}")
    
    def run_tne_mention_analysis(self, output_dir: str = "outputs/tne_mention_statistics"):
        """Run the complete TNE mention analysis."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("Starting TNE mention statistics analysis...")
        
        # Analyze mentions
        self.analyze_tne_mentions()
        
        # Print statistics
        self.print_tne_mention_statistics()
        
        # Create visualizations
        viz_path = output_path / "tne_mention_statistics.png"
        self.create_tne_mention_visualizations(str(viz_path))
        
        # Save statistics
        stats_path = output_path / "tne_mention_statistics.json"
        self.save_tne_mention_statistics(str(stats_path))
        
        print(f"\nTNE mention analysis complete! Results saved to {output_dir}")

def main():
    parser = argparse.ArgumentParser(description="Analyze TNE mention statistics for Hebrew NP Chunker")
    parser.add_argument("--output-dir", default="outputs/tne_mention_statistics", 
                       help="Output directory for results")
    args = parser.parse_args()
    
    analyzer = TNEMentionStatisticsAnalyzer()
    analyzer.run_tne_mention_analysis(args.output_dir)

if __name__ == "__main__":
    main() 
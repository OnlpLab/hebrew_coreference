#!/usr/bin/env python3
"""
Comprehensive Error Analysis Script for Hebrew Coreference Resolution

This script compares the mistakes between different approaches:
- LLM vs Neural models
- Different tokenization strategies (gold, SOTA, raw)
- Analyzes cluster-level and mention-level errors
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
from collections import defaultdict, Counter
import argparse
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class Mention:
    """Represents a mention with its position and text"""
    start: int
    end: int
    text: str
    sent_id: int
    
    def __post_init__(self):
        if isinstance(self.start, list):
            self.start = self.start[0]
        if isinstance(self.end, list):
            self.end = self.end[0]

@dataclass
class Cluster:
    """Represents a coreference cluster"""
    mentions: List[Mention]
    cluster_id: int
    
    def get_span_texts(self) -> List[str]:
        """Get all text spans in this cluster"""
        return [f"{m.start}-{m.end}:{m.text}" for m in self.mentions]

class CorefAnalyzer:
    """Analyzes coreference resolution results and compares them with gold annotations"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.gold_path = self.base_path / "gold"
        self.llm_path = self.base_path / "llm"
        self.neural_path = self.base_path / "neural"
        
    def load_conllu_file(self, file_path: str) -> Dict[str, Any]:
        """Load CONLLU file and extract coreference information"""
        clusters = []
        tokens = []
        sentences = []
        current_sent = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('# begin document'):
                    continue
                elif line.startswith('# end document'):
                    break
                elif line == '':
                    if current_sent:
                        sentences.append(current_sent)
                        current_sent = []
                    continue
                else:
                    parts = line.split('\t')
                    if len(parts) >= 10:
                        token = parts[1]
                        tokens.append(token)
                        current_sent.append(token)
                        
                        # Check for coreference annotation
                        coref_info = parts[-1]
                        if coref_info != '_':
                            # Parse coreference information
                            if '(' in coref_info:
                                # Start of mention
                                cluster_id = int(coref_info.strip('()'))
                                clusters.append([len(tokens) - 1])
                            elif ')' in coref_info:
                                # End of mention
                                cluster_id = int(coref_info.strip('()'))
                                if clusters and len(clusters[-1]) == 1:
                                    clusters[-1].append(len(tokens) - 1)
        
        if current_sent:
            sentences.append(current_sent)
            
        return {
            'clusters': clusters,
            'tokens': tokens,
            'sentences': sentences
        }
    
    def load_jsonl_file(self, file_path: str) -> Dict[str, Any]:
        """Load JSONL file with predictions"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line.strip())
                return data
        return {}
    
    def load_raw_text(self, file_path: str) -> str:
        """Load raw text file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    
    def extract_mentions_from_clusters(self, clusters: List[List[int]], tokens: List[str], sent_ids: List[int] = None) -> List[Mention]:
        """Extract mention objects from cluster format"""
        mentions = []
        for cluster in clusters:
            if len(cluster) >= 2:
                start, end = cluster[0], cluster[1]
                text = ' '.join(tokens[start:end+1])
                sent_id = sent_ids[start] if sent_ids else 0
                mentions.append(Mention(start, end, text, sent_id))
        return mentions
    
    def extract_mentions_from_neural_format(self, data: Dict[str, Any]) -> List[Mention]:
        """Extract mentions from neural model output format"""
        mentions = []
        if 'clusters' in data:
            for cluster_id, cluster in enumerate(data['clusters']):
                for mention in cluster:
                    if len(mention) >= 2:
                        start, end = mention[0], mention[1]
                        text = ' '.join(data['tokens'][start:end+1])
                        sent_id = data['sent_id'][start] if 'sent_id' in data else 0
                        mentions.append(Mention(start, end, text, sent_id))
        return mentions
    
    def calculate_cluster_metrics(self, gold_clusters: List[List[Mention]], pred_clusters: List[List[Mention]]) -> Dict[str, float]:
        """Calculate precision, recall, and F1 for clusters"""
        gold_mentions = set()
        pred_mentions = set()
        
        # Convert clusters to mention sets
        for cluster in gold_clusters:
            for mention in cluster:
                gold_mentions.add((mention.start, mention.end))
        
        for cluster in pred_clusters:
            for mention in cluster:
                pred_mentions.add((mention.start, mention.end))
        
        # Calculate metrics
        correct = len(gold_mentions.intersection(pred_mentions))
        precision = correct / len(pred_mentions) if pred_mentions > 0 else 0.0
        recall = correct / len(gold_mentions) if gold_mentions > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'gold_mentions': len(gold_mentions),
            'pred_mentions': len(pred_clusters),
            'correct_mentions': correct
        }
    
    def analyze_cluster_errors(self, gold_clusters: List[List[Mention]], pred_clusters: List[List[Mention]]) -> Dict[str, Any]:
        """Analyze specific types of errors in clustering"""
        errors = {
            'missing_clusters': [],
            'extra_clusters': [],
            'split_clusters': [],
            'merged_clusters': [],
            'boundary_errors': []
        }
        
        # Convert to mention sets for easier comparison
        gold_mentions = set()
        for cluster in gold_clusters:
            cluster_mentions = set()
            for mention in cluster:
                mention_key = (mention.start, mention.end)
                gold_mentions.add(mention_key)
                cluster_mentions.add(mention_key)
            errors['missing_clusters'].append(cluster_mentions)
        
        pred_mentions = set()
        for cluster in pred_clusters:
            cluster_mentions = set()
            for mention in cluster:
                mention_key = (mention.start, mention.end)
                pred_mentions.add(mention_key)
                cluster_mentions.add(mention_key)
            errors['extra_clusters'].append(cluster_mentions)
        
        # Find missing mentions
        missing = gold_mentions - pred_mentions
        extra = pred_mentions - gold_mentions
        
        return {
            'missing_mentions': len(missing),
            'extra_mentions': len(extra),
            'correct_mentions': len(gold_mentions.intersection(pred_mentions)),
            'total_gold': len(gold_mentions),
            'total_pred': len(pred_mentions),
            'missing_mention_details': list(missing),
            'extra_mention_details': list(extra)
        }
    
    def compare_approaches(self, doc_id: str = "240") -> Dict[str, Any]:
        """Compare all approaches for a given document"""
        results = {}
        
        # Load gold annotation
        gold_conllu = self.gold_path / "conllu" / f"htb:{doc_id}.conllu"
        if gold_conllu.exists():
            gold_data = self.load_conllu_file(str(gold_conllu))
            gold_clusters = []
            for cluster in gold_data['clusters']:
                if len(cluster) >= 2:
                    mentions = self.extract_mentions_from_clusters([cluster], gold_data['tokens'])
                    gold_clusters.append(mentions)
            results['gold'] = {
                'clusters': gold_clusters,
                'total_mentions': sum(len(cluster) for cluster in gold_clusters)
            }
        
        # Load LLM results
        llm_approaches = ['raw', 'tokenized', 'sota_tokenized']
        for approach in llm_approaches:
            llm_file = self.llm_path / approach / f"llm_{approach}_{doc_id}.jsonl"
            if llm_file.exists():
                llm_data = self.load_jsonl_file(str(llm_file))
                if 'predicted_clusters' in llm_data:
                    pred_clusters = []
                    for cluster in llm_data['predicted_clusters']:
                        mentions = self.extract_mentions_from_clusters([cluster], llm_data.get('tokens', []))
                        pred_clusters.append(mentions)
                    
                    if 'gold' in results:
                        metrics = self.calculate_cluster_metrics(results['gold']['clusters'], pred_clusters)
                        errors = self.analyze_cluster_errors(results['gold']['clusters'], pred_clusters)
                        results[f'llm_{approach}'] = {
                            'clusters': pred_clusters,
                            'metrics': metrics,
                            'errors': errors,
                            'total_mentions': sum(len(cluster) for cluster in pred_clusters)
                        }
        
        # Load Neural results
        neural_approaches = ['gold', 'sota_tokenized']
        for approach in neural_approaches:
            neural_file = self.neural_path / approach / f"neural_{approach}_tokenization_{doc_id}.jsonl"
            if neural_file.exists():
                neural_data = self.load_jsonl_file(str(neural_file))
                if 'clusters' in neural_data:
                    pred_clusters = []
                    for cluster in neural_data['clusters']:
                        mentions = self.extract_mentions_from_neural_format({'clusters': [cluster], 'tokens': neural_data['tokens'], 'sent_id': neural_data.get('sent_id', [])})
                        if mentions:
                            pred_clusters.append(mentions)
                    
                    if 'gold' in results:
                        metrics = self.calculate_cluster_metrics(results['gold']['clusters'], pred_clusters)
                        errors = self.analyze_cluster_errors(results['gold']['clusters'], pred_clusters)
                        results[f'neural_{approach}'] = {
                            'clusters': pred_clusters,
                            'metrics': metrics,
                            'errors': errors,
                            'total_mentions': sum(len(cluster) for cluster in pred_clusters)
                        }
        
        return results
    
    def generate_error_report(self, comparison_results: Dict[str, Any], doc_id: str) -> str:
        """Generate a comprehensive error report"""
        report = []
        report.append(f"=== Coreference Error Analysis Report for Document {doc_id} ===\n")
        
        if 'gold' not in comparison_results:
            report.append("ERROR: Gold annotations not found!")
            return '\n'.join(report)
        
        gold_mentions = comparison_results['gold']['total_mentions']
        report.append(f"Gold Annotations: {gold_mentions} mentions\n")
        
        # Compare approaches
        approaches = [k for k in comparison_results.keys() if k != 'gold']
        
        for approach in approaches:
            if approach in comparison_results:
                data = comparison_results[approach]
                metrics = data['metrics']
                errors = data['errors']
                
                report.append(f"--- {approach.upper()} ---")
                report.append(f"Precision: {metrics['precision']:.3f}")
                report.append(f"Recall: {metrics['recall']:.3f}")
                report.append(f"F1: {metrics['f1']:.3f}")
                report.append(f"Total Mentions: {data['total_mentions']}")
                report.append(f"Missing Mentions: {errors['missing_mentions']}")
                report.append(f"Extra Mentions: {errors['extra_mentions']}")
                report.append(f"Correct Mentions: {errors['correct_mentions']}")
                report.append("")
        
        # Find best performing approach
        best_approach = None
        best_f1 = 0.0
        
        for approach in approaches:
            if approach in comparison_results:
                f1 = comparison_results[approach]['metrics']['f1']
                if f1 > best_f1:
                    best_f1 = f1
                    best_approach = approach
        
        if best_approach:
            report.append(f"Best Performing Approach: {best_approach} (F1: {best_f1:.3f})")
        
        return '\n'.join(report)
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """Save analysis results to JSON file"""
        # Convert dataclasses to dictionaries for JSON serialization
        serializable_results = {}
        for key, value in results.items():
            if key == 'gold':
                serializable_results[key] = {
                    'total_mentions': value['total_mentions'],
                    'cluster_count': len(value['clusters'])
                }
            elif key != 'gold':
                serializable_results[key] = {
                    'metrics': value['metrics'],
                    'errors': value['errors'],
                    'total_mentions': value['total_mentions']
                }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description='Analyze coreference resolution errors')
    parser.add_argument('--base-path', type=str, 
                       default='/Users/s0g0a87/studies/hebrew coreference/error_analysis/error_analysis_data',
                       help='Base path to error analysis data')
    parser.add_argument('--doc-id', type=str, default='240', help='Document ID to analyze')
    parser.add_argument('--output', type=str, help='Output file for results')
    parser.add_argument('--report', type=str, help='Output file for text report')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = CorefAnalyzer(args.base_path)
    
    # Perform analysis
    logger.info(f"Analyzing document {args.doc_id}")
    results = analyzer.compare_approaches(args.doc_id)
    
    # Generate report
    report = analyzer.generate_error_report(results, args.doc_id)
    print(report)
    
    # Save results if requested
    if args.output:
        analyzer.save_results(results, args.output)
        logger.info(f"Results saved to {args.output}")
    
    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)
        logger.info(f"Report saved to {args.report}")

if __name__ == "__main__":
    main() 
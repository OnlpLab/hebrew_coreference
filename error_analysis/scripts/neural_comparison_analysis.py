#!/usr/bin/env python3
"""
Neural Model Comparison Analysis: Gold vs SOTA Tokenization
Focuses on detailed mistake analysis and human-readable output
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Set
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NeuralComparisonAnalyzer:
    def __init__(self):
        self.neural_gold = {}
        self.neural_sota = {}
        self.gold_standard = {}
        self.document_mapping = {}
        self.token_data = {}  # Store token information for each document
        
    def load_document_mapping(self, mapping_file: str):
        """Load document mapping between neural model keys and gold standard keys."""
        logger.info("Loading document mapping...")
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                self.document_mapping = json.load(f)
            logger.info(f"Loaded document mapping for {len(self.document_mapping)} documents")
            
            # Create reverse mapping for convenience
            self.reverse_mapping = {v: k for k, v in self.document_mapping.items()}
        except Exception as e:
            logger.error(f"Failed to load document mapping: {e}")
            raise
    
    def load_neural_results(self, gold_file: str, sota_file: str):
        """Load neural model results for both gold and SOTA tokenization."""
        logger.info("Loading neural model results...")
        
        # Load gold tokenization results
        try:
            with open(gold_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        self.neural_gold[data['doc_key']] = data
        except json.JSONDecodeError:
            # Try as single JSON array
            with open(gold_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    self.neural_gold[item['doc_key']] = item
        
        # Load SOTA tokenization results
        try:
            with open(sota_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        self.neural_sota[data['doc_key']] = data
        except json.JSONDecodeError:
            # Try as single JSON array
            with open(sota_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data:
                    self.neural_sota[item['doc_key']] = data
        
        logger.info(f"Loaded {len(self.neural_gold)} gold tokenization documents")
        logger.info(f"Loaded {len(self.neural_sota)} SOTA tokenization documents")
    
    def load_gold_standard(self, conllu_dir: str):
        """Load gold standard data from CoNLL-U files."""
        logger.info("Loading gold standard data...")
        
        conllu_path = Path(conllu_dir)
        for conllu_file in conllu_path.glob("*.conllu"):
            doc_key = conllu_file.stem
            clusters = self.parse_conllu_clusters(conllu_file)
            self.gold_standard[doc_key] = {'clusters': clusters}
            
            # Also load token data for human-readable output
            self.token_data[doc_key] = self.load_tokens_from_conllu(conllu_file)
        
        logger.info(f"Loaded gold standard for {len(self.gold_standard)} documents")
    
    def load_tokens_from_conllu(self, conllu_file: Path) -> List[str]:
        """Load tokens from CoNLL-U file for human-readable output."""
        tokens = []
        try:
            with open(conllu_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line == '' or line.startswith('#'):
                        continue
                    
                    cols = line.split()
                    if len(cols) >= 1:
                        tokens.append(cols[0])  # First column is the token
        except Exception as e:
            logger.error(f"Error loading tokens from {conllu_file}: {e}")
        
        return tokens
    
    def parse_conllu_clusters(self, conllu_file: Path) -> List:
        """Parse clusters from a CoNLL-U file."""
        clusters = {}  # cluster_id -> list of spans
        open_mentions = {}  # cluster_id -> start_position
        
        try:
            with open(conllu_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line == '' or line.startswith('#'):
                        continue
                    
                    cols = line.split()
                    if len(cols) < 5:
                        continue
                    
                    token = cols[0]
                    sent_id = int(cols[1])
                    token_pos = int(cols[2])
                    coref = cols[4]  # 5th column (index 4) is coref annotation
                    
                    if coref != '_':
                        # Parse coref annotations
                        for annotation in coref.split('|'):
                            annotation = annotation.strip()
                            
                            if annotation.startswith('(') and annotation.endswith(')'):
                                # Single token cluster
                                cluster_id = annotation[1:-1]
                                if cluster_id.isdigit():
                                    cluster_id = int(cluster_id)
                                    if cluster_id not in clusters:
                                        clusters[cluster_id] = []
                                    clusters[cluster_id].append([token_pos, token_pos])
                            
                            elif annotation.startswith('('):
                                # Start of cluster
                                cluster_id = annotation[1:]
                                if cluster_id.isdigit():
                                    open_mentions[int(cluster_id)] = token_pos
                            
                            elif annotation.endswith(')'):
                                # End of cluster
                                cluster_id = annotation[:-1]
                                if cluster_id.isdigit():
                                    cluster_id = int(cluster_id)
                                    if cluster_id in open_mentions:
                                        start = open_mentions[cluster_id]
                                        if cluster_id not in clusters:
                                            clusters[cluster_id] = []
                                        clusters[cluster_id].append([start, token_pos])
                                        del open_mentions[cluster_id]
        
        except Exception as e:
            logger.error(f"Error parsing {conllu_file}: {e}")
        
        # Convert clusters from dict to list of lists
        output_clusters = []
        for cluster_id in sorted(clusters.keys(), key=int):
            output_clusters.append(clusters[cluster_id])
        
        return output_clusters
    
    def find_documents_with_errors(self) -> List[str]:
        """Find documents that have errors in both neural models."""
        error_docs = []
        
        for doc_key in self.gold_standard.keys():
            # Find corresponding neural document keys
            neural_key = None
            for neural_doc_key, gold_doc_key in self.document_mapping.items():
                if gold_doc_key == doc_key:
                    neural_key = neural_doc_key
                    break
            
            if neural_key and neural_key in self.neural_gold and neural_key in self.neural_sota:
                # Check if this document has errors
                gold_clusters = self.gold_standard[doc_key]['clusters']
                gold_pred = self.neural_gold[neural_key].get('clusters', [])
                sota_pred = self.neural_sota[neural_key].get('clusters', [])
                
                # Simple error check: if predictions don't exactly match gold
                if gold_pred != gold_clusters or sota_pred != gold_clusters:
                    error_docs.append(doc_key)
        
        return error_docs[:5]  # Return first 5 documents with errors
    
    def analyze_document_mistakes(self, doc_key: str) -> Dict:
        """Analyze mistakes for a specific document."""
        neural_key = self.reverse_mapping.get(doc_key)
        if not neural_key:
            return {}
        
        gold_clusters = self.gold_standard[doc_key]['clusters']
        gold_pred = self.neural_gold[neural_key].get('clusters', [])
        sota_pred = self.neural_sota[neural_key].get('clusters', [])
        tokens = self.token_data.get(doc_key, [])
        
        analysis = {
            'doc_key': doc_key,
            'neural_key': neural_key,
            'tokens': tokens,
            'gold_clusters': gold_clusters,
            'gold_pred': gold_pred,
            'sota_pred': sota_pred,
            'gold_errors': self.analyze_cluster_errors(gold_pred, gold_clusters),
            'sota_errors': self.analyze_cluster_errors(sota_pred, gold_clusters)
        }
        
        return analysis
    
    def analyze_cluster_errors(self, predicted: List, gold: List) -> Dict:
        """Analyze errors in predicted clusters compared to gold."""
        errors = {
            'missing_clusters': [],
            'extra_clusters': [],
            'boundary_errors': [],
            'linking_errors': []
        }
        
        # Find missing and extra clusters
        gold_set = {tuple(span) for cluster in gold for span in cluster}
        pred_set = {tuple(span) for cluster in predicted for span in cluster}
        
        missing = gold_set - pred_set
        extra = pred_set - gold_set
        
        if missing:
            errors['missing_clusters'] = list(missing)
        if extra:
            errors['extra_clusters'] = list(extra)
        
        # Analyze boundary and linking errors (simplified)
        # This is a basic analysis - could be enhanced with more sophisticated metrics
        
        return errors
    
    def print_human_readable_analysis(self, doc_analysis: Dict):
        """Print human-readable analysis of document mistakes."""
        print(f"\n{'='*80}")
        print(f"DOCUMENT ANALYSIS: {doc_analysis['doc_key']}")
        print(f"Neural Key: {doc_analysis['neural_key']}")
        print(f"{'='*80}")
        
        tokens = doc_analysis['tokens']
        print(f"\nTOKENS ({len(tokens)} total):")
        print(" ".join([f"{i}:{token}" for i, token in enumerate(tokens[:50])]) + ("..." if len(tokens) > 50 else ""))
        
        print(f"\nGOLD STANDARD CLUSTERS ({len(doc_analysis['gold_clusters'])} total):")
        for i, cluster in enumerate(doc_analysis['gold_clusters']):
            cluster_text = " | ".join([f"[{span[0]}-{span[1]}: {' '.join(tokens[span[0]:span[1]+1])}]" for span in cluster])
            print(f"  Cluster {i}: {cluster_text}")
        
        print(f"\nNEURAL GOLD PREDICTIONS ({len(doc_analysis['gold_pred'])} total):")
        for i, cluster in enumerate(doc_analysis['gold_pred']):
            cluster_text = " | ".join([f"[{span[0]}-{span[1]}: {' '.join(tokens[span[0]:span[1]+1])}]" for span in cluster])
            print(f"  Cluster {i}: {cluster_text}")
        
        print(f"\nNEURAL SOTA PREDICTIONS ({len(doc_analysis['sota_pred'])} total):")
        for i, cluster in enumerate(doc_analysis['sota_pred']):
            cluster_text = " | ".join([f"[{span[0]}-{span[1]}: {' '.join(tokens[span[0]:span[1]+1])}]" for span in cluster])
            print(f"  Cluster {i}: {cluster_text}")
        
        # Print error analysis
        print(f"\nERROR ANALYSIS:")
        print(f"  Gold Tokenization Errors:")
        gold_errors = doc_analysis['gold_errors']
        if gold_errors['missing_clusters']:
            print(f"    Missing: {len(gold_errors['missing_clusters'])} spans")
        if gold_errors['extra_clusters']:
            print(f"    Extra: {len(gold_errors['extra_clusters'])} spans")
        
        print(f"  SOTA Tokenization Errors:")
        sota_errors = doc_analysis['sota_errors']
        if sota_errors['missing_clusters']:
            print(f"    Missing: {len(sota_errors['missing_clusters'])} spans")
        if sota_errors['extra_clusters']:
            print(f"    Extra: {len(sota_errors['extra_clusters'])} spans")
        
        print(f"{'='*80}\n")
    
    def generate_comparison_visualizations(self, output_dir: str):
        """Generate visualizations comparing neural gold vs SOTA."""
        logger.info("Generating comparison visualizations...")
        
        # Prepare data for visualization
        metrics = ['boundary_only', 'linking_only', 'both']
        gold_scores = []
        sota_scores = []
        
        for doc_key in self.gold_standard.keys():
            neural_key = self.reverse_mapping.get(doc_key)
            if neural_key and neural_key in self.neural_gold and neural_key in self.neural_sota:
                # Calculate error metrics for this document
                gold_errors = self.calculate_document_errors(doc_key, self.neural_gold[neural_key])
                sota_errors = self.calculate_document_errors(doc_key, self.neural_sota[neural_key])
                
                gold_scores.append(gold_errors)
                sota_scores.append(sota_errors)
        
        if not gold_scores:
            logger.warning("No data available for visualization")
            return
        
        # Convert to numpy arrays for easier manipulation
        gold_scores = np.array(gold_scores)
        sota_scores = np.array(sota_scores)
        
        # Create comparison plots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Neural Gold vs SOTA Tokenization Comparison', fontsize=16)
        
        # 1. Error type comparison
        ax1 = axes[0, 0]
        x = np.arange(len(metrics))
        width = 0.35
        
        gold_means = np.mean(gold_scores, axis=0)
        sota_means = np.mean(sota_scores, axis=0)
        gold_stds = np.std(gold_scores, axis=0)
        sota_stds = np.std(sota_scores, axis=0)
        
        ax1.bar(x - width/2, gold_means, width, label='Gold Tokenization', yerr=gold_stds, capsize=5)
        ax1.bar(x + width/2, sota_means, width, label='SOTA Tokenization', yerr=sota_stds, capsize=5)
        
        ax1.set_xlabel('Error Type')
        ax1.set_ylabel('Average Error Count')
        ax1.set_title('Error Type Distribution')
        ax1.set_xticks(x)
        ax1.set_xticklabels(['Boundary\n(Missing+Extra)', 'Linking\n(Wrong Clusters)', 'Both\n(Boundary+Linking)'])
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Scatter plot of gold vs SOTA errors
        ax2 = axes[0, 1]
        total_gold_errors = np.sum(gold_scores, axis=1)
        total_sota_errors = np.sum(sota_scores, axis=1)
        
        ax2.scatter(total_gold_errors, total_sota_errors, alpha=0.6)
        ax2.plot([0, max(total_gold_errors.max(), total_sota_errors.max())], 
                [0, max(total_gold_errors.max(), total_sota_errors.max())], 'r--', alpha=0.8)
        
        ax2.set_xlabel('Gold Tokenization Errors')
        ax2.set_ylabel('SOTA Tokenization Errors')
        ax2.set_title('Total Errors: Gold vs SOTA')
        ax2.grid(True, alpha=0.3)
        
        # 3. Performance improvement analysis
        ax3 = axes[1, 0]
        improvement = total_gold_errors - total_sota_errors
        ax3.hist(improvement, bins=20, alpha=0.7, edgecolor='black')
        ax3.axvline(0, color='red', linestyle='--', alpha=0.8)
        ax3.set_xlabel('Error Reduction (Gold - SOTA)')
        ax3.set_ylabel('Number of Documents')
        ax3.set_title('SOTA Performance Improvement')
        ax3.grid(True, alpha=0.3)
        
        # 4. Error type breakdown
        ax4 = axes[1, 1]
        error_types = ['Boundary\n(Missing+Extra)', 'Linking\n(Wrong Clusters)', 'Both\n(Boundary+Linking)']
        gold_totals = np.sum(gold_scores, axis=0)
        sota_totals = np.sum(sota_scores, axis=0)
        
        x = np.arange(len(error_types))
        ax4.bar(x - width/2, gold_totals, width, label='Gold Tokenization')
        ax4.bar(x + width/2, sota_totals, width, label='SOTA Tokenization')
        
        ax4.set_xlabel('Error Type')
        ax4.set_ylabel('Total Error Count')
        ax4.set_title('Total Errors by Type')
        ax4.set_xticks(x)
        ax4.set_xticklabels(error_types)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save visualization
        output_path = Path(output_dir) / "neural_gold_vs_sota_comparison.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info(f"Visualization saved to {output_path}")
    
    def calculate_document_errors(self, doc_key: str, predictions: Dict) -> List[int]:
        """Calculate error metrics for a document."""
        neural_key = self.reverse_mapping.get(doc_key)
        if not neural_key:
            return [0, 0, 0]
        
        gold_clusters = self.gold_standard[doc_key]['clusters']
        pred_clusters = predictions.get('clusters', [])
        
        # Flatten all spans for analysis
        gold_spans = set()
        pred_spans = set()
        
        for cluster in gold_clusters:
            for span in cluster:
                if isinstance(span, list) and len(span) == 2:
                    gold_spans.add(tuple(span))
        
        for cluster in pred_clusters:
            for span in cluster:
                if isinstance(span, list) and len(span) == 2:
                    pred_spans.add(tuple(span))
        
        # Calculate different types of errors
        missing_spans = gold_spans - pred_spans
        extra_spans = pred_spans - gold_spans
        correct_spans = gold_spans & pred_spans
        
        # Boundary errors: spans that are completely wrong (missing + extra)
        boundary_errors = len(missing_spans) + len(extra_spans)
        
        # Linking errors: spans that exist but are in wrong clusters
        # This is a simplified approximation - we'll count spans that exist in both
        # but may be in different cluster configurations
        linking_errors = 0
        if len(gold_clusters) > 0 and len(pred_clusters) > 0:
            # Count spans that exist in both but cluster structure differs
            if len(correct_spans) > 0:
                # If we have correct spans but different cluster counts, it's a linking issue
                if len(gold_clusters) != len(pred_clusters):
                    linking_errors = min(len(correct_spans), abs(len(gold_clusters) - len(pred_clusters)))
                else:
                    # Even with same cluster count, structure might differ
                    linking_errors = len(correct_spans) // 2  # Simplified approximation
        
        # Both errors: cases where both boundary and linking are wrong
        # This happens when we have many missing/extra spans AND wrong cluster structure
        both_errors = 0
        if boundary_errors > 0 and linking_errors > 0:
            both_errors = min(boundary_errors, linking_errors) // 2  # Simplified
        
        return [boundary_errors, linking_errors, both_errors]
    
    def run_analysis(self):
        """Run the complete analysis."""
        logger.info("Starting neural model comparison analysis...")
        
        # Find documents with errors
        error_docs = self.find_documents_with_errors()
        logger.info(f"Found {len(error_docs)} documents with errors for analysis")
        
        # Analyze each document in detail
        for doc_key in error_docs:
            analysis = self.analyze_document_mistakes(doc_key)
            if analysis:
                self.print_human_readable_analysis(analysis)
        
        return error_docs

def main():
    parser = argparse.ArgumentParser(description='Neural Model Comparison Analysis')
    parser.add_argument('--neural_gold', required=True, help='Path to neural model results with gold tokenization')
    parser.add_argument('--neural_sota', required=True, help='Path to neural model results with SOTA tokenization')
    parser.add_argument('--gold_conllu', required=True, help='Path to gold standard CoNLL-U directory')
    parser.add_argument('--document_mapping', required=True, help='Path to document mapping JSON file')
    parser.add_argument('--output_dir', default='outputs/neural_comparison', help='Output directory for results')
    
    args = parser.parse_args()
    
    # Create output directory
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize analyzer
    analyzer = NeuralComparisonAnalyzer()
    
    try:
        # Load data
        analyzer.load_document_mapping(args.document_mapping)
        analyzer.load_neural_results(args.neural_gold, args.neural_sota)
        analyzer.load_gold_standard(args.gold_conllu)
        
        # Run analysis
        error_docs = analyzer.run_analysis()
        
        # Generate visualizations
        analyzer.generate_comparison_visualizations(args.output_dir)
        
        logger.info(f"Analysis completed successfully! Results saved to {args.output_dir}")
        logger.info(f"Analyzed {len(error_docs)} documents with errors")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == "__main__":
    main() 
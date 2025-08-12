#!/usr/bin/env python3
"""
Multi-System Output Comparison Script

This script compares the results from five different approaches:
1. Raw tokenization (llm_raw_*.jsonl)
2. Gold tokenization (llm_gold_tok_*.jsonl) 
3. SOTA tokenization (llm_sota_tok_*.jsonl)
4. Neural SOTA tokenized (neural/sota_tokenized/sota_tokenized_test_output.json)
5. Neural Gold tokenized (neural/gold/test_output.json)

Each approach is compared against its corresponding gold CONLLU file.
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Add the scripts directory to path to import compare_neural
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from compare_neural import load_llm_data, load_conllu_data

class MultiSystemComparisonRunner:
    def __init__(self, base_path: str = None):
        """Initialize the comparison runner."""
        self.base_path = Path(base_path) if base_path else Path.cwd()
        
        # Create output directory with timestamp and approach info
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = self.base_path / "multi_system_comparison_results" / f"comparison_{timestamp}"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Store the approaches used for this run
        self.current_approaches = []
        
        # Define all available approaches
        self.all_approaches = {
            # LLM approaches
            "raw": {"type": "llm", "path": "error_analysis_data/llm/raw", "description": "LLM Raw Tokenization"},
            "gold_tokenized": {"type": "llm", "path": "error_analysis_data/llm/gold_tokenized", "description": "LLM Gold Tokenization"},
            "sota_tokenized": {"type": "llm", "path": "error_analysis_data/llm/sota_tokenized", "description": "LLM SOTA Tokenization"},
            
            # Neural approaches
            "neural_sota": {"type": "neural", "path": "error_analysis_data/neural/sota_tokenized", "description": "Neural SOTA Tokenization"},
            "neural_gold": {"type": "neural", "path": "error_analysis_data/neural/gold", "description": "Neural Gold Tokenization"}
        }
        
        # Available documents (based on gold files)
        self.available_docs = self._get_available_documents()
        
    def _get_available_documents(self) -> List[str]:
        """Get list of available document keys from all approaches."""
        all_doc_keys = set()
        
        print(f"🔍 Searching for documents in base path: {self.base_path}")
        
        for approach_name, approach_info in self.all_approaches.items():
            if approach_info["type"] == "llm":
                pred_file = self.base_path / approach_info["path"] / "doc_predictions.jsonl"
            else:  # neural
                pred_file = self.base_path / approach_info["path"] / f"{approach_info['path'].split('/')[-1]}_test_output.json"
            
            print(f"🔍 Looking for {approach_name}: {pred_file}")
            
            if pred_file.exists():
                print(f"✅ Found {approach_name}: {pred_file}")
                # Load and extract document keys
                try:
                    with open(pred_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            data = json.loads(line.strip())
                            doc_key = data.get('doc_key', '')
                            if doc_key:
                                # Convert LLM format (e.g., "240.txt") to CONLLU format (e.g., "htb:240")
                                if doc_key.endswith('.txt'):
                                    doc_key = f"htb:{doc_key[:-4]}"
                                all_doc_keys.add(doc_key)
                except Exception as e:
                    print(f"⚠️  Error reading {pred_file}: {e}")
            else:
                print(f"❌ Not found: {pred_file}")
        
        return sorted(list(all_doc_keys))
    
    def _get_prediction_file_path(self, approach: str) -> Optional[Path]:
        """Get the prediction file path for a given approach."""
        approach_info = self.all_approaches.get(approach)
        if not approach_info:
            return None
            
        if approach_info["type"] == "llm":
            pred_file = self.base_path / approach_info["path"] / "doc_predictions.jsonl"
        else:  # neural
            if approach == "neural_sota":
                pred_file = self.base_path / approach_info["path"] / "sota_tokenized_test_output.json"
            else:  # neural_gold
                pred_file = self.base_path / approach_info["path"] / "test_output.json"
        
        if pred_file.exists():
            return pred_file
        else:
            print(f"⚠️  Prediction file not found: {pred_file}")
            return None
    
    def _get_gold_file_path(self, approach: str, doc_key: str) -> Path:
        """Get the appropriate gold file path for the given approach and document."""
        if approach.startswith("neural"):
            # Neural approaches use JSONLines files
            if approach == "neural_sota":
                return self.base_path / "error_analysis_data/gold/gold_neural/new_sota.test.hebrew.jsonlines"
            else:  # neural_gold
                return self.base_path / "error_analysis_data/gold/gold_neural/test.hebrew.jsonlines"
        else:
            # LLM approaches use CONLLU files
            return self.base_path / "error_analysis_data/gold/gold_llm" / f"{doc_key}.conllu"
    
    def run_single_comparison(self, approach: str, doc_key: str, 
                             show_full_doc: bool = False, 
                             show_diff: bool = False,
                             show_correct_mistaken: bool = False) -> Dict:
        """Run comparison for a single approach against a single document."""
        pred_file = self._get_prediction_file_path(approach)
        gold_file = self._get_gold_file_path(approach, doc_key)
        
        if not pred_file:
            return {"error": f"Prediction file not found for {approach} and {doc_key}"}
        
        if not gold_file.exists():
            return {"error": f"Gold file not found: {gold_file}"}
        
        # Get approach info for document key mapping
        approach_info = self.all_approaches.get(approach)
        if not approach_info:
            return {"error": f"Unknown approach: {approach}"}
        
        # Convert doc_key to the format expected by the prediction files
        # Handle both formats: "htb:240" -> "240.txt" for LLM, or "htb:240" for neural
        if doc_key.startswith("htb:"):
            if approach_info["type"] == "neural" or approach == "sota_tokenized":
                # Neural approaches and sota_tokenized use "htb:240" format directly
                pred_doc_key = doc_key
            else:
                # Other LLM approaches use "240.txt" format
                pred_doc_key = f"{doc_key.split(':')[1]}.txt"
        else:
            pred_doc_key = f"{doc_key}.txt"
        
        # Construct the command to run compare_neural.py
        cmd = [
            "python", str(self.base_path / "scripts" / "compare_neural.py"),
            "--neural", str(pred_file.relative_to(self.base_path.parent)),  # Relative to project root
            "--doc", pred_doc_key
        ]
        
        # Only add --gold argument if the approach doesn't have built-in gold data
        # LLM approaches with built-in gold: sota_tokenized
        # LLM approaches without built-in gold: raw, gold_tokenized
        # Neural approaches always need external gold
        if approach_info["type"] == "llm" and approach == "sota_tokenized":
            # sota_tokenized has built-in gold, don't add --gold argument
            pass
        else:
            # Add external gold file
            cmd.extend(["--gold", str(gold_file.relative_to(self.base_path.parent))])
        
        # Add --correct-mistaken flag to ensure metrics are displayed
        cmd.append("--correct-mistaken")
        
        if show_full_doc:
            cmd.append("--full-doc")
        if show_diff:
            cmd.append("--show-diff")
        if show_correct_mistaken:
            cmd.append("--correct-mistaken")
        
        # Run the comparison
        try:
            # Run from the project root directory so relative paths work correctly
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.base_path.parent,  # Run from project root
                timeout=60
            )
            
            if result.returncode == 0:
                # Parse the output to extract cluster analysis
                cluster_analysis = self._extract_cluster_analysis(result.stdout)
                return {
                    "success": True,
                    "approach": approach,
                    "doc_key": doc_key,
                    "cluster_analysis": cluster_analysis,
                    "output": result.stdout
                }
            else:
                return {
                    "error": f"Command failed with return code {result.returncode}",
                    "stderr": result.stderr,
                    "stdout": result.stdout
                }
                
        except Exception as e:
            return {"error": f"Exception occurred: {str(e)}"}
    
    def _extract_metrics_from_output(self, output: str) -> Dict:
        """Extract precision, recall, F1 from the comparison output."""
        metrics = {}
        
        # Look for metrics in the output
        lines = output.split('\n')
        for line in lines:
            if 'Precision:' in line and 'Recall:' in line and 'F1:' in line:
                # Extract metrics from line like "Precision: 0.571 Recall: 0.308 F1: 0.400"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part == 'Precision:':
                        metrics['precision'] = float(parts[i + 1])
                    elif part == 'Recall:':
                        metrics['recall'] = float(parts[i + 1])
                    elif part == 'F1:':
                        metrics['f1'] = float(parts[i + 1])
                break
        
        # If no explicit metrics found, calculate from cluster analysis
        if not metrics:
            correct_clusters = 0
            extra_clusters = 0
            missed_clusters = 0
            
            for line in lines:
                if '✅ Correct clusters:' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'clusters:':
                            correct_clusters = int(parts[i + 1])
                            break
                elif '❌ Extra clusters:' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'clusters:':
                            extra_clusters = int(parts[i + 1])
                            break
                elif '🔍 Missed clusters:' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'clusters:':
                            missed_clusters = int(parts[i + 1])
                            break
            
            # Calculate metrics
            if correct_clusters + extra_clusters > 0:
                precision = correct_clusters / (correct_clusters + extra_clusters)
                metrics['precision'] = precision
            
            if correct_clusters + missed_clusters > 0:
                recall = correct_clusters / (correct_clusters + missed_clusters)
                metrics['recall'] = recall
            
            if 'precision' in metrics and 'recall' in metrics:
                if metrics['precision'] + metrics['recall'] > 0:
                    f1 = 2 * (metrics['precision'] * metrics['recall']) / (metrics['precision'] + metrics['recall'])
                    metrics['f1'] = f1
        
        return metrics
    
    def _extract_cluster_analysis(self, output: str) -> Dict:
        """Extract cluster-level analysis from the comparison output."""
        analysis = {}
        
        # Look for cluster summary in the output
        lines = output.split('\n')
        for i, line in enumerate(lines):
            if 'Summary:' in line:
                # Look at the next few lines for cluster counts
                for j in range(i+1, min(i+5, len(lines))):
                    next_line = lines[j]
                    
                    if '✅ Correct clusters:' in next_line:
                        try:
                            # Extract the number after "Correct clusters:"
                            parts = next_line.split('✅ Correct clusters:')
                            if len(parts) > 1:
                                correct_part = parts[1].split('❌')[0].strip()
                                analysis['correct_clusters'] = int(correct_part)
                        except Exception as e:
                            pass
                    
                    elif '❌ Extra clusters:' in next_line:
                        try:
                            # Extract the number after "Extra clusters:"
                            parts = next_line.split('❌ Extra clusters:')
                            if len(parts) > 1:
                                extra_part = parts[1].split('🔍')[0].strip()
                                analysis['extra_clusters'] = int(extra_part)
                        except Exception as e:
                            pass
                    
                    elif '🔍 Missed clusters:' in next_line:
                        try:
                            # Extract the number after "Missed clusters:"
                            parts = next_line.split('🔍 Missed clusters:')
                            if len(parts) > 1:
                                missed_part = parts[1].strip()
                                analysis['missed_clusters'] = int(missed_part)
                        except Exception as e:
                            pass
                
                break  # Found summary, no need to look further
        
        # Look for non-pronoun mention analysis
        non_pronoun_mentions = 0
        total_mentions = 0
        for line in lines:
            if '→' in line and not any(pronoun in line for pronoun in ['הוא', 'היא', 'הם', 'הן', 'אני', 'אנחנו', 'אתה', 'אתם', 'את', 'אתן']):
                # This line contains non-pronoun mentions
                non_pronoun_mentions += 1
            if '→' in line:
                total_mentions += 1
        
        if total_mentions > 0:
            analysis['non_pronoun_ratio'] = non_pronoun_mentions / total_mentions
            analysis['total_mentions'] = total_mentions
            analysis['non_pronoun_mentions'] = non_pronoun_mentions
        
        return analysis
    
    def create_visualizations(self, results: Dict) -> None:
        """Create comprehensive visualizations comparing all approaches."""
        # Convert results to DataFrame for easier plotting
        data = []
        for doc_key, doc_results in results.items():
            for approach, result in doc_results.items():
                if result.get("success") and result.get("cluster_analysis"):
                    analysis = result["cluster_analysis"]
                    data.append({
                        'Document': doc_key,
                        'Approach': approach,
                        'Correct_Clusters': analysis.get('correct_clusters', 0),
                        'Extra_Clusters': analysis.get('extra_clusters', 0),
                        'Missed_Clusters': analysis.get('missed_clusters', 0),
                        'Non_Pronoun_Ratio': analysis.get('non_pronoun_ratio', 0),
                        'Total_Mentions': analysis.get('total_mentions', 0),
                        'Non_Pronoun_Mentions': analysis.get('non_pronoun_mentions', 0)
                    })
        
        if not data:
            print("⚠️  No data available for visualization")
            return
        
        df = pd.DataFrame(data)
        
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # Color scheme for 5 approaches - ensure unique colors
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
        
        # Create separate visualizations
        
        # 1. Correct Clusters Comparison
        self._create_correct_clusters_plot(df, colors)
        
        # 2. Extra Clusters Comparison
        self._create_extra_clusters_plot(df, colors)
        
        # 3. Missed Clusters Comparison
        self._create_missed_clusters_plot(df, colors)
        
        # 4. Non-Pronoun Ratio Comparison
        self._create_non_pronoun_ratio_plot(df, colors)
        
        # 5. Performance Heatmap
        self._create_performance_heatmap(df)
        
        # 6. Total Mentions Comparison
        self._create_mentions_comparison_plot(df, colors)
        
        # 7. Comprehensive overview (original combined plot)
        self._create_comprehensive_overview(df, colors)
        
        print(f"📊 All visualizations saved to: {self.output_dir}")
        
        # Create additional detailed plots
        self._create_detailed_plots(df, colors)
    
    def _create_correct_clusters_plot(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create separate plot for correct clusters comparison."""
        plt.figure(figsize=(12, 8))
        
        correct_data = df.groupby('Approach')['Correct_Clusters'].mean().reset_index()
        bars = plt.bar(correct_data['Approach'], correct_data['Correct_Clusters'], 
                      color=colors[:len(correct_data)], alpha=0.8)
        
        plt.title('Average Correct Clusters by Approach', fontsize=16, fontweight='bold')
        plt.ylabel('Correct Clusters', fontsize=12)
        plt.xlabel('Approach', fontsize=12)
        plt.xticks(rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Adjust scale if values are very similar
        values = correct_data['Correct_Clusters'].tolist()
        self._adjust_y_scale_for_similar_values(plt.gca(), values, min_difference_threshold=0.15)
        
        plt.tight_layout()
        plot_file = self.output_dir / "01_correct_clusters_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Correct clusters plot: {plot_file}")
    
    def _create_extra_clusters_plot(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create separate plot for extra clusters comparison."""
        plt.figure(figsize=(12, 8))
        
        extra_data = df.groupby('Approach')['Extra_Clusters'].mean().reset_index()
        bars = plt.bar(extra_data['Approach'], extra_data['Extra_Clusters'], 
                      color=colors[:len(extra_data)], alpha=0.8)
        
        plt.title('Average Extra Clusters by Approach', fontsize=16, fontweight='bold')
        plt.ylabel('Extra Clusters', fontsize=12)
        plt.xlabel('Approach', fontsize=12)
        plt.xticks(rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Adjust scale if values are very similar
        values = extra_data['Extra_Clusters'].tolist()
        self._adjust_y_scale_for_similar_values(plt.gca(), values, min_difference_threshold=0.15)
        
        plt.tight_layout()
        plot_file = self.output_dir / "02_extra_clusters_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Extra clusters plot: {plot_file}")
    
    def _create_missed_clusters_plot(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create separate plot for missed clusters comparison."""
        plt.figure(figsize=(12, 8))
        
        missed_data = df.groupby('Approach')['Missed_Clusters'].mean().reset_index()
        bars = plt.bar(missed_data['Approach'], missed_data['Missed_Clusters'], 
                      color=colors[:len(missed_data)], alpha=0.8)
        
        plt.title('Average Missed Clusters by Approach', fontsize=16, fontweight='bold')
        plt.ylabel('Missed Clusters', fontsize=12)
        plt.xlabel('Approach', fontsize=12)
        plt.xticks(rotation=45)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{height:.1f}', ha='center', va='bottom', fontweight='bold')
        
        # Adjust scale if values are very similar
        values = missed_data['Missed_Clusters'].tolist()
        self._adjust_y_scale_for_similar_values(plt.gca(), values, min_difference_threshold=0.15)
        
        plt.tight_layout()
        plot_file = self.output_dir / "03_missed_clusters_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Missed clusters plot: {plot_file}")
    
    def _create_non_pronoun_ratio_plot(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create separate plot for non-pronoun ratio comparison."""
        plt.figure(figsize=(12, 8))
        
        # Use unique colors for each approach
        unique_approaches = df['Approach'].unique()
        approach_colors = {approach: colors[i % len(colors)] for i, approach in enumerate(unique_approaches)}
        
        sns.boxplot(data=df, x='Approach', y='Non_Pronoun_Ratio', 
                   palette=[approach_colors[app] for app in unique_approaches])
        
        plt.title('Non-Pronoun Ratio Distribution by Approach', fontsize=16, fontweight='bold')
        plt.ylabel('Non-Pronoun Ratio', fontsize=12)
        plt.xlabel('Approach', fontsize=12)
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        plot_file = self.output_dir / "04_non_pronoun_ratio_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Non-pronoun ratio plot: {plot_file}")
    
    def _create_performance_heatmap(self, df: pd.DataFrame) -> None:
        """Create separate performance heatmap."""
        plt.figure(figsize=(10, 8))
        
        performance_data = df.groupby('Approach').agg({
            'Correct_Clusters': 'mean',
            'Extra_Clusters': 'mean',
            'Missed_Clusters': 'mean',
            'Non_Pronoun_Ratio': 'mean'
        })
        
        sns.heatmap(performance_data.T, annot=True, cmap='RdYlGn', center=0, 
                    cbar_kws={'label': 'Average Value'})
        plt.title('Performance Metrics Heatmap', fontsize=16, fontweight='bold')
        
        plt.tight_layout()
        plot_file = self.output_dir / "05_performance_heatmap.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Performance heatmap: {plot_file}")
    
    def _create_mentions_comparison_plot(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create separate plot for mentions comparison."""
        plt.figure(figsize=(12, 8))
        
        mention_data = df.groupby('Approach').agg({
            'Total_Mentions': 'sum',
            'Non_Pronoun_Mentions': 'sum'
        }).reset_index()
        
        x = np.arange(len(mention_data))
        width = 0.35
        
        bars1 = plt.bar(x - width/2, mention_data['Total_Mentions'], width, 
                        label='Total Mentions', color=colors[0], alpha=0.8)
        bars2 = plt.bar(x + width/2, mention_data['Non_Pronoun_Mentions'], width, 
                        label='Non-Pronoun Mentions', color=colors[1], alpha=0.8)
        
        plt.title('Total vs Non-Pronoun Mentions by Approach', fontsize=16, fontweight='bold')
        plt.ylabel('Number of Mentions', fontsize=12)
        plt.xlabel('Approach', fontsize=12)
        plt.xticks(x, mention_data['Approach'], rotation=45)
        plt.legend()
        
        # Adjust scale if values are very similar
        total_values = mention_data['Total_Mentions'].tolist()
        non_pronoun_values = mention_data['Non_Pronoun_Mentions'].tolist()
        all_values = total_values + non_pronoun_values
        self._adjust_y_scale_for_similar_values(plt.gca(), all_values, min_difference_threshold=0.15)
        
        plt.tight_layout()
        plot_file = self.output_dir / "06_mentions_comparison.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Mentions comparison plot: {plot_file}")
    
    def _create_comprehensive_overview(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create the original comprehensive overview plot."""
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Multi-System Performance Comparison - Overview', fontsize=20, fontweight='bold')
        
        # 1. Correct Clusters Comparison
        ax1 = axes[0, 0]
        correct_data = df.groupby('Approach')['Correct_Clusters'].mean().reset_index()
        bars1 = ax1.bar(correct_data['Approach'], correct_data['Correct_Clusters'], 
                        color=colors[:len(correct_data)], alpha=0.8)
        ax1.set_title('Average Correct Clusters by Approach', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Correct Clusters')
        ax1.set_xlabel('Approach')
        ax1.tick_params(axis='x', rotation=45)
        
        # Adjust scale if values are very similar
        correct_values = correct_data['Correct_Clusters'].tolist()
        self._adjust_y_scale_for_similar_values(ax1, correct_values, min_difference_threshold=0.15)
        
        # 2. Extra Clusters Comparison
        ax2 = axes[0, 1]
        extra_data = df.groupby('Approach')['Extra_Clusters'].mean().reset_index()
        bars2 = ax2.bar(extra_data['Approach'], extra_data['Extra_Clusters'], 
                        color=colors[:len(extra_data)], alpha=0.8)
        ax2.set_title('Average Extra Clusters by Approach', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Extra Clusters')
        ax2.set_xlabel('Approach')
        ax2.tick_params(axis='x', rotation=45)
        
        # Adjust scale if values are very similar
        extra_values = extra_data['Extra_Clusters'].tolist()
        self._adjust_y_scale_for_similar_values(ax2, extra_values, min_difference_threshold=0.15)
        
        # 3. Missed Clusters Comparison
        ax3 = axes[0, 2]
        missed_data = df.groupby('Approach')['Missed_Clusters'].mean().reset_index()
        bars3 = ax3.bar(missed_data['Approach'], missed_data['Missed_Clusters'], 
                        color=colors[:len(missed_data)], alpha=0.8)
        ax3.set_title('Average Missed Clusters by Approach', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Missed Clusters')
        ax3.set_xlabel('Approach')
        ax3.tick_params(axis='x', rotation=45)
        
        # Adjust scale if values are very similar
        missed_values = missed_data['Missed_Clusters'].tolist()
        self._adjust_y_scale_for_similar_values(ax3, missed_values, min_difference_threshold=0.15)
        
        # 4. Non-Pronoun Ratio Comparison
        ax4 = axes[1, 0]
        unique_approaches = df['Approach'].unique()
        approach_colors = {approach: colors[i % len(colors)] for i, approach in enumerate(unique_approaches)}
        sns.boxplot(data=df, x='Approach', y='Non_Pronoun_Ratio', ax=ax4, 
                   palette=[approach_colors[app] for app in unique_approaches])
        ax4.set_title('Non-Pronoun Ratio Distribution by Approach', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Non-Pronoun Ratio')
        ax4.set_xlabel('Approach')
        ax4.tick_params(axis='x', rotation=45)
        
        # 5. Performance Heatmap
        ax5 = axes[1, 1]
        performance_data = df.groupby('Approach').agg({
            'Correct_Clusters': 'mean',
            'Extra_Clusters': 'mean',
            'Missed_Clusters': 'mean',
            'Non_Pronoun_Ratio': 'mean'
        })
        sns.heatmap(performance_data.T, annot=True, cmap='RdYlGn', center=0, 
                    ax=ax5, cbar_kws={'label': 'Average Value'})
        ax5.set_title('Performance Metrics Heatmap', fontsize=14, fontweight='bold')
        
        # 6. Total Mentions Comparison
        ax6 = axes[1, 2]
        mention_data = df.groupby('Approach').agg({
            'Total_Mentions': 'sum',
            'Non_Pronoun_Mentions': 'sum'
        }).reset_index()
        
        x = np.arange(len(mention_data))
        width = 0.35
        
        bars6a = ax6.bar(x - width/2, mention_data['Total_Mentions'], width, 
                          label='Total Mentions', color=colors[0], alpha=0.8)
        bars6b = ax6.bar(x + width/2, mention_data['Non_Pronoun_Mentions'], width, 
                          label='Non-Pronoun Mentions', color=colors[1], alpha=0.8)
        
        ax6.set_title('Total vs Non-Pronoun Mentions by Approach', fontsize=14, fontweight='bold')
        ax6.set_ylabel('Number of Mentions')
        ax6.set_xlabel('Approach')
        ax6.set_xticks(x)
        ax6.set_xticklabels(mention_data['Approach'], rotation=45)
        ax6.legend()
        
        plt.tight_layout()
        plot_file = self.output_dir / "00_comprehensive_overview.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Comprehensive overview: {plot_file}")
    
    def _create_detailed_plots(self, df: pd.DataFrame, colors: List[str]) -> None:
        """Create additional detailed visualizations."""
        # Set style
        plt.style.use('seaborn-v0_8')
        
        # Create figure for detailed analysis
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Detailed Multi-System Performance Analysis', fontsize=20, fontweight='bold')
        
        # 1. Cluster Performance by Document
        ax1 = axes[0, 0]
        pivot_data = df.pivot(index='Document', columns='Approach', values='Correct_Clusters')
        
        # Use unique colors for each approach
        unique_approaches = pivot_data.columns
        approach_colors = {approach: colors[i % len(colors)] for i, approach in enumerate(unique_approaches)}
        
        pivot_data.plot(kind='bar', ax=ax1, color=[approach_colors[app] for app in unique_approaches])
        ax1.set_title('Correct Clusters by Document and Approach', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Correct Clusters')
        ax1.set_xlabel('Document')
        ax1.legend(title='Approach')
        ax1.tick_params(axis='x', rotation=45)
        
        # Adjust scale if values are very similar for each approach
        for approach in unique_approaches:
            values = pivot_data[approach].dropna().tolist()
            if values:
                self._adjust_y_scale_for_similar_values(ax1, values, min_difference_threshold=0.15)
        
        # 2. Non-Pronoun Ratio by Approach
        ax2 = axes[0, 1]
        sns.boxplot(data=df, x='Approach', y='Non_Pronoun_Ratio', ax=ax2, 
                   palette=[approach_colors[app] for app in unique_approaches])
        ax2.set_title('Non-Pronoun Ratio Distribution by Approach', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Non-Pronoun Ratio')
        ax2.set_xlabel('Approach')
        ax2.tick_params(axis='x', rotation=45)
        
        # 3. Total Performance Score
        ax3 = axes[1, 0]
        # Calculate a simple performance score: (correct - extra) / (correct + missed)
        df['Performance_Score'] = (df['Correct_Clusters'] - df['Extra_Clusters']) / (df['Correct_Clusters'] + df['Missed_Clusters'] + 1e-6)
        performance_data = df.groupby('Approach')['Performance_Score'].mean().reset_index()
        
        bars = ax3.bar(performance_data['Approach'], performance_data['Performance_Score'], 
                       color=[approach_colors[app] for app in performance_data['Approach']], alpha=0.8)
        ax3.set_title('Average Performance Score by Approach', fontsize=14, fontweight='bold')
        ax3.set_ylabel('Performance Score')
        ax3.set_xlabel('Approach')
        ax3.tick_params(axis='x', rotation=45)
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # Adjust scale if values are very similar
        performance_values = performance_data['Performance_Score'].tolist()
        self._adjust_y_scale_for_similar_values(ax3, performance_values, min_difference_threshold=0.15)
        
        # 4. Mention Type Comparison - Create separate pie charts for each approach
        ax4 = axes[1, 1]
        mention_data = df.groupby('Approach').agg({
            'Non_Pronoun_Mentions': 'sum',
            'Total_Mentions': 'sum'
        })
        
        # Calculate pronoun mentions
        mention_data['Pronoun_Mentions'] = mention_data['Total_Mentions'] - mention_data['Non_Pronoun_Mentions']
        
        # Create a combined bar chart instead of pie charts to avoid color repetition
        x = np.arange(len(mention_data))
        width = 0.35
        
        bars4a = ax4.bar(x - width/2, mention_data['Pronoun_Mentions'], width, 
                          label='Pronoun Mentions', color=colors[0], alpha=0.8)
        bars4b = ax4.bar(x + width/2, mention_data['Non_Pronoun_Mentions'], width, 
                          label='Non-Pronoun Mentions', color=colors[1], alpha=0.8)
        
        ax4.set_title('Mention Type Distribution by Approach', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Number of Mentions')
        ax4.set_xlabel('Approach')
        ax4.set_xticks(x)
        ax4.set_xticklabels(mention_data.index, rotation=45)
        ax4.legend()
        
        # Adjust scale if values are very similar
        all_mention_values = mention_data['Pronoun_Mentions'].tolist() + mention_data['Non_Pronoun_Mentions'].tolist()
        self._adjust_y_scale_for_similar_values(ax4, all_mention_values, min_difference_threshold=0.15)
        
        # Adjust layout and save
        plt.tight_layout()
        
        # Save the detailed plot
        detailed_plot_file = self.output_dir / "07_detailed_analysis.png"
        plt.savefig(detailed_plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Detailed analysis plots: {detailed_plot_file}")
        
        # Create additional separate pie charts for each approach
        self._create_individual_pie_charts(mention_data, colors)
    
    def _create_individual_pie_charts(self, mention_data: pd.DataFrame, colors: List[str]) -> None:
        """Create individual pie charts for each approach to show mention distribution."""
        n_approaches = len(mention_data)
        n_cols = min(3, n_approaches)  # Max 3 columns
        n_rows = (n_approaches + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
        
        # Handle different subplot configurations
        if n_rows == 1 and n_cols == 1:
            axes = np.array([[axes]])
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        fig.suptitle('Mention Type Distribution by Approach (Individual Charts)', fontsize=16, fontweight='bold')
        
        for i, (approach, data) in enumerate(mention_data.iterrows()):
            row = i // n_cols
            col = i % n_cols
            
            # Get the correct axis
            if n_rows == 1 and n_cols == 1:
                ax = axes[0, 0]
            else:
                ax = axes[row, col]
            
            # Use unique colors for each approach
            approach_color = colors[i % len(colors)]
            other_color = colors[(i + 1) % len(colors)]
            
            labels = ['Pronoun Mentions', 'Non-Pronoun Mentions']
            sizes = [data['Pronoun_Mentions'], data['Non_Pronoun_Mentions']]
            colors_pie = [approach_color, other_color]
            
            if sum(sizes) > 0:  # Only plot if there are mentions
                ax.pie(sizes, labels=labels, colors=colors_pie, autopct='%1.1f%%', startangle=90)
                ax.set_title(f'{approach}', fontweight='bold')
            else:
                ax.text(0.5, 0.5, 'No mentions', ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f'{approach}', fontweight='bold')
        
        # Hide empty subplots
        for i in range(n_approaches, n_rows * n_cols):
            row = i // n_cols
            col = i % n_cols
            if n_rows == 1 and n_cols == 1:
                pass  # No need to hide for single subplot
            else:
                axes[row, col].set_visible(False)
        
        plt.tight_layout()
        pie_charts_file = self.output_dir / "08_individual_pie_charts.png"
        plt.savefig(pie_charts_file, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"📊 Individual pie charts: {pie_charts_file}")
    
    def _adjust_y_scale_for_similar_values(self, ax, values, min_difference_threshold=0.1):
        """
        Adjust y-axis scale when values are very similar to make differences clearly visible.
        This is especially important for scientific papers where small differences matter.
        
        Args:
            ax: matplotlib axis object
            values: list of numeric values
            min_difference_threshold: minimum difference to trigger scale adjustment
        """
        if not values or len(values) < 2:
            return
            
        min_val = min(values)
        max_val = max(values)
        current_range = max_val - min_val
        
        # If the range is very small relative to the values, adjust the scale
        if current_range > 0 and (current_range / max_val) < min_difference_threshold:
            # Calculate a new range that makes differences visible
            # Use 20% of the max value as the new range, centered on the data
            new_range = max_val * 0.2
            center = (min_val + max_val) / 2
            
            new_min = max(0, center - new_range / 2)  # Don't go below 0 for counts/ratios
            new_max = center + new_range / 2
            
            # Set the new y-axis limits
            ax.set_ylim(new_min, new_max)
            
            # Add a note about the adjusted scale
            ax.text(0.02, 0.98, f'Scale adjusted for clarity\n(Range: {current_range:.3f})', 
                   transform=ax.transAxes, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.8),
                   fontsize=8)
    
    def run_all_comparisons(self, show_full_doc: bool = False,
                           show_diff: bool = False,
                           show_correct_mistaken: bool = False,
                           selected_approaches: Optional[List[str]] = None) -> Dict:
        """Run comparisons for all approaches against all documents."""
        print("🔍 Running comparisons for all approaches...")
        print(f"📁 Available documents: {', '.join(self.available_docs)}")
        
        # Filter approaches if specified
        approaches_to_run = selected_approaches if selected_approaches else list(self.all_approaches.keys())
        print(f"🔄 Approaches to run: {', '.join(approaches_to_run)}")
        print("=" * 80)
        
        # Clear any previous results to ensure fresh data
        results = {}
        
        for doc_key in self.available_docs:
            print(f"\n📄 Processing document: {doc_key}")
            results[doc_key] = {}
            
            for approach in approaches_to_run:
                print(f"  🔄 Testing {approach}...")
                
                result = self.run_single_comparison(
                    approach, doc_key, 
                    show_full_doc, show_diff, show_correct_mistaken
                )
                
                if result.get("success"):
                    print(f"    ✅ Correct: {result.get('cluster_analysis', {}).get('correct_clusters', 0)}, ❌ Extra: {result.get('cluster_analysis', {}).get('extra_clusters', 0)}, 🔍 Missed: {result.get('cluster_analysis', {}).get('missed_clusters', 0)}")
                    results[doc_key][approach] = result
                else:
                    print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                    # Don't add failed results to avoid contaminating data
        
        # Filter results to only include approaches that were actually run
        filtered_results = {}
        for doc_key, doc_results in results.items():
            filtered_results[doc_key] = {
                approach: result for approach, result in doc_results.items() 
                if approach in approaches_to_run
            }
        
        return filtered_results
    
    def generate_summary_report(self, results: Dict) -> str:
        """Generate a comprehensive summary report."""
        report = []
        report.append("=" * 80)
        report.append("MULTI-SYSTEM OUTPUT COMPARISON SUMMARY REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total documents: {len(results)}")
        report.append("")
        
        # Summary table
        report.append("📊 OVERALL PERFORMANCE SUMMARY")
        report.append("-" * 80)
        report.append(f"{'Document':<15} {'Approach':<20} {'Correct':<10} {'Extra':<10} {'Missed':<10} {'Non-Pronoun':<12}")
        report.append("-" * 80)
        
        for doc_key, doc_results in results.items():
            for approach, result in doc_results.items():
                if result.get("success") and result.get("cluster_analysis"):
                    analysis = result["cluster_analysis"]
                    report.append(f"{doc_key:<15} {approach:<20} "
                               f"{analysis.get('correct_clusters', 0):<10} "
                               f"{analysis.get('extra_clusters', 0):<10} "
                               f"{analysis.get('missed_clusters', 0):<10} "
                               f"{analysis.get('non_pronoun_ratio', 0):<12.2f}")
                else:
                    report.append(f"{doc_key:<15} {approach:<20} {'ERROR':<10} {'ERROR':<10} {'ERROR':<10} {'ERROR':<12}")
        
        report.append("-" * 80)
        report.append("")
        
        # Detailed results
        report.append("📋 DETAILED RESULTS BY DOCUMENT")
        report.append("=" * 80)
        
        for doc_key, doc_results in results.items():
            report.append(f"\n📄 Document: {doc_key}")
            report.append("-" * 40)
            
            for approach, result in doc_results.items():
                if result.get("success"):
                    analysis = result.get("cluster_analysis", {})
                    if analysis:
                        report.append(f"  🔄 {approach}:")
                        report.append(f"    Correct clusters: {analysis.get('correct_clusters', 0)}")
                        report.append(f"    Extra clusters: {analysis.get('extra_clusters', 0)}")
                        report.append(f"    Missed clusters: {analysis.get('missed_clusters', 0)}")
                        report.append(f"    Non-pronoun ratio: {analysis.get('non_pronoun_ratio', 0):.2f}")
                        report.append(f"    Total mentions: {analysis.get('total_mentions', 0)}")
                        report.append(f"    Non-pronoun mentions: {analysis.get('non_pronoun_mentions', 0)}")
                    else:
                        report.append(f"  🔄 {approach}: No cluster analysis available")
                else:
                    report.append(f"  ❌ {approach}: {result.get('error', 'Unknown error')}")
        
        return "\n".join(report)
    
    def save_results(self, results: Dict, report: str):
        """Save results and report to files."""
        # Save detailed results as JSON
        results_file = self.output_dir / "multi_system_comparison_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Save summary report
        report_file = self.output_dir / "multi_system_comparison_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Generate CSV summary for easy analysis
        csv_data = []
        for doc_key, doc_results in results.items():
            for approach, result in doc_results.items():
                if result.get("success") and result.get("cluster_analysis"):
                    analysis = result["cluster_analysis"]
                    csv_data.append({
                        'Document': doc_key,
                        'Approach': approach,
                        'Correct_Clusters': analysis.get('correct_clusters', 0),
                        'Extra_Clusters': analysis.get('extra_clusters', 0),
                        'Missed_Clusters': analysis.get('missed_clusters', 0),
                        'Non_Pronoun_Ratio': analysis.get('non_pronoun_ratio', 0),
                        'Total_Mentions': analysis.get('total_mentions', 0),
                        'Non_Pronoun_Mentions': analysis.get('non_pronoun_mentions', 0)
                    })
                else:
                    csv_data.append({
                        'Document': doc_key,
                        'Approach': approach,
                        'Correct_Clusters': 'ERROR',
                        'Extra_Clusters': 'ERROR',
                        'Missed_Clusters': 'ERROR',
                        'Non_Pronoun_Ratio': 'ERROR',
                        'Total_Mentions': 'ERROR',
                        'Non_Pronoun_Mentions': 'ERROR'
                    })
        
        # Save CSV
        df = pd.DataFrame(csv_data)
        csv_file = self.output_dir / "multi_system_comparison_results.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8')
        
        print(f"💾 Results saved to: {self.output_dir}")
        print(f"📄 Detailed results: {results_file}")
        print(f"📋 Summary report: {report_file}")
        print(f"📊 CSV data: {csv_file}")
    
    def run_comprehensive_analysis(self, show_full_doc: bool = False,
                                  show_diff: bool = False,
                                  show_correct_mistaken: bool = False,
                                  selected_approaches: Optional[List[str]] = None):
        """Run the complete multi-system comparison analysis."""
        print("🚀 Starting Multi-System Output Comparison Analysis")
        print("=" * 80)
        
        # Run all comparisons
        results = self.run_all_comparisons(show_full_doc, show_diff, show_correct_mistaken, selected_approaches)
        
        # Generate summary report
        report = self.generate_summary_report(results)
        
        # Save results
        self.save_results(results, report)
        
        # Create visualizations
        print("\n" + "=" * 80)
        print("📊 CREATING VISUALIZATIONS...")
        print("=" * 80)
        self.create_visualizations(results)
        
        # Display summary
        print("\n" + "=" * 80)
        print("🎯 ANALYSIS COMPLETE!")
        print("=" * 80)
        print(report)
        
        return results, report

def main():
    """Main function to run the comparison analysis."""
    parser = argparse.ArgumentParser(description="Compare multiple system outputs for coreference resolution")
    parser.add_argument("--approaches", nargs="+", 
                       choices=["raw", "gold_tokenized", "sota_tokenized", "neural_sota", "neural_gold"],
                       help="Specific approaches to compare (default: all)")
    parser.add_argument("--full-doc", action="store_true", 
                       help="Show full document comparison")
    parser.add_argument("--show-diff", action="store_true", 
                       help="Show detailed differences between predictions")
    parser.add_argument("--correct-mistaken", action="store_true", 
                       help="Show correct vs mistaken predictions analysis")
    parser.add_argument("--no-viz", action="store_true", 
                       help="Skip visualization generation")
    
    args = parser.parse_args()
    
    # Get the base path (error_analysis directory where the data is located)
    base_path = Path(__file__).parent.parent  # Go up from llm_comparison to error_analysis
    
    print("🚀 Starting Multi-System Output Comparison Analysis")
    print("=" * 80)
    
    # Initialize runner with base path
    runner = MultiSystemComparisonRunner(base_path)
    
    # Store current approaches for this run
    approaches_to_run = args.approaches if args.approaches else list(runner.all_approaches.keys())
    runner.current_approaches = approaches_to_run
    
    # Create descriptive subfolder name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    approaches_str = "_".join(sorted(approaches_to_run))
    descriptive_name = f"comparison_{approaches_str}_{timestamp}"
    
    # Update output directory with descriptive name (under error_analysis directory)
    runner.output_dir = base_path / "multi_system_comparison_results" / descriptive_name
    runner.output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {runner.output_dir}")
    print(f"🔄 Approaches to run: {', '.join(approaches_to_run)}")
    print(f"🔍 Base path (error_analysis): {base_path}")
    print("=" * 80)
    
    # Comprehensive analysis
    if approaches_to_run:
        print(f"🔄 Running comprehensive analysis for selected approaches: {', '.join(approaches_to_run)}")
    else:
        print("🔄 Running comprehensive analysis for all approaches")
        
    # Run comprehensive analysis and capture results
    results, report = runner.run_comprehensive_analysis(
        args.full_doc, args.show_diff, args.correct_mistaken, approaches_to_run
    )
    
    # Create visualizations unless disabled
    if not args.no_viz:
        print("\n" + "=" * 80)
        print("📊 CREATING VISUALIZATIONS...")
        print("=" * 80)
        # Use the results that were already generated in run_comprehensive_analysis
        runner.create_visualizations(results)
    
    print("\n" + "=" * 80)
    print("🎯 ANALYSIS COMPLETE!")
    print("=" * 80)

if __name__ == "__main__":
    main() 
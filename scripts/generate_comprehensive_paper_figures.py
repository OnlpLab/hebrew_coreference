#!/usr/bin/env python3
"""
Generate comprehensive publication-quality figures for the Hebrew Coreference Resolution paper
Includes both GPT-4o-mini and Gemini 2.5 Pro results
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.patches as mpatches

# Set style for publication-quality figures
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

def load_comprehensive_error_data():
    """Load comprehensive error analysis data"""
    comparison_file = Path("outputs/error_analysis_comprehensive/error_comparison.json")
    if not comparison_file.exists():
        print("Comprehensive error comparison file not found!")
        return None
    
    with open(comparison_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_comprehensive_error_type_comparison(data, output_dir):
    """Create comprehensive error type comparison figure"""
    approaches = list(data["error_type_distribution"].keys())
    error_types = ["no_prediction", "partial_match", "over_prediction", "complete_mismatch"]
    
    # Create DataFrame for easier plotting
    df_data = []
    for approach in approaches:
        for error_type in error_types:
            count = data["error_type_distribution"][approach].get(error_type, 0)
            df_data.append({
                'Approach': approach,
                'Error Type': error_type.replace('_', ' ').title(),
                'Count': count
            })
    
    df = pd.DataFrame(df_data)
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 10))
    
    # Create grouped bar chart
    x = np.arange(len(error_types))
    width = 0.15  # Reduced width to accommodate more approaches
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
    
    for i, (approach, color) in enumerate(zip(approaches, colors)):
        counts = [df[(df['Approach'] == approach) & (df['Error Type'] == error_type.replace('_', ' ').title())]['Count'].iloc[0] 
                 if len(df[(df['Approach'] == approach) & (df['Error Type'] == error_type.replace('_', ' ').title())]) > 0 else 0
                 for error_type in error_types]
        ax.bar(x + i * width, counts, width, label=approach, color=color)
    
    ax.set_xlabel('Error Type', fontsize=14)
    ax.set_ylabel('Number of Errors', fontsize=14)
    ax.set_title('Error Type Distribution Across All Approaches', fontsize=16, fontweight='bold')
    ax.set_xticks(x + width * (len(approaches) - 1) / 2)
    ax.set_xticklabels([et.replace('_', ' ').title() for et in error_types], fontsize=12)
    ax.legend(fontsize=11, bbox_to_anchor=(1.05, 1), loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comprehensive_error_type_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_llm_comparison_figure(data, output_dir):
    """Create LLM comparison figure"""
    approaches = list(data["total_errors"].keys())
    
    # Filter for LLM approaches
    llm_approaches = [app for app in approaches if "GPT" in app or "Gemini" in app]
    total_errors = [data["total_errors"][app] for app in llm_approaches]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. Total Errors Comparison
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    bars1 = ax1.bar(llm_approaches, total_errors, color=colors[:len(llm_approaches)])
    ax1.set_title('Total Errors by LLM Approach', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add value labels on bars
    for bar, value in zip(bars1, total_errors):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, 
                str(value), ha='center', va='bottom', fontsize=10)
    
    # 2. Error Rate Comparison
    total_clusters = 454
    error_rates = [errors / total_clusters * 100 for errors in total_errors]
    
    bars2 = ax2.bar(llm_approaches, error_rates, color=colors[:len(llm_approaches)])
    ax2.set_title('Error Rate by LLM Approach', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Percentage (%)')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add percentage labels on bars
    for bar, rate in zip(bars2, error_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'llm_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_summary_figure(data, output_dir):
    """Create comprehensive performance summary figure"""
    approaches = list(data["total_errors"].keys())
    total_errors = list(data["total_errors"].values())
    
    # Calculate additional metrics
    total_clusters = 454
    error_rates = [errors / total_clusters * 100 for errors in total_errors]
    
    # Get no prediction rates
    no_prediction_rates = []
    for approach in approaches:
        no_pred = data["error_type_distribution"][approach].get("no_prediction", 0)
        no_pred_rate = no_pred / total_clusters * 100
        no_prediction_rates.append(no_pred_rate)
    
    # Create subplot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(18, 12))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
    
    # 1. Total Errors
    bars1 = ax1.bar(approaches, total_errors, color=colors[:len(approaches)])
    ax1.set_title('Total Errors', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    for bar, value in zip(bars1, total_errors):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                str(value), ha='center', va='bottom', fontsize=10)
    
    # 2. Error Rates
    bars2 = ax2.bar(approaches, error_rates, color=colors[:len(approaches)])
    ax2.set_title('Error Rates', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Percentage (%)')
    ax2.tick_params(axis='x', rotation=45)
    for bar, rate in zip(bars2, error_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
    
    # 3. No Prediction Rates
    bars3 = ax3.bar(approaches, no_prediction_rates, color=colors[:len(approaches)])
    ax3.set_title('No Prediction Rates', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Percentage (%)')
    ax3.tick_params(axis='x', rotation=45)
    for bar, rate in zip(bars3, no_prediction_rates):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
    
    # 4. Error Type Distribution (stacked)
    error_types = ["no_prediction", "partial_match", "over_prediction"]
    x = np.arange(len(approaches))
    width = 0.25
    
    for i, error_type in enumerate(error_types):
        counts = [data["error_type_distribution"][approach].get(error_type, 0) for approach in approaches]
        ax4.bar(x + i * width, counts, width, label=error_type.replace('_', ' ').title())
    
    ax4.set_title('Error Type Distribution', fontsize=14, fontweight='bold')
    ax4.set_xticks(x + width)
    ax4.set_xticklabels(approaches, rotation=45)
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'comprehensive_performance_summary.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_llm_vs_neural_comparison(data, output_dir):
    """Create comparison between LLM and neural approaches"""
    approaches = list(data["total_errors"].keys())
    
    # Separate LLM and neural approaches
    neural_approaches = [app for app in approaches if "Lingmess" in app]
    llm_approaches = [app for app in approaches if "GPT" in app or "Gemini" in app]
    
    # Calculate metrics
    total_clusters = 454
    
    neural_errors = [data["total_errors"][app] for app in neural_approaches]
    llm_errors = [data["total_errors"][app] for app in llm_approaches]
    
    neural_rates = [errors / total_clusters * 100 for errors in neural_errors]
    llm_rates = [errors / total_clusters * 100 for errors in llm_errors]
    
    # Create figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # 1. Error Count Comparison
    x = np.arange(len(neural_approaches + llm_approaches))
    all_errors = neural_errors + llm_errors
    all_approaches = neural_approaches + llm_approaches
    
    colors = ['#2E86AB'] * len(neural_approaches) + ['#A23B72'] * len(llm_approaches)
    bars1 = ax1.bar(all_approaches, all_errors, color=colors)
    ax1.set_title('Total Errors: Neural vs LLM Approaches', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Count')
    ax1.tick_params(axis='x', rotation=45)
    
    # Add legend
    neural_patch = mpatches.Patch(color='#2E86AB', label='Neural')
    llm_patch = mpatches.Patch(color='#A23B72', label='LLM')
    ax1.legend(handles=[neural_patch, llm_patch])
    
    # 2. Error Rate Comparison
    all_rates = neural_rates + llm_rates
    bars2 = ax2.bar(all_approaches, all_rates, color=colors)
    ax2.set_title('Error Rates: Neural vs LLM Approaches', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Percentage (%)')
    ax2.tick_params(axis='x', rotation=45)
    
    # Add percentage labels
    for bar, rate in zip(bars2, all_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'neural_vs_llm_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Generate all comprehensive paper figures"""
    output_dir = Path("outputs/comprehensive_paper_figures")
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    data = load_comprehensive_error_data()
    if not data:
        print("Failed to load comprehensive error analysis data!")
        return
    
    print("Generating comprehensive paper figures...")
    
    # Generate figures
    create_comprehensive_error_type_comparison(data, output_dir)
    print("✓ Comprehensive error type comparison figure generated")
    
    create_llm_comparison_figure(data, output_dir)
    print("✓ LLM comparison figure generated")
    
    create_performance_summary_figure(data, output_dir)
    print("✓ Comprehensive performance summary figure generated")
    
    create_llm_vs_neural_comparison(data, output_dir)
    print("✓ Neural vs LLM comparison figure generated")
    
    print(f"\n✓ All comprehensive paper figures generated successfully!")
    print(f"Figures saved to: {output_dir}")
    print("\nGenerated figures:")
    for fig_file in output_dir.glob("*.png"):
        print(f"  - {fig_file.name}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Generate publication-quality figures for the Hebrew Coreference Resolution paper
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

def load_error_data():
    """Load error analysis data"""
    comparison_file = Path("outputs/error_analysis/error_comparison.json")
    if not comparison_file.exists():
        print("Error comparison file not found!")
        return None
    
    with open(comparison_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_error_type_comparison(data, output_dir):
    """Create error type comparison figure"""
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
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create grouped bar chart
    x = np.arange(len(approaches))
    width = 0.2
    
    for i, error_type in enumerate(error_types):
        counts = [df[(df['Approach'] == approach) & (df['Error Type'] == error_type.replace('_', ' ').title())]['Count'].iloc[0] 
                 if len(df[(df['Approach'] == approach) & (df['Error Type'] == error_type.replace('_', ' ').title())]) > 0 else 0
                 for approach in approaches]
        ax.bar(x + i * width, counts, width, label=error_type.replace('_', ' ').title())
    
    ax.set_xlabel('Approach', fontsize=14)
    ax.set_ylabel('Number of Errors', fontsize=14)
    ax.set_title('Error Type Distribution Across Approaches', fontsize=16, fontweight='bold')
    ax.set_xticks(x + width * 1.5)
    ax.set_xticklabels(approaches, fontsize=12)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'error_type_comparison_paper.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_total_errors_comparison(data, output_dir):
    """Create total errors comparison figure"""
    approaches = list(data["total_errors"].keys())
    total_errors = list(data["total_errors"].values())
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Create bar chart with custom colors
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars = ax.bar(approaches, total_errors, color=colors[:len(approaches)])
    
    # Add value labels on bars
    for bar, value in zip(bars, total_errors):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                str(value), ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('Approach', fontsize=14)
    ax.set_ylabel('Total Errors', fontsize=14)
    ax.set_title('Total Errors by Approach', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'total_errors_comparison_paper.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_error_rate_comparison(data, output_dir):
    """Create error rate comparison figure"""
    approaches = list(data["total_errors"].keys())
    total_errors = list(data["total_errors"].values())
    
    # Calculate error rates (assuming 454 total clusters per approach)
    total_clusters = 454
    error_rates = [errors / total_clusters * 100 for errors in total_errors]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars = ax.bar(approaches, error_rates, color=colors[:len(approaches)])
    
    # Add percentage labels on bars
    for bar, rate in zip(bars, error_rates):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=12, fontweight='bold')
    
    ax.set_xlabel('Approach', fontsize=14)
    ax.set_ylabel('Error Rate (%)', fontsize=14)
    ax.set_title('Error Rate by Approach', fontsize=16, fontweight='bold')
    ax.set_ylim(0, 105)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'error_rate_comparison_paper.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_hebrew_error_patterns(output_dir):
    """Create Hebrew-specific error patterns figure"""
    # Load detailed error patterns
    patterns_file = Path("outputs/detailed_error_analysis/error_patterns.json")
    if not patterns_file.exists():
        print("Error patterns file not found!")
        return
    
    with open(patterns_file, 'r', encoding='utf-8') as f:
        patterns = json.load(f)
    
    # Extract category distribution
    category_data = patterns.get("category_distribution", {})
    if not category_data:
        print("No category distribution data found!")
        return
    
    # Convert to list for plotting
    categories = list(category_data.keys())
    counts = list(category_data.values())
    
    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Create horizontal bar chart for better readability
    y_pos = np.arange(len(categories))
    colors = plt.cm.Set3(np.linspace(0, 1, len(categories)))
    
    bars = ax.barh(y_pos, counts, color=colors)
    
    # Add value labels
    for i, (bar, count) in enumerate(zip(bars, counts)):
        ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2, 
                str(count), ha='left', va='center', fontsize=11)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels([cat.replace('_', ' ').title() for cat in categories], fontsize=12)
    ax.set_xlabel('Number of Errors', fontsize=14)
    ax.set_title('Hebrew-Specific Error Categories', fontsize=16, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'hebrew_error_categories_paper.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_model_comparison_summary(data, output_dir):
    """Create a comprehensive model comparison summary"""
    approaches = list(data["total_errors"].keys())
    total_errors = list(data["total_errors"].values())
    
    # Calculate additional metrics
    total_clusters = 454
    error_rates = [errors / total_clusters * 100 for errors in total_errors]
    
    # Get partial match rates
    partial_match_rates = []
    for approach in approaches:
        partial_matches = data["error_type_distribution"][approach].get("partial_match", 0)
        partial_match_rate = partial_matches / total_clusters * 100
        partial_match_rates.append(partial_match_rate)
    
    # Create subplot
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. Total Errors
    colors = ['#2E86AB', '#A23B72', '#F18F01']
    bars1 = ax1.bar(approaches, total_errors, color=colors[:len(approaches)])
    ax1.set_title('Total Errors', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Count')
    for bar, value in zip(bars1, total_errors):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                str(value), ha='center', va='bottom', fontsize=10)
    
    # 2. Error Rates
    bars2 = ax2.bar(approaches, error_rates, color=colors[:len(approaches)])
    ax2.set_title('Error Rates', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Percentage (%)')
    for bar, rate in zip(bars2, error_rates):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=10)
    
    # 3. Partial Match Rates
    bars3 = ax3.bar(approaches, partial_match_rates, color=colors[:len(approaches)])
    ax3.set_title('Partial Match Rates', fontsize=14, fontweight='bold')
    ax3.set_ylabel('Percentage (%)')
    for bar, rate in zip(bars3, partial_match_rates):
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
    ax4.set_xticklabels(approaches)
    ax4.legend()
    
    plt.tight_layout()
    plt.savefig(output_dir / 'model_comparison_summary_paper.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Generate all paper figures"""
    output_dir = Path("outputs/paper_figures")
    output_dir.mkdir(exist_ok=True)
    
    # Load data
    data = load_error_data()
    if not data:
        print("Failed to load error analysis data!")
        return
    
    print("Generating paper figures...")
    
    # Generate figures
    create_error_type_comparison(data, output_dir)
    print("✓ Error type comparison figure generated")
    
    create_total_errors_comparison(data, output_dir)
    print("✓ Total errors comparison figure generated")
    
    create_error_rate_comparison(data, output_dir)
    print("✓ Error rate comparison figure generated")
    
    create_hebrew_error_patterns(output_dir)
    print("✓ Hebrew error patterns figure generated")
    
    create_model_comparison_summary(data, output_dir)
    print("✓ Model comparison summary figure generated")
    
    print(f"\n✓ All paper figures generated successfully!")
    print(f"Figures saved to: {output_dir}")
    print("\nGenerated figures:")
    for fig_file in output_dir.glob("*.png"):
        print(f"  - {fig_file.name}")

if __name__ == "__main__":
    main() 
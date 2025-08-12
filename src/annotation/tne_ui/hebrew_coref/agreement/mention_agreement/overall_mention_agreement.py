#!/usr/bin/env python3
"""
Overall Mention Agreement Analysis
This script calculates mention agreement scores across all documents and creates visualizations.
"""

import os
import sys
import re
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mention_agreemnet_utils import process_annotations, read_annotation_data


def extract_document_number(file_path):
    """Extract document number from file path."""
    match = re.search(r'/(\d+)_', file_path)
    if match:
        return match.group(1)
    return None


def find_matching_documents(list1, list2):
    """Find matching documents between two lists."""
    doc_numbers_list1 = {extract_document_number(file): file for file in list1}
    doc_numbers_list2 = {extract_document_number(file): file for file in list2}
    
    common_docs = set(doc_numbers_list1.keys()).intersection(set(doc_numbers_list2.keys()))
    matching_files = [(doc_numbers_list1[doc], doc_numbers_list2[doc]) for doc in common_docs]
    return matching_files


def extract_file_couples(annotator_names, mention_annotation_data_path):
    """Extract file couples for agreement calculation."""
    annotator_files = {}
    for name in annotator_names:
        annotator_files[name] = {f.split("_")[0]: f for f in file_by_annotator[name]}
    print(f"Check agreement for {len(annotator_files)} files")
    
    file_couples = []
    for i, name1 in enumerate(annotator_names):
        for j, name2 in enumerate(annotator_names[i + 1:], i + 1):
            a1_f = []
            a2_f = []
            
            for key, a1_file in annotator_files[name1].items():
                if key in annotator_files[name2]:
                    a1_f.append(os.path.join(mention_annotation_data_path, a1_file))
                    a2_f.append(os.path.join(mention_annotation_data_path, annotator_files[name2][key]))
            
            file_couples.append((a1_f, a2_f))
    return file_couples


def create_agreement_graph(doc_agreement_scores, output_path=None):
    """Create and save agreement graph."""
    # Convert document numbers to integers for proper sorting
    doc_numbers = [int(doc) for doc in doc_agreement_scores.keys()]
    agreement_scores = [doc_agreement_scores[str(doc)] * 100 for doc in doc_numbers]
    
    # Sort by document number
    sorted_indices = np.argsort(doc_numbers)
    sorted_docs = [doc_numbers[i] for i in sorted_indices]
    sorted_scores = [agreement_scores[i] for i in sorted_indices]
    
    # Create bins of 50 documents each
    bin_size = 50
    doc_bins = []
    score_bins = []
    
    for i in range(0, len(sorted_docs), bin_size):
        bin_docs = sorted_docs[i:i+bin_size]
        bin_scores = sorted_scores[i:i+bin_size]
        
        if bin_scores:  # Only add if there are scores in this bin
            doc_bins.append(f"Docs {bin_docs[0]}-{bin_docs[-1]}")
            score_bins.append(np.mean(bin_scores))
    
    # Create the line plot
    plt.figure(figsize=(14, 8))
    
    # Create x-axis positions (middle of each bin)
    x_positions = range(len(doc_bins))
    
    # Plot the line
    plt.plot(x_positions, score_bins, marker='o', linewidth=3, markersize=8, 
             color='blue', alpha=0.8, label='Agreement Score Trend')
    
    # Add trend line
    if len(score_bins) > 1:
        z = np.polyfit(x_positions, score_bins, 1)
        p = np.poly1d(z)
        plt.plot(x_positions, p(x_positions), "--", color='red', alpha=0.7, 
                linewidth=2, label=f'Trend Line (slope: {z[0]:.2f})')
    
    # Customize the plot
    plt.xlabel('Document Ranges (every 50 docs)', fontsize=12)
    plt.ylabel('Average Mention Agreement Score (%)', fontsize=12)
    plt.title('Mention Agreement Scores Trend Over Documents', fontsize=14, fontweight='bold')
    plt.xticks(x_positions, doc_bins, rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    plt.ylim(min(score_bins) - 2, max(score_bins) + 2)  # Add some padding
    
    # Add value labels on points
    for i, score in enumerate(score_bins):
        plt.text(i, score + 0.5, f'{score:.1f}%', ha='center', va='bottom', 
                fontweight='bold', fontsize=10)
    
    # Add overall average line
    overall_avg = np.mean(score_bins)
    plt.axhline(y=overall_avg, color='green', linestyle=':', alpha=0.7, 
                linewidth=2, label=f'Overall Average: {overall_avg:.1f}%')
    
    plt.legend()
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Graph saved to: {output_path}")
    
    plt.show()
    
    # Print summary statistics
    print(f"\nSummary Statistics:")
    print(f"Number of document ranges: {len(doc_bins)}")
    print(f"Overall average agreement: {overall_avg:.2f}%")
    print(f"Range of agreement scores: {min(score_bins):.1f}% - {max(score_bins):.1f}%")
    
    # Calculate trend
    if len(score_bins) > 1:
        trend_slope = z[0]
        print(f"Trend slope: {trend_slope:.3f}")
        if trend_slope > 0:
            print("Trend: INCREASING (agreement scores are going up)")
        elif trend_slope < 0:
            print("Trend: DECREASING (agreement scores are going down)")
        else:
            print("Trend: STABLE (no clear trend)")
    
    return doc_bins, score_bins


def main():
    """Main function to run the mention agreement analysis."""
    print("=== Overall Mention Agreement Analysis ===\n")
    
    # Set paths
    mention_annotation_data_path = "../../mention_annotation_data"
    
    # Get all document ranges from the mention annotation data
    print("Scanning mention annotation data...")
    all_docs = set()
    for annotator_name in os.listdir(mention_annotation_data_path):
        annotator_dir = os.path.join(mention_annotation_data_path, annotator_name)
        if os.path.isdir(annotator_dir):
            for file_name in os.listdir(annotator_dir):
                if file_name.endswith(".json"):
                    doc_id = int(file_name.split(".")[0])
                    all_docs.add(doc_id)
    
    print(f"Total documents found: {len(all_docs)}")
    print(f"Document range: {min(all_docs)} - {max(all_docs)}")
    
    # Exclude certain annotators as in the original files
    exclude_annotators = {
        'ariela levkov', 'Ariela', 'Yeshaaya Klein', 'Hadas Elitzur',
        'Bar Shwarts', 'Nofar Eidlman', 'itay atal', 'may green',
        'Shay Umaschi', 'matan schwartz', 'tsofit hadad', 'Tal Chayen',
        'Yovelarye', 'אוריאל אטווד', 'shachar sasson', 'Noa Nagary', 'Ido',
        'Shimrit Devora Laufer', 'Hadar Salniker', 'Ayala Dvir', 'Aviv Sason',
        'Shali Bernstein', 'Itamar Adoram', 'yechiel hexter', 'Arbel',
        'Yuval Sagi', 'Hinoy Meirovitch', 'Yovel arye', 'hadar livyatan',
        'Rom Golan'
    }
    
    # Read all annotation data
    print("\nReading annotation data...")
    file_by_annotator = read_annotation_data(mention_annotation_data_path, 
                                            specific_files=all_docs,
                                            exclude=exclude_annotators)
    
    print(f"Annotators included: {list(file_by_annotator.keys())}")
    
    # Calculate agreement scores for each document
    print("\nCalculating agreement scores...")
    scores = defaultdict(list)
    doc_agreement_scores = {}
    
    for doc_id in sorted(all_docs):
        # Get annotations for this document from all annotators
        doc_annotations = {}
        for annotator, annotations in file_by_annotator.items():
            if doc_id in annotations:
                doc_annotations[annotator] = {doc_id: annotations[doc_id]}
        
        if len(doc_annotations) >= 2:  # Need at least 2 annotators for agreement
            try:
                agreement_score = process_annotations(doc_annotations)
                scores[str(doc_id)].append(agreement_score)
                doc_agreement_scores[str(doc_id)] = agreement_score
            except Exception as e:
                print(f"Error calculating agreement for document {doc_id}: {e}")
                continue
    
    print(f"Successfully calculated agreement for {len(doc_agreement_scores)} documents")
    
    # Calculate overall average agreement
    overall_agreement = sum(doc_agreement_scores.values()) / len(doc_agreement_scores)
    print(f"\nOverall mention agreement score: {overall_agreement * 100:.2f}%")
    
    # Create a DataFrame for analysis
    mention_agreement_df = pd.DataFrame([
        {'doc_id': int(doc_id), 'agreement_score': score * 100} 
        for doc_id, score in doc_agreement_scores.items()
    ])
    
    mention_agreement_df = mention_agreement_df.sort_values('doc_id')
    print(f"\nAgreement statistics:")
    print(f"Mean: {mention_agreement_df['agreement_score'].mean():.2f}%")
    print(f"Median: {mention_agreement_df['agreement_score'].median():.2f}%")
    print(f"Std: {mention_agreement_df['agreement_score'].std():.2f}%")
    print(f"Min: {mention_agreement_df['agreement_score'].min():.2f}%")
    print(f"Max: {mention_agreement_df['agreement_score'].max():.2f}%")
    
    # Create and save the agreement graph
    print("\nCreating agreement graph...")
    output_path = "mention_agreement_graph.png"
    create_agreement_graph(doc_agreement_scores, output_path)
    
    # Save results to CSV
    csv_path = "mention_agreement_results.csv"
    mention_agreement_df.to_csv(csv_path, index=False)
    print(f"\nResults saved to: {csv_path}")
    
    print("\n=== Analysis Complete ===")


if __name__ == "__main__":
    main() 
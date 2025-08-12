#!/usr/bin/env python3
"""
Test script to validate the SOTA tokenization conversion.

This script:
1. Tests the conversion on a few example documents
2. Shows before/after comparisons
3. Validates the conversion quality
"""

import json
import os
from convert_sota_tokenization_improved import ImprovedTokenAlignmentConverter


def test_conversion():
    """Test the conversion on a few example documents."""
    
    # Paths
    original_test_path = "data/lingmess/hebrew/test.hebrew.jsonlines"
    sota_tokenized_dir = "/Users/s0g0a87/studies/coref-llms/data_coref/hebrew/tokenized_documents_danit_tokenization/test"
    
    # Create converter
    converter = ImprovedTokenAlignmentConverter(original_test_path, sota_tokenized_dir)
    
    # Test on first few documents
    with open(original_test_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= 3:  # Only test first 3 documents
                break
                
            original_doc = json.loads(line.strip())
            doc_key = original_doc['doc_key']
            
            print(f"\n{'='*60}")
            print(f"Testing document: {doc_key}")
            print(f"{'='*60}")
            
            # Convert document
            converted_doc = converter.convert_document(original_doc)
            
            # Show comparison
            print(f"\nOriginal tokens (first 20):")
            print(f"  {original_doc['cased_words'][:20]}")
            
            print(f"\nSOTA tokens (first 20):")
            print(f"  {converted_doc['cased_words'][:20]}")
            
            print(f"\nOriginal clusters:")
            for j, cluster in enumerate(original_doc['clusters']):
                print(f"  Cluster {j}: {cluster}")
            
            print(f"\nConverted clusters:")
            for j, cluster in enumerate(converted_doc['clusters']):
                print(f"  Cluster {j}: {cluster}")
            
            print(f"\nToken count comparison:")
            print(f"  Original: {len(original_doc['cased_words'])} tokens")
            print(f"  SOTA: {len(converted_doc['cased_words'])} tokens")
            print(f"  Original clusters: {len(original_doc['clusters'])}")
            print(f"  Converted clusters: {len(converted_doc['clusters'])}")


def validate_alignment_quality():
    """Validate the quality of token alignment."""
    
    # Paths
    original_test_path = "data/lingmess/hebrew/test.hebrew.jsonlines"
    sota_tokenized_dir = "/Users/s0g0a87/studies/coref-llms/data_coref/hebrew/tokenized_documents_danit_tokenization/test"
    
    # Create converter
    converter = ImprovedTokenAlignmentConverter(original_test_path, sota_tokenized_dir)
    
    # Test alignment on first document
    with open(original_test_path, 'r', encoding='utf-8') as f:
        original_doc = json.loads(f.readline().strip())
    
    doc_key = original_doc['doc_key']
    sota_filename = converter.doc_mapping[doc_key]
    sota_text = converter._read_sota_tokenized_file(sota_filename)
    sota_tokens = converter._tokenize_text(sota_text)
    
    print(f"Alignment validation for document: {doc_key}")
    print(f"Original tokens: {len(original_doc['cased_words'])}")
    print(f"SOTA tokens: {len(sota_tokens)}")
    
    # Test alignment
    alignment = converter._align_tokens_robust(original_doc['cased_words'], sota_tokens)
    
    print(f"Alignment length: {len(alignment)}")
    
    # Show some alignment examples
    print(f"\nAlignment examples (first 10):")
    for i, (start, end) in enumerate(alignment[:10]):
        original_span = original_doc['cased_words'][start:end]
        sota_token = sota_tokens[i] if i < len(sota_tokens) else "N/A"
        print(f"  {i}: {original_span} -> '{sota_token}'")
    
    # Validate alignment
    is_valid = converter._validate_alignment(original_doc['cased_words'], sota_tokens, alignment)
    print(f"\nAlignment valid: {is_valid}")


if __name__ == "__main__":
    print("Testing SOTA tokenization conversion...")
    
    # Test conversion
    test_conversion()
    
    print(f"\n{'='*60}")
    print("Testing alignment quality...")
    print(f"{'='*60}")
    
    # Test alignment quality
    validate_alignment_quality()
    
    print("\nTesting completed!") 
#!/usr/bin/env python3
"""
Script to find the correct document mapping between old neural doc_ids and new test doc_ids
by examining the actual content of the files.
"""

import json
import os
from pathlib import Path
import re

def extract_first_sentence_from_conllu(file_path):
    """Extract the first sentence from a conllu file to use for matching."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Find the first sentence (lines that start with a word, not # or _)
            first_sentence = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and not line.startswith('_'):
                    parts = line.split('\t')
                    if len(parts) > 0:
                        word = parts[0]  # The first column contains the word
                        if word and word != '_':
                            first_sentence.append(word)
                            if word.endswith('.'):  # End of sentence
                                break
            return ' '.join(first_sentence[:10])  # First 10 words
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def get_first_sentence_from_neural(file_path):
    """Extract the first sentence from a neural jsonlines file to use for matching."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if first_line:
                doc_data = json.loads(first_line)
                if 'sentences' in doc_data and doc_data['sentences']:
                    # Get first few words of first sentence for matching
                    first_sent = doc_data['sentences'][0]
                    return ' '.join(first_sent[:10])  # First 10 words
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    return None

def find_correct_mapping():
    """Find the correct mapping between neural doc_ids and test doc_ids."""
    base_dir = Path(__file__).parent.parent
    
    # Paths to the files
    neural_file = base_dir / "error_analysis_data" / "gold" / "gold_neural" / "new_sota.test.hebrew.jsonlines"
    test_dir = base_dir.parent.parent / "HebNpChunker" / "corpus" / "coreference_final_split" / "mentions_by_parsed" / "test"
    
    if not neural_file.exists():
        print(f"Error: Neural file not found: {neural_file}")
        return
    
    if not test_dir.exists():
        print(f"Error: Test directory not found: {test_dir}")
        return
    
    # Get all test files
    test_files = list(test_dir.glob("htb:*.conllu"))
    print(f"Found {len(test_files)} test files")
    
    # Create mapping from first sentence to filename
    sentence_to_filename = {}
    for test_file in test_files:
        first_sentence = extract_first_sentence_from_conllu(test_file)
        if first_sentence:
            sentence_to_filename[first_sentence] = test_file.name.replace('.conllu', '')
            print(f"File {test_file.name}: {first_sentence[:50]}...")
    
    # Now process neural file to find mappings
    print(f"\nProcessing neural file: {neural_file}")
    
    correct_mapping = {}
    neural_docs = []
    
    with open(neural_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                doc_data = json.loads(line)
                if 'doc_key' in doc_data:
                    old_doc_key = doc_data['doc_key']
                    neural_docs.append((old_doc_key, line_num))
                    
                    # Get first sentence from neural file
                    if 'sentences' in doc_data and doc_data['sentences']:
                        first_sent = doc_data['sentences'][0]
                        neural_sentence = ' '.join(first_sent[:10])
                        
                        # Look for match in test files
                        found_match = False
                        for test_sentence, filename in sentence_to_filename.items():
                            if neural_sentence == test_sentence:
                                correct_mapping[old_doc_key] = filename
                                print(f"Line {line_num}: {old_doc_key} -> {filename}")
                                found_match = True
                                break
                        
                        if not found_match:
                            print(f"Line {line_num}: {old_doc_key} -> NO MATCH FOUND")
                            print(f"  Neural sentence: {neural_sentence}")
                            
            except json.JSONDecodeError as e:
                print(f"Line {line_num}: JSON decode error: {e}")
    
    print(f"\nFound {len(correct_mapping)} correct mappings:")
    for old_key, new_key in correct_mapping.items():
        print(f"  {old_key} -> {new_key}")
    
    # Save the correct mapping
    output_file = base_dir / "outputs" / "correct_document_mapping.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(correct_mapping, f, indent=2, ensure_ascii=False)
    
    print(f"\nCorrect mapping saved to: {output_file}")
    
    # Create a report
    report_file = base_dir / "outputs" / "correct_mapping_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("Correct Document Mapping Report\n")
        f.write("===============================\n\n")
        f.write(f"Summary:\n")
        f.write(f"- Neural documents: {len(neural_docs)}\n")
        f.write(f"- Test documents: {len(test_files)}\n")
        f.write(f"- Correct mappings found: {len(correct_mapping)}\n\n")
        f.write("Mapping entries:\n")
        for old_key, new_key in correct_mapping.items():
            f.write(f"  {old_key} -> {new_key}\n")
    
    print(f"Report saved to: {report_file}")
    
    return correct_mapping

if __name__ == "__main__":
    find_correct_mapping() 
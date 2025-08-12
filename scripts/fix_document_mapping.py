#!/usr/bin/env python3
"""
Script to fix document keys in neural results files using the document mapping.
"""

import json
import shutil
from pathlib import Path

def load_document_mapping(mapping_file_path):
    """Load the document mapping from JSON file."""
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fix_sota_tokenized_output(input_file_path, output_file_path, doc_mapping):
    """Fix the doc_key fields in the sota_tokenized_test_output.json file."""
    print(f"Processing {input_file_path}...")
    
    fixed_lines = []
    updated_count = 0
    
    with open(input_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                old_doc_key = data.get('doc_key')
                
                if old_doc_key and old_doc_key in doc_mapping:
                    new_doc_key = doc_mapping[old_doc_key]
                    data['doc_key'] = new_doc_key
                    updated_count += 1
                    print(f"  Updated doc_key: {old_doc_key} -> {new_doc_key}")
                elif old_doc_key:
                    print(f"  Warning: No mapping found for doc_key: {old_doc_key}")
                
                fixed_lines.append(json.dumps(data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")
                fixed_lines.append(line)
    
    # Write the fixed content
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for line in fixed_lines:
            f.write(line + '\n')
    
    print(f"Updated {updated_count} document keys in {output_file_path}")
    return updated_count

def fix_gold_output(input_file_path, output_file_path, doc_mapping):
    """Fix the doc_key fields in the gold test_output.json file."""
    print(f"Processing {input_file_path}...")
    
    fixed_lines = []
    updated_count = 0
    
    with open(input_file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                old_doc_key = data.get('doc_key')
                
                if old_doc_key and old_doc_key in doc_mapping:
                    new_doc_key = doc_mapping[old_doc_key]
                    data['doc_key'] = new_doc_key
                    updated_count += 1
                    print(f"  Updated doc_key: {old_doc_key} -> {new_doc_key}")
                elif old_doc_key:
                    print(f"  Warning: No mapping found for doc_key: {old_doc_key}")
                
                fixed_lines.append(json.dumps(data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")
                fixed_lines.append(line)
    
    # Write the fixed content
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for line in fixed_lines:
            f.write(line + '\n')
    
    print(f"Updated {updated_count} document keys in {output_file_path}")
    return updated_count

def main():
    """Main function to fix document keys in neural results files."""
    # Load document mapping
    mapping_file = "outputs/document_mapping.json"
    if not Path(mapping_file).exists():
        print(f"Error: Mapping file {mapping_file} not found!")
        return
    
    print("Loading document mapping...")
    doc_mapping = load_document_mapping(mapping_file)
    print(f"Loaded {len(doc_mapping)} document mappings")
    
    # Fix sota_tokenized_test_output.json
    sota_input = "error_analysis_data/neural/sota_tokenized/sota_tokenized_test_output.json"
    sota_output = "error_analysis_data/neural/sota_tokenized/sota_tokenized_test_output_fixed.json"
    
    if Path(sota_input).exists():
        # Create backup
        backup_file = sota_input + ".backup"
        shutil.copy2(sota_input, backup_file)
        print(f"Created backup: {backup_file}")
        
        # Fix the file
        sota_updated = fix_sota_tokenized_output(sota_input, sota_output, doc_mapping)
        
        # Replace original with fixed version
        shutil.move(sota_output, sota_input)
        print(f"Replaced original file with fixed version")
    else:
        print(f"Warning: {sota_input} not found")
    
    # Fix gold test_output.json
    gold_input = "error_analysis_data/neural/gold/test_output.json"
    gold_output = "error_analysis_data/neural/gold/test_output_fixed.json"
    
    if Path(gold_input).exists():
        # Create backup
        backup_file = gold_input + ".backup"
        shutil.copy2(gold_input, backup_file)
        print(f"Created backup: {backup_file}")
        
        # Fix the file
        gold_updated = fix_gold_output(gold_input, gold_output, doc_mapping)
        
        # Replace original with fixed version
        shutil.move(gold_output, gold_input)
        print(f"Replaced original file with fixed version")
    else:
        print(f"Warning: {gold_input} not found")
    
    print("\nDocument key fixing completed!")

if __name__ == "__main__":
    main() 
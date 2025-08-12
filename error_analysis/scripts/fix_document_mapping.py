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
                doc_data = json.loads(line)
                
                if 'doc_key' in doc_data:
                    old_doc_key = doc_data['doc_key']
                    if old_doc_key in doc_mapping:
                        new_doc_key = doc_mapping[old_doc_key]
                        doc_data['doc_key'] = new_doc_key
                        updated_count += 1
                        print(f"  Line {line_num}: Updated doc_key '{old_doc_key}' -> '{new_doc_key}'")
                    else:
                        print(f"  Line {line_num}: No mapping found for doc_key '{old_doc_key}'")
                
                fixed_lines.append(json.dumps(doc_data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"  Line {line_num}: JSON decode error: {e}")
                fixed_lines.append(line)
    
    with open(output_file_path, 'w', encoding='utf-8') as f:
        for line in fixed_lines:
            f.write(line + '\n')
    
    print(f"Updated {updated_count} document keys")
    print(f"Output written to: {output_file_path}")

def main():
    """Main function to fix document keys in neural results files."""
    base_dir = Path(__file__).parent.parent
    mapping_file = base_dir / "outputs" / "document_mapping.json"
    neural_dir = base_dir / "error_analysis_data" / "neural"
    
    sota_tokenized_input = neural_dir / "sota_tokenized" / "sota_tokenized_test_output.json"
    sota_tokenized_backup = neural_dir / "sota_tokenized" / "sota_tokenized_test_output.json.backup"
    sota_tokenized_fixed = neural_dir / "sota_tokenized" / "sota_tokenized_test_output_fixed.json"
    
    if not mapping_file.exists():
        print(f"Error: Document mapping file not found: {mapping_file}")
        return
    
    if not sota_tokenized_input.exists():
        print(f"Error: Sota tokenized input file not found: {sota_tokenized_input}")
        return
    
    print("Loading document mapping...")
    doc_mapping = load_document_mapping(mapping_file)
    print(f"Loaded {len(doc_mapping)} document mappings")
    
    print(f"Creating backup of {sota_tokenized_input}...")
    shutil.copy2(sota_tokenized_input, sota_tokenized_backup)
    print(f"Backup created: {sota_tokenized_backup}")
    
    fix_sota_tokenized_output(sota_tokenized_input, sota_tokenized_fixed, doc_mapping)
    
    print("\nDocument key fixing completed!")
    print(f"Original file backed up to: {sota_tokenized_backup}")
    print(f"Fixed file written to: {sota_tokenized_fixed}")

if __name__ == "__main__":
    main() 
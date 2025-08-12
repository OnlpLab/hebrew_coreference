#!/usr/bin/env python3
"""
Script to fix document keys in neural results files using the correct document mapping.
"""

import json
import shutil
from pathlib import Path

def load_document_mapping(mapping_file_path):
    """Load the document mapping from JSON file."""
    with open(mapping_file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def fix_neural_file(input_file_path, output_file_path, doc_mapping):
    """Fix the doc_key fields in the neural file."""
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
    mapping_file = base_dir / "outputs" / "correct_document_mapping.json"
    neural_dir = base_dir / "error_analysis_data" / "gold" / "gold_neural"
    
    # Input files to fix
    input_files = [
        "new_sota.test.hebrew.jsonlines",
        "test.hebrew.jsonlines"
    ]
    
    if not mapping_file.exists():
        print(f"Error: Document mapping file not found: {mapping_file}")
        return
    
    print("Loading document mapping...")
    doc_mapping = load_document_mapping(mapping_file)
    print(f"Loaded {len(doc_mapping)} document mappings")
    
    # Process each input file
    for input_filename in input_files:
        input_file = neural_dir / input_filename
        if not input_file.exists():
            print(f"Warning: Input file not found: {input_file}")
            continue
        
        print(f"\nProcessing {input_filename}...")
        
        # Create backup
        backup_file = neural_dir / f"{input_filename}.backup"
        print(f"Creating backup: {backup_file}")
        shutil.copy2(input_file, backup_file)
        
        # Create fixed output file
        output_filename = input_filename.replace('.jsonlines', '_fixed.jsonlines')
        output_file = neural_dir / output_filename
        
        # Fix the document keys
        fix_neural_file(input_file, output_file, doc_mapping)
        
        print(f"Original file backed up to: {backup_file}")
        print(f"Fixed file written to: {output_file}")
    
    print("\nDocument key fixing completed!")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Script to apply the CORRECT document mapping to neural results files.
"""

import json
import shutil
from pathlib import Path

def main():
    # Load the CORRECT document mapping
    with open("outputs/correct_document_mapping.json", 'r', encoding='utf-8') as f:
        correct_mapping = json.load(f)
    
    print(f"Loaded {len(correct_mapping)} CORRECT document mappings")
    
    # Files to fix
    files_to_fix = [
        "error_analysis_data/neural/sota_tokenized/sota_tokenized_test_output.json",
        "error_analysis_data/neural/gold/test_output.json"
    ]
    
    for file_path in files_to_fix:
        if not Path(file_path).exists():
            print(f"Warning: {file_path} not found, skipping...")
            continue
            
        print(f"\nProcessing {file_path}...")
        
        # Create backup
        backup_file = file_path + ".backup2"
        shutil.copy2(file_path, backup_file)
        print(f"Created backup: {backup_file}")
        
        # Read and fix the file
        fixed_lines = []
        updated_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    old_doc_key = data.get('doc_key')
                    
                    if old_doc_key and old_doc_key in correct_mapping:
                        new_doc_key = correct_mapping[old_doc_key]
                        data['doc_key'] = new_doc_key
                        updated_count += 1
                        print(f"  Line {line_num}: Updated doc_key '{old_doc_key}' -> '{new_doc_key}'")
                    elif old_doc_key:
                        print(f"  Warning: No mapping found for doc_key: {old_doc_key}")
                    
                    fixed_lines.append(json.dumps(data, ensure_ascii=False))
                    
                except json.JSONDecodeError as e:
                    print(f"  Error parsing line {line_num}: {e}")
                    fixed_lines.append(line)
        
        # Write the fixed content back to the original file
        with open(file_path, 'w', encoding='utf-8') as f:
            for line in fixed_lines:
                f.write(line + '\n')
        
        print(f"Updated {updated_count} document keys in {file_path}")
    
    print("\nCorrect document mapping applied to all files!")

if __name__ == "__main__":
    main() 
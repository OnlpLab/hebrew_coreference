#!/usr/bin/env python3
"""
Script to fix document keys in the gold test_output.json file.
"""

import json
import shutil

def main():
    # Load document mapping
    with open("outputs/document_mapping.json", 'r', encoding='utf-8') as f:
        doc_mapping = json.load(f)
    
    print(f"Loaded {len(doc_mapping)} document mappings")
    
    # Fix gold test_output.json
    gold_input = "error_analysis_data/neural/gold/test_output.json"
    
    # Create backup
    backup_file = gold_input + ".backup"
    shutil.copy2(gold_input, backup_file)
    print(f"Created backup: {backup_file}")
    
    # Read and fix the file
    fixed_lines = []
    updated_count = 0
    
    with open(gold_input, 'r', encoding='utf-8') as f:
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
                    print(f"  Line {line_num}: Updated doc_key '{old_doc_key}' -> '{new_doc_key}'")
                elif old_doc_key:
                    print(f"  Warning: No mapping found for doc_key: {old_doc_key}")
                
                fixed_lines.append(json.dumps(data, ensure_ascii=False))
                
            except json.JSONDecodeError as e:
                print(f"  Error parsing line {line_num}: {e}")
                fixed_lines.append(line)
    
    # Write the fixed content back to the original file
    with open(gold_input, 'w', encoding='utf-8') as f:
        for line in fixed_lines:
            f.write(line + '\n')
    
    print(f"\nUpdated {updated_count} document keys in {gold_input}")
    print("Document key fixing completed!")

if __name__ == "__main__":
    main() 
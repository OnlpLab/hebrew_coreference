#!/usr/bin/env python3
"""
Run comprehensive error analysis on all available test set outputs
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Define paths to the test results
    base_dir = Path(__file__).parent.parent
    
    # Lingmess coref results (SOTA tokenized evaluation)
    lingmess_path = base_dir / "src/neural_models/neural_coref/results/lingmess/dictabert_seed31415_sota_tokenized_eval"
    
    # LLM results paths
    llm_base = base_dir / "src/llm_evaluation/llm_coref/results/heb/gpt-4o-mini/test"
    
    # Raw text results
    llm_raw_text_path = llm_base / "e2e_train/raw_text/raw_text_1/doc_predictions.jsonl"
    
    # Gold mentions results  
    llm_gold_mentions_path = llm_base / "gold_mentions/gold_mention_1/doc_predictions.jsonl"
    
    # Check which paths exist
    available_paths = []
    
    if lingmess_path.exists():
        available_paths.append(("--lingmess_path", str(lingmess_path)))
        print(f"✓ Found lingmess results: {lingmess_path}")
    else:
        print(f"✗ Lingmess results not found: {lingmess_path}")
    
    if llm_raw_text_path.exists():
        available_paths.append(("--llm_raw_text_path", str(llm_raw_text_path)))
        print(f"✓ Found LLM raw text results: {llm_raw_text_path}")
    else:
        print(f"✗ LLM raw text results not found: {llm_raw_text_path}")
    
    if llm_gold_mentions_path.exists():
        available_paths.append(("--llm_gold_mentions_path", str(llm_gold_mentions_path)))
        print(f"✓ Found LLM gold mentions results: {llm_gold_mentions_path}")
    else:
        print(f"✗ LLM gold mentions results not found: {llm_gold_mentions_path}")
    
    # Look for SOTA tokenized LLM results
    # Check if there are any SOTA tokenized results in the LLM directory
    sota_llm_path = None
    for approach_dir in llm_base.iterdir():
        if approach_dir.is_dir() and "sota" in approach_dir.name.lower():
            for subdir in approach_dir.iterdir():
                if subdir.is_dir() and "doc_predictions.jsonl" in [f.name for f in subdir.iterdir()]:
                    sota_llm_path = subdir / "doc_predictions.jsonl"
                    break
            if sota_llm_path:
                break
    
    if sota_llm_path and sota_llm_path.exists():
        available_paths.append(("--llm_sota_path", str(sota_llm_path)))
        print(f"✓ Found LLM SOTA results: {sota_llm_path}")
    else:
        print("✗ LLM SOTA results not found")
    
    if not available_paths:
        print("No test results found to analyze!")
        print("\nExpected paths:")
        print(f"  - Lingmess: {lingmess_path}")
        print(f"  - LLM Raw Text: {llm_raw_text_path}")
        print(f"  - LLM Gold Mentions: {llm_gold_mentions_path}")
        print("  - LLM SOTA: (looked in LLM results directories)")
        return
    
    # Build command
    cmd = [sys.executable, "error_analysis/scripts/error_analysis.py", "--output_dir", "outputs/error_analysis"]
    
    for arg, path in available_paths:
        cmd.extend([arg, path])
    
    print(f"\nRunning error analysis with command:")
    print(" ".join(cmd))
    print()
    
    # Run the error analysis
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Error analysis completed successfully!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("✗ Error analysis failed!")
        print(f"Error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")

if __name__ == "__main__":
    main() 
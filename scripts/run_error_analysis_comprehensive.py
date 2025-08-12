#!/usr/bin/env python3
"""
Run comprehensive error analysis on all available test set outputs including Gemini 2.5 Pro
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Define paths to the test results
    base_dir = Path(__file__).parent.parent
    
    # Lingmess coref results (SOTA tokenized evaluation)
    lingmess_path = base_dir / "src/neural_models/neural_coref/results/lingmess/dictabert_seed31415_sota_tokenized_eval"
    
    # LLM results paths - GPT-4o-mini
    gpt_base = base_dir / "src/llm_evaluation/llm_coref/results/heb/gpt-4o-mini/test"
    gpt_raw_text_path = gpt_base / "e2e_train/raw_text/raw_text_1/doc_predictions.jsonl"
    gpt_gold_mentions_path = gpt_base / "gold_mentions/gold_mention_1/doc_predictions.jsonl"
    
    # LLM results paths - Gemini 2.5 Pro
    gemini_base = base_dir / "src/llm_evaluation/llm_coref/results/heb/gemini-2.5-pro/test"
    gemini_raw_text_path = gemini_base / "e2e_train/raw_text/raw_text_1/doc_predictions.jsonl"
    gemini_gold_mentions_path = gemini_base / "gold_mentions/gold_mention_1/doc_predictions.jsonl"
    
    # Check which paths exist
    available_paths = []
    
    if lingmess_path.exists():
        available_paths.append(("--lingmess_path", str(lingmess_path)))
        print(f"✓ Found lingmess results: {lingmess_path}")
    else:
        print(f"✗ Lingmess results not found: {lingmess_path}")
    
    # GPT-4o-mini results
    if gpt_raw_text_path.exists():
        available_paths.append(("--llm_raw_text_path", str(gpt_raw_text_path)))
        print(f"✓ Found GPT-4o-mini raw text results: {gpt_raw_text_path}")
    else:
        print(f"✗ GPT-4o-mini raw text results not found: {gpt_raw_text_path}")
    
    if gpt_gold_mentions_path.exists():
        available_paths.append(("--llm_gold_mentions_path", str(gpt_gold_mentions_path)))
        print(f"✓ Found GPT-4o-mini gold mentions results: {gpt_gold_mentions_path}")
    else:
        print(f"✗ GPT-4o-mini gold mentions results not found: {gpt_gold_mentions_path}")
    
    # Gemini 2.5 Pro results
    if gemini_raw_text_path.exists():
        available_paths.append(("--gemini_raw_text_path", str(gemini_raw_text_path)))
        print(f"✓ Found Gemini 2.5 Pro raw text results: {gemini_raw_text_path}")
    else:
        print(f"✗ Gemini 2.5 Pro raw text results not found: {gemini_raw_text_path}")
    
    if gemini_gold_mentions_path.exists():
        available_paths.append(("--gemini_gold_mentions_path", str(gemini_gold_mentions_path)))
        print(f"✓ Found Gemini 2.5 Pro gold mentions results: {gemini_gold_mentions_path}")
    else:
        print(f"✗ Gemini 2.5 Pro gold mentions results not found: {gemini_gold_mentions_path}")
    
    if not available_paths:
        print("No test results found to analyze!")
        return
    
    # Build command
    cmd = [sys.executable, "error_analysis/scripts/error_analysis.py", "--output_dir", "outputs/error_analysis_comprehensive"]
    
    for arg, path in available_paths:
        cmd.extend([arg, path])
    
    print(f"\nRunning comprehensive error analysis with command:")
    print(" ".join(cmd))
    print()
    
    # Run the error analysis
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✓ Comprehensive error analysis completed successfully!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("✗ Comprehensive error analysis failed!")
        print(f"Error: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")

if __name__ == "__main__":
    main() 
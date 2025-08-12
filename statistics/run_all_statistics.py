#!/usr/bin/env python3
"""
Run All Statistics Script for Hebrew NP Chunker

This script runs all statistics analysis scripts in the correct order.
"""

import subprocess
import sys
from pathlib import Path

def run_script(script_name, description):
    """Run a statistics script and handle errors."""
    print(f"\n{'='*80}")
    print(f"Running {description}...")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print("✅ Success!")
            print(result.stdout)
        else:
            print("❌ Error!")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False
    
    return True

def main():
    """Run all statistics scripts in order."""
    print("🚀 Starting comprehensive statistics analysis for Hebrew NP Chunker")
    print("📁 Running from statistics folder")
    
    # Define scripts to run in order
    scripts = [
        ("data_statistics.py", "Basic Data Statistics"),
        ("agreement_analysis.py", "Agreement Analysis"),
        ("tne_mention_statistics.py", "TNE Mention Statistics"),
        ("conllu_mention_counter.py", "CONLLU Mention Counter"),
        ("comprehensive_statistics.py", "Comprehensive Statistics"),
        ("final_statistics_summary.py", "Final Statistics Summary")
    ]
    
    success_count = 0
    total_count = len(scripts)
    
    for script, description in scripts:
        if run_script(script, description):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"📊 STATISTICS ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print(f"✅ Successful: {success_count}/{total_count}")
    print(f"❌ Failed: {total_count - success_count}/{total_count}")
    
    if success_count == total_count:
        print("\n🎉 All statistics scripts completed successfully!")
        print("📁 Check the outputs/ folder for results")
    else:
        print("\n⚠️  Some scripts failed. Check the output above for details.")

if __name__ == "__main__":
    main() 
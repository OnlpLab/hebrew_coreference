#!/usr/bin/env python3
"""
Demo integration for Hebrew Coreference Resolution System.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    """Main demo function."""
    print("=" * 60)
    print("HEBREW COREFERENCE RESOLUTION SYSTEM - DEMO")
    print("=" * 60)
    
    print("\nThis is a demo of the integrated Hebrew Coreference Resolution System.")
    print("The system includes the following components:")
    print("1. Mention Detection (NP chunking)")
    print("2. Web Annotation Interface (TNE UI)")
    print("3. Neural Coreference Models")
    print("4. LLM Evaluation")
    
    print("\nDemo completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
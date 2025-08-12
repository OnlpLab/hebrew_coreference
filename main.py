#!/usr/bin/env python3
"""
Hebrew Coreference Resolution System
Main entry point for the complete pipeline.
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from tools.integrated_workflow import main as run_workflow
except ImportError:
    # Fallback for testing
    run_workflow = None
from config import *

def main():
    """Main entry point for the Hebrew Coreference Resolution System."""
    parser = argparse.ArgumentParser(
        description="Hebrew Coreference Resolution System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete pipeline
  python main.py run --input data/corpus/UD_Hebrew-HTB/he_htb-ud-dev.conllu

  # Run individual components
  python main.py mention-detect --input <file> --parser stanza
  python main.py annotate --input <np_results> --db-name annotation_db
  python main.py train-neural --base-model onlplab/alephbert-base
  python main.py evaluate-llm --model gpt-4o-mini --eval-data data/example.jsonl

  # Start annotation server
  python main.py serve --db-dir data/tne_ui/data --db-name annotation_db

  # Run demo
  python main.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Run complete workflow
    run_parser = subparsers.add_parser('run', help='Run complete workflow')
    run_parser.add_argument('--input', required=True, help='Input file for mention detection')
    run_parser.add_argument('--parser', default='stanza', choices=['stanza', 'trankit', 'gold'], 
                           help='Parser to use for mention detection')
    run_parser.add_argument('--base-model', default='onlplab/alephbert-base', 
                           help='Base model for neural training')
    run_parser.add_argument('--llm-model', default='gpt-4o-mini', help='LLM model for evaluation')
    run_parser.add_argument('--prompt-template', default='doc_template', 
                           help='Prompt template for LLM')
    run_parser.add_argument('--eval-data', default='data/example.jsonl', 
                           help='Evaluation data for LLM')
    run_parser.add_argument('--start-server', action='store_true', 
                           help='Start TNE server after processing')
    run_parser.add_argument('--skip-neural', action='store_true', 
                           help='Skip neural model training')
    run_parser.add_argument('--skip-llm', action='store_true', 
                           help='Skip LLM evaluation')
    
    # Mention detection
    mention_parser = subparsers.add_parser('mention-detect', help='Run mention detection')
    mention_parser.add_argument('--input', required=True, help='Input file')
    mention_parser.add_argument('--parser', default='stanza', choices=['stanza', 'trankit', 'gold'], 
                               help='Parser to use')
    mention_parser.add_argument('--output', default='outputs/np_results.txt', 
                               help='Output file')
    
    # Annotation
    annotate_parser = subparsers.add_parser('annotate', help='Run data annotation')
    annotate_parser.add_argument('--input', required=True, help='NP results file')
    annotate_parser.add_argument('--db-name', default='annotation_db', 
                                help='Database name')
    annotate_parser.add_argument('--db-dir', default='data/tne_ui/data', 
                                help='Database directory')
    
    # Neural training
    neural_parser = subparsers.add_parser('train-neural', help='Train neural models')
    neural_parser.add_argument('--base-model', default='onlplab/alephbert-base', 
                              help='Base model for training')
    neural_parser.add_argument('--seeds', nargs='+', type=int, 
                              default=[42, 123, 2021, 31415, 27182], 
                              help='Random seeds for reproducibility')
    
    # LLM evaluation
    llm_parser = subparsers.add_parser('evaluate-llm', help='Evaluate LLM models')
    llm_parser.add_argument('--model', default='gpt-4o-mini', 
                           choices=['gpt-4o-mini', 'gpt4o', 'gpt4.1', 'gpt-3.5-turbo', 'gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-2.5-pro', 'o1', 'o3'], 
                           help='LLM model to evaluate')
    llm_parser.add_argument('--eval-data', default='data/example.jsonl', 
                           help='Evaluation data file')
    llm_parser.add_argument('--prompt-template', default='doc_template', 
                           choices=['doc_template', 'qa_template'], 
                           help='Prompt template')
    
    # Serve annotation server
    serve_parser = subparsers.add_parser('serve', help='Start annotation server')
    serve_parser.add_argument('--db-dir', default='data/tne_ui/data', 
                             help='Database directory')
    serve_parser.add_argument('--db-name', default='annotation_db', 
                             help='Database name')
    serve_parser.add_argument('--port', type=int, default=8080, 
                             help='Server port')
    
    # Demo
    demo_parser = subparsers.add_parser('demo', help='Run system demo')
    
    # Info
    info_parser = subparsers.add_parser('info', help='Show system information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == 'run':
        # Import and run the integrated workflow
        sys.argv = ['integrated_workflow.py'] + [
            '--input', args.input,
            '--parser', args.parser,
            '--base-model', args.base_model,
            '--llm-model', args.llm_model,
            '--prompt-template', args.prompt_template,
            '--eval-data', args.eval_data
        ]
        if args.start_server:
            sys.argv.append('--start-server')
        if args.skip_neural:
            sys.argv.append('--skip-neural')
        if args.skip_llm:
            sys.argv.append('--skip-llm')
        
        return run_workflow()
    
    elif args.command == 'mention-detect':
        from tools.integrated_workflow import run_mention_detection
        return 0 if run_mention_detection(args.input, args.output, args.parser) else 1
    
    elif args.command == 'annotate':
        from tools.integrated_workflow import convert_to_tne_format, load_to_tne_database
        tne_format = f"outputs/tne_format_{args.db_name}.json"
        if convert_to_tne_format(args.input, tne_format):
            return 0 if load_to_tne_database(tne_format, args.db_dir, args.db_name) else 1
        return 1
    
    elif args.command == 'train-neural':
        from tools.integrated_workflow import run_neural_training
        return 0 if run_neural_training(args.base_model, args.seeds) else 1
    
    elif args.command == 'evaluate-llm':
        from tools.integrated_workflow import run_llm_evaluation
        return 0 if run_llm_evaluation(args.model, args.eval_data, args.prompt_template) else 1
    
    elif args.command == 'serve':
        from tools.integrated_workflow import start_tne_server
        return 0 if start_tne_server(args.db_dir, args.db_name) else 1
    
    elif args.command == 'demo':
        from examples.demo_integration import main as run_demo
        return run_demo()
    
    elif args.command == 'info':
        print("Hebrew Coreference Resolution System")
        print("=" * 50)
        print(f"Version: 1.0.0")
        print(f"Components: {len(COMPONENTS)}")
        print(f"Parsers: {len(PARSERS)}")
        print(f"Neural Models: {len(NEURAL_MODELS)}")
        print(f"LLM Models: {len(LLM_MODELS)}")
        print()
        print("Components:")
        for name, config in COMPONENTS.items():
            print(f"  - {config['name']}: {config['description']}")
        print()
        print("Directories:")
        print(f"  - Source code: src/")
        print(f"  - Data: data/")
        print(f"  - Outputs: outputs/")
        print(f"  - Tools: tools/")
        print(f"  - Examples: examples/")
        print(f"  - Tests: tests/")
        print(f"  - Documentation: docs/")
        return 0
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
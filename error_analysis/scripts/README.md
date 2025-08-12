# Hebrew Coreference Error Analysis Scripts

This directory contains scripts for analyzing and comparing mistakes between different coreference resolution approaches.

## Scripts Overview

### 1. `simple_comparison.py` (Recommended for quick analysis)
A focused script that compares LLM vs Neural models with different tokenization strategies for document 240.

**Features:**
- Loads gold annotations from CONLLU files
- Loads predictions from LLM and Neural models
- Compares different tokenization approaches (raw, gold, SOTA)
- Calculates precision, recall, and F1 scores
- Identifies missing and extra mentions
- Generates detailed comparison reports

**Usage:**
```bash
cd error_analysis/scripts
python simple_comparison.py
```

### 2. `comprehensive_error_analysis.py`
A more comprehensive analysis script with additional features and extensibility.

**Features:**
- All features from simple_comparison.py
- More detailed error categorization
- Support for multiple documents
- Command-line interface with options
- Detailed cluster-level analysis
- Export capabilities

**Usage:**
```bash
cd error_analysis/scripts
python comprehensive_error_analysis.py --doc-id 240 --output results.json --report report.txt
```

## Requirements

Install the required dependencies:
```bash
pip install -r requirements.txt
```

## File Structure Expected

The scripts expect the following directory structure:
```
error_analysis/error_analysis_data/
├── gold/
│   ├── conllu/
│   │   └── htb:240.conllu          # Gold annotations
│   ├── raw/
│   │   └── 240.txt                  # Raw text
│   └── tokenized/
│       └── 240.txt                  # Tokenized text
├── llm/
│   ├── raw/
│   │   └── llm_raw_240.jsonl       # LLM raw predictions
│   ├── tokenized/
│   │   └── llm_gold_tok_240.jsonl  # LLM gold tokenization predictions
│   └── sota_tokenized/
│       └── llm_sota_tok_240.jsonl  # LLM SOTA tokenization predictions
└── neural/
    ├── gold/
    │   └── neural_gold_tokenization_240.jsonl      # Neural gold tokenization predictions
    └── sota_tokenized/
        └── neural_sota_tokenization_240.jsonl      # Neural SOTA tokenization predictions
```

## Output

The scripts generate:

1. **Console Output**: Summary statistics and comparison results
2. **JSON Results**: Detailed metrics and mention data saved to `comparison_results_240.json`
3. **Text Report**: Human-readable analysis (comprehensive script only)

## Key Metrics Explained

- **Precision**: Percentage of predicted mentions that are correct
- **Recall**: Percentage of gold mentions that were found
- **F1**: Harmonic mean of precision and recall
- **Missing Mentions**: Gold mentions that were not predicted
- **Extra Mentions**: Predicted mentions that don't exist in gold

## Customization

### Changing Document ID
Edit the `doc_id` variable in `simple_comparison.py` or use the `--doc-id` flag with the comprehensive script.

### Adding New Approaches
Modify the script to load additional prediction files and include them in the comparison.

### Changing Base Path
Update the `base_path` variable in the scripts to match your directory structure.

## Troubleshooting

### File Not Found Errors
- Ensure all expected files exist in the correct locations
- Check file permissions
- Verify the base path is correct

### Encoding Issues
- All scripts use UTF-8 encoding for Hebrew text
- If you encounter encoding errors, check your system's locale settings

### Performance
- For large documents, the comprehensive script may take longer to run
- Consider using the simple script for quick comparisons

## Example Output

```
=== Hebrew Coreference Error Analysis for Document 240 ===

Loading gold annotation...
Gold mentions: 45

Loading LLM results...
LLM Raw: 0.623 F1
LLM Gold Tokenization: 0.712 F1
LLM SOTA Tokenization: 0.689 F1

Loading Neural results...
Neural Gold Tokenization: 0.756 F1
Neural SOTA Tokenization: 0.734 F1

============================================================
COMPARISON REPORT
============================================================

LLM Raw:
  F1: 0.623
  Precision: 0.589
  Recall: 0.667
  Missing: 15
  Extra: 18

...

============================================================
BEST PERFORMING APPROACH: Neural Gold Tokenization (F1: 0.756)
============================================================
```

## Contributing

To extend these scripts:
1. Add new analysis functions to the `CorefAnalyzer` class
2. Implement new metric calculations
3. Add support for additional file formats
4. Enhance the reporting capabilities 
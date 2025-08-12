# LLM Output Comparison Script

This script compares the results from three different LLM tokenization approaches against their corresponding gold CONLLU files.

## 🎯 Purpose

Compare the performance of LLM coreference resolution across different tokenization strategies:
1. **Raw tokenization** (`llm_raw_*.jsonl`)
2. **Gold tokenization** (`llm_gold_tok_*.jsonl`) 
3. **SOTA tokenization** (`llm_sota_tok_*.jsonl`)

## 📁 Directory Structure

```
llm_comparison/
├── compare_llm_outputs.py    # Main comparison script
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── llm_comparison_results/  # Output directory (created automatically)
```

## 🚀 Usage

### 1. Comprehensive Analysis (All Documents, All Approaches)

```bash
cd llm_comparison
python compare_llm_outputs.py
```

This will:
- Compare all three LLM approaches against all available gold documents
- Generate comprehensive reports
- Save results in multiple formats (JSON, CSV, TXT)

### 2. Single Document Analysis (All Approaches)

```bash
python compare_llm_outputs.py --doc htb:240
```

Compare all three LLM approaches against a specific document.

### 3. Single Approach vs Single Document

```bash
python compare_llm_outputs.py --doc htb:240 --approach raw
```

Compare a specific LLM approach against a specific document.

### 4. With Detailed Analysis Options

```bash
python compare_llm_outputs.py --doc htb:240 --full-doc --show-diff --correct-mistaken
```

- `--full-doc`: Show full document with colored clusters
- `--show-diff`: Show key differences between predictions and gold
- `--correct-mistaken`: Show correct/mistaken cluster analysis

## 📊 Output Files

The script generates several output files in the `llm_comparison_results/` directory:

1. **`llm_comparison_results.json`** - Detailed results in JSON format
2. **`llm_comparison_report.txt`** - Human-readable summary report
3. **`llm_comparison_summary.csv`** - CSV table for easy analysis

## 🔧 Configuration

### Base Path
By default, the script assumes it's run from the `llm_comparison/` directory with the project root at `../`. You can customize this:

```bash
python compare_llm_outputs.py --base-path /path/to/project
```

### Output Directory
Customize the output directory:

```bash
python compare_llm_outputs.py --output-dir custom_results
```

## 📋 Example Output

```
🚀 Starting LLM Output Comparison Analysis
================================================================================
🔍 Running LLM comparisons for 10 documents...
📁 Available documents: htb:232, htb:233, htb:234, htb:235, htb:236, htb:237, htb:238, htb:239_1, htb:239_2, htb:240
🔄 LLM approaches: raw, gold_tokenized, sota_tokenized
================================================================================

📄 Processing document: htb:240
  🔄 Testing raw...
    ✅ raw: P=0.571, R=0.308, F1=0.400
  🔄 Testing gold_tokenized...
    ✅ gold_tokenized: P=0.750, R=0.692, F1=0.720
  🔄 Testing sota_tokenized...
    ✅ sota_tokenized: P=0.667, R=0.538, F1=0.596
```

## 🎨 Features

- **Automatic Document Discovery**: Finds all available gold CONLLU files
- **Flexible Comparison Modes**: Single document, single approach, or comprehensive
- **Multiple Output Formats**: JSON, CSV, and human-readable reports
- **Error Handling**: Gracefully handles missing files and comparison errors
- **Progress Tracking**: Shows real-time progress during analysis
- **Detailed Metrics**: Extracts precision, recall, and F1 scores

## 🔍 Troubleshooting

### Common Issues

1. **Import Error**: Make sure you're running from the `llm_comparison/` directory
2. **File Not Found**: Check that the LLM files exist in the expected locations
3. **Permission Error**: Ensure you have read access to the data directories

### File Naming Convention

The script expects LLM files to follow this naming pattern:
- Raw: `llm_raw_240.jsonl`
- Gold tokenized: `llm_gold_tok_240.jsonl`
- SOTA tokenized: `llm_sota_tok_240.jsonl`

Where `240` corresponds to the document key `htb:240`.

## 📈 Analysis Tips

1. **Start with a single document** to verify everything works
2. **Use the CSV output** for statistical analysis in Excel/R
3. **Compare approaches side-by-side** for the same document
4. **Look for patterns** across different document types

## 🤝 Dependencies

- Python 3.7+
- pandas
- pathlib (built-in for Python 3.4+)
- The `compare_neural.py` script from the parent directory

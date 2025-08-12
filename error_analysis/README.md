# Hebrew Coreference Resolution Error Analysis

This directory contains comprehensive error analysis tools for Hebrew coreference resolution, focusing on the main analysis pipeline and document mapping fixes.

## 📁 Directory Structure

```
error_analysis/
├── README.md                    # This file
├── FINAL_SUMMARY.md            # Project summary and status
├── scripts/                     # Analysis scripts
│   ├── reviewer_proof_analysis.py # Main comprehensive analysis script
│   └── fix_document_mapping.py    # Document mapping fix script
└── outputs/                     # Analysis results
    ├── reviewer_proof/          # Main analysis outputs
    ├── document_mapping.json    # Document key mappings
    └── mapping_report.txt       # Mapping creation report
```

## 🎯 Analysis Capabilities

### Main Analysis (`reviewer_proof_analysis.py`)
This is the primary analysis script that implements comprehensive error analysis across multiple priorities:

#### **Priority 1: Headline Claims**
- **Paired Bootstrap Significance**: Per-document resampling for MUC/B³/CEAF and CoNLL F1
- **Error Decomposition**: Boundary vs. linking errors analysis
- **Phenomenon-Sliced Evaluation**: Auto-tagging with linguistic features

#### **Priority 2: Tokenization Bottleneck**
- **Micro-analysis**: Gold vs. SOTA tokenization alignment
- **Boundary-tolerant Metrics**: ±2-char F1 validation

#### **Priority 3: Generality & Robustness**
- **Document Difficulty Analysis**: Feature-based performance prediction
- **Inter-system Agreement**: Clustering agreement between systems
- **Seed Variance**: Stability analysis for neural runs
- **Cluster Structure Effects**: Performance by cluster size/singleton proportion

### Document Mapping Fix (`fix_document_mapping.py`)
Resolves document naming mismatches between neural model outputs and test set files:
- Creates neural→test document mappings
- Fixes converted files with proper keys
- Generates mapping reports

## 🚀 Quick Start

### 1. Fix Document Mapping (if needed)

```bash
python error_analysis/scripts/fix_document_mapping.py \
  --neural_file "src/neural_models/neural_coref/results/lingmess/alephbert-base_seed42_model/test_output.json" \
  --test_dir "data/data/conllu/with_singleton/test" \
  --gold_conllu_dir "data/data/conllu/with_singleton/test" \
  --output_converted "path/to/output.json" \
  --mapping_file "error_analysis/outputs/document_mapping.json" \
  --create_new
```

### 2. Run Main Analysis

```bash
python error_analysis/scripts/reviewer_proof_analysis.py \
  --neural_gold "path/to/fixed_neural.json" \
  --llm_gold "src/llm_evaluation/llm_coref/results/heb/gpt4o/test/gold_mentions/gold_mention_1/doc_predictions.jsonl" \
  --output_dir "error_analysis/outputs/reviewer_proof/new_analysis" \
  --bootstrap_samples 1000
```

## 📊 Output Structure

The main analysis generates comprehensive outputs including:
- Statistical significance tests
- Error breakdowns and visualizations
- Phenomenon-sliced evaluation results
- Document difficulty analysis
- Inter-system agreement metrics

## 🔧 Dependencies

The analysis requires:
- Python 3.8+
- Core dependencies: numpy, pandas, matplotlib, seaborn
- Optional: scipy, scikit-learn for advanced statistical analysis
- Repository-specific evaluators for coreference metrics

## 📝 Notes

- This analysis assumes system outputs are in JSON/JSONL format with fields: `doc_key`, `gold_clusters`, `predicted_clusters`
- Uses fast-coref style CorefEvaluator for computing MUC/B³/CEAF and CoNLL F1 scores
- Designed to work with Hebrew coreference data and Hebrew-specific linguistic phenomena 
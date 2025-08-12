# Hebrew NP Chunker - Statistics Scripts

This directory contains scripts for analyzing the final train-dev-test data and generating comprehensive statistics for the Hebrew NP Chunker project.

## Scripts Overview

### 1. `data_statistics.py`
**Purpose**: Analyzes basic dataset statistics including document counts, sentence counts, token counts, and agreement data.

**Features**:
- Counts documents, sentences, and tokens across train/dev/test splits
- Calculates average and median sentences/tokens per document
- Analyzes agreement data from annotation results
- Generates basic visualizations

**Usage**:
```bash
python statistics/data_statistics.py
```

**Output**:
- `outputs/statistics/data_statistics.json` - Detailed statistics in JSON format
- `outputs/statistics/agreement_improvement.png` - Agreement improvement visualization

### 2. `agreement_analysis.py`
**Purpose**: Focuses specifically on agreement analysis and provides detailed agreement statistics.

**Features**:
- Extracts agreement data from existing notebook results
- Analyzes coreference and mention agreement scores
- Provides pairwise agreement analysis
- Creates comprehensive agreement visualizations

**Usage**:
```bash
python statistics/agreement_analysis.py
```

**Output**:
- `outputs/agreement_analysis/agreement_statistics.json` - Agreement statistics in JSON format
- `outputs/agreement_analysis/agreement_improvement_comprehensive.png` - Comprehensive agreement visualization

### 3. `comprehensive_statistics.py`
**Purpose**: Provides a complete analysis combining dataset statistics and agreement analysis.

**Features**:
- Complete dataset analysis (documents, sentences, tokens)
- Agreement analysis from multiple rounds
- Comprehensive visualizations with 9 subplots
- Summary statistics and improvement analysis

**Usage**:
```bash
python statistics/comprehensive_statistics.py
```

**Output**:
- `outputs/comprehensive_statistics.json` - Complete statistics in JSON format
- `outputs/comprehensive_statistics.png` - Comprehensive visualization

### 4. `conllu_mention_counter.py`
**Purpose**: Counts actual mentions from final CONLLU files and compares with_singleton vs no_singleton versions.

**Features**:
- Counts actual mentions from CONLLU files
- Compares with_singleton vs no_singleton versions
- Analyzes singleton mention distribution
- Provides detailed per-split statistics

**Usage**:
```bash
python statistics/conllu_mention_counter.py
```

**Output**:
- `outputs/conllu_mention_analysis/conllu_mention_comparison.json` - Comparison statistics in JSON format



## Key Statistics Summary

### Dataset Statistics
- **Total Documents**: 351 (301 train, 26 dev, 24 test)
- **Original Dataset**: 354 documents (3 excluded during final split)
- **Excluded Documents**: 160_1, 221_3, 221_2
- **Missing Base Documents**: 2, 26
- **Total Sentences**: 6,151
- **Total Tokens**: 159,975
- **Average Sentences per Document**: 17.52
- **Average Tokens per Document**: 455.77

### Mention Statistics (from CONLLU files)
- **Total Mentions (no singleton)**: 19,483
- **Total Mentions (with singleton)**: 45,689
- **Singleton Mentions**: 26,206 (57.4%)
- **Average Mentions per Document**: 55.5 (no singleton), 130.2 (with singleton)
- **Mention Distribution**: Train (16,907), Dev (1,181), Test (1,395)

### Agreement Statistics
- **CoNLL Score Improvement**: 29.3% (from 0.518 to 0.811)
- **Mention Score Improvement**: 22.2% (from 0.628 to 0.850)
- **Final Agreement Scores**:
  - CoNLL Score: 0.811 (81.1%)
  - Mention Score: 0.850 (85.0%)
  - Overall Agreement: 0.830 (83.0%)

## Visualization Features

The comprehensive visualization includes:
1. Document distribution across splits
2. Sentence and token distribution
3. Sentences per document distribution
4. Tokens per document distribution
5. Agreement improvement over rounds
6. Average pairwise agreement scores
7. Dataset composition pie chart
8. Summary statistics table

## Requirements

The scripts require the following Python packages:
- pandas
- numpy
- matplotlib
- seaborn

Install with:
```bash
pip install pandas numpy matplotlib seaborn
```

## Data Sources

The scripts analyze data from:
- `data/corpus/coreference_final_split/gold_splits/with_singleton/` - Final train/dev/test splits
- `src/annotation/tne_ui/annotation_results/` - Agreement data from annotation results
- Existing notebook results for agreement scores

## Usage Examples

### Basic Dataset Analysis
```bash
python statistics/data_statistics.py --output-dir outputs/my_analysis
```

### Agreement Analysis Only
```bash
python statistics/agreement_analysis.py --output-dir outputs/agreement_only
```

### Complete Analysis
```bash
python statistics/comprehensive_statistics.py --output-dir outputs/complete_analysis
```



## Output Files

Each script generates:
1. **JSON files** with detailed statistics in structured format
2. **PNG files** with visualizations showing trends and distributions
3. **Console output** with formatted statistics summary

The JSON files can be used for further analysis or integration with other tools. 
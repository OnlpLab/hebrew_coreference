# Individual Plots Summary

This document lists all the individual PNG images created from the comprehensive plots.

## Agreement Analysis Individual Plots

**Location:** `outputs/agreement_analysis/individual_plots/`

### 1. Coreference Agreement Improvement Over Rounds
- **File:** `01_coreference_agreement_improvement.png`
- **Description:** Line plot showing CoNLL and Mention agreement scores across annotation rounds
- **Content:** Shows improvement from Round 1 to Final, with clear round labels

### 2. Average Pairwise Agreement Scores
- **File:** `02_average_pairwise_agreement.png`
- **Description:** Line plot showing average pairwise agreement scores across rounds
- **Content:** Compares average CoNLL vs Mention scores with trend analysis

### 3. Agreement Score Comparison by Round
- **File:** `03_agreement_score_comparison.png`
- **Description:** Bar chart comparing CoNLL vs Mention scores side by side
- **Content:** Side-by-side comparison for each round with clear labels

### 4. Agreement Improvement Analysis
- **File:** `04_agreement_improvement_analysis.png`
- **Description:** Bar chart showing improvement between consecutive rounds
- **Content:** Shows the improvement delta between rounds for both metrics

## Comprehensive Statistics Individual Plots

**Location:** `outputs/comprehensive_statistics/individual_plots/`

### 1. Number of Documents by Split
- **File:** `01_documents_by_split.png`
- **Description:** Bar chart showing document counts for train/dev/test splits
- **Content:** Train: 301, Dev: 26, Test: 24 documents

### 2. Number of Sentences by Split
- **File:** `02_sentences_by_split.png`
- **Description:** Bar chart showing sentence counts for each split
- **Content:** Train: 5,236, Dev: 428, Test: 487 sentences

### 3. Number of Tokens by Split
- **File:** `03_tokens_by_split.png`
- **Description:** Bar chart showing token counts for each split
- **Content:** Train: 137,333, Dev: 10,474, Test: 12,168 tokens

### 4. Distribution of Sentences per Document
- **File:** `04_sentences_per_document_distribution.png`
- **Description:** Histogram showing the distribution of sentences per document
- **Content:** Shows frequency distribution with mean line

### 5. Distribution of Tokens per Document
- **File:** `05_tokens_per_document_distribution.png`
- **Description:** Histogram showing the distribution of tokens per document
- **Content:** Shows frequency distribution with mean line

### 6. Agreement Improvement Over Rounds
- **File:** `06_agreement_improvement_over_rounds.png`
- **Description:** Line plot showing agreement improvement across annotation rounds
- **Content:** CoNLL and Mention scores with trend lines

### 7. Average Pairwise Agreement Scores
- **File:** `07_average_pairwise_agreement_scores.png`
- **Description:** Line plot showing average pairwise agreement scores
- **Content:** Average CoNLL vs Mention scores across rounds

### 8. Dataset Composition by Split
- **File:** `08_dataset_composition_pie.png`
- **Description:** Pie chart showing the proportional composition of dataset splits
- **Content:** Train: 85.8%, Dev: 7.4%, Test: 6.8%

### 9. Dataset Summary Statistics
- **File:** `09_dataset_summary_statistics.png`
- **Description:** Table visualization showing key statistics for each split
- **Content:** Documents, sentences, tokens, averages per document for each split

## Usage

These individual plots can be used for:
- **Presentations:** Each plot is self-contained and ready for slides
- **Reports:** High-quality individual visualizations for documentation
- **Analysis:** Focused views on specific aspects of the data
- **Publications:** Individual figures for academic papers

## File Sizes

All plots are generated at 300 DPI for high-quality output suitable for:
- Print publications
- Presentations
- Web display
- Academic papers

## Generation

These plots were created using the `create_individual_plots.py` script, which:
1. Extracts data from the comprehensive analysis
2. Creates individual matplotlib figures for each subplot
3. Saves high-quality PNG files with descriptive names
4. Organizes files in logical subdirectories 
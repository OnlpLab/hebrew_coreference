# SOTA Tokenization Conversion for Hebrew Coreference Resolution

This document explains the solution for converting the original test set clusters to align with SOTA (State-of-the-Art) tokenization for Hebrew coreference resolution evaluation.

## Problem Description

The original test set uses gold tokenization with clusters aligned to it. However, you have a different SOTA tokenization that needs to be used for evaluation. The challenge is to convert the clusters from the original tokenization to align with the SOTA tokenization.

### Key Differences in Tokenization

**Original Tokenization:**
```
["ה", "פועל", "חולון"]  # 3 tokens
```

**SOTA Tokenization:**
```
["הפועל", "חולון"]  # 2 tokens
```

This means clusters that span multiple tokens in the original tokenization need to be converted to the corresponding spans in the SOTA tokenization.

## Solution Overview

The solution consists of three main components:

1. **Document Mapping**: Maps original document IDs to SOTA tokenized files
2. **Token Alignment**: Aligns tokens between the two tokenization schemes
3. **Cluster Conversion**: Converts cluster spans from original to SOTA tokenization

## Files Structure

```
src/sota_tokenization/
├── convert_clusters_to_sota_tokenization.py  # Main conversion script
├── compare_sota_tokenization.py              # Comparison and analysis tool
└── fix_clusters.py                          # Interactive fixing tool

data/lingmess/hebrew/
├── test.hebrew.jsonlines                    # Original test set
└── sota_tokenized/
    └── new_sota.test.hebrew.jsonlines      # Converted test set (output)
```

## Usage Workflow

### Step 1: Convert Clusters to SOTA Tokenization

```bash
cd src/sota_tokenization
python convert_clusters_to_sota_tokenization.py \
    --original /path/to/original/test.hebrew.jsonlines \
    --tokenized /path/to/sota/tokenized/documents \
    --output /path/to/new_test.hebrew.jsonlines
```

This script:
- **Matches documents** between original and SOTA tokenized versions using content similarity
- **Aligns tokens** using sequence matching with `difflib.SequenceMatcher`
- **Updates cluster indices** to refer to the new tokenization
- **Handles token merging/splitting** (e.g., "ה" + "פועל" → "הפועל")
- **Preserves sentence structure** and speaker information

### Step 2: Examine Changes

```bash
python compare_sota_tokenization.py \
    --orig /path/to/original/test.hebrew.jsonlines \
    --new /path/to/new_test.hebrew.jsonlines \
    --doc nw/3  # optional: examine specific document
```

This provides a detailed cluster-by-cluster comparison showing:
- **Original vs. new cluster spans** with color coding
- **Token-level differences** with context preview
- **Span-by-span alignment** for easy identification of changes
- **Interactive document selection** for focused analysis

### Step 3: Fix Alignment Issues

```bash
python fix_clusters.py \
    --orig /path/to/original/test.hebrew.jsonlines \
    --new /path/to/new_test.hebrew.jsonlines \
    --out /path/to/new_test.fixed.jsonlines
```

This interactive tool:
- **Automatically fixes** common issues:
  - Trailing punctuation inside spans
  - Superfluous 'של' + pronoun after pronoun base
  - Extra/missing leading definite article 'ה'
  - Clitic expansions (בוקו ↔ בוק של הוא)
  - Underscore tokens from segmenters
- **Prompts for manual review** of doubtful alignments
- **Allows manual corrections** for complex cases
- **Preserves cluster integrity** throughout the process

## Algorithm Details

### 1. Document Mapping

The script creates a mapping between original document IDs and SOTA tokenized files using content similarity:

```python
# Example mapping
"nw/3" -> "htb:232"
"nw/11" -> "htb:233"
"nw/65" -> "htb:234"
```

The matching algorithm:
1. **Normalizes content** by removing underscores and punctuation
2. **Compares concatenated tokens** between original and SOTA versions
3. **Uses SequenceMatcher** for similarity scoring when exact matches fail
4. **Ensures 1:1 mapping** between documents

### 2. Token Alignment

The robust token alignment algorithm:

1. **Sequence Matching**: Uses `difflib.SequenceMatcher` at the token level
2. **Span Distribution**: When multiple original tokens map to multiple SOTA tokens, distributes the span proportionally
3. **Deletion Handling**: Marks deleted tokens with (-1, -1) mapping
4. **Insertion Handling**: New tokens without original counterparts are handled separately

Example alignment:
```python
# Original: ["ה", "פועל", "חולון"]
# SOTA: ["הפועל", "חולון"]
# Alignment: [(0, 1), (1, 2)]  # "ה"+"פועל" -> "הפועל", "חולון" -> "חולון"
```

### 3. Cluster Conversion

For each cluster span in the original tokenization:

1. **Find Overlapping SOTA Tokens**: Identify which SOTA tokens overlap with the original span
2. **Convert Spans**: Map the original span to the corresponding SOTA token span
3. **Validation**: Ensure converted spans are valid and non-empty

Example conversion:
```python
# Original cluster: [[12, 15]]  # spans tokens 12-14
# SOTA alignment: [(10, 12), (12, 15), (15, 17)]
# Converted cluster: [[1, 2]]  # spans SOTA tokens 1-2
```

## Output Format

The converted test set maintains the same format as the original:

```json
{
  "cased_words": ["הפועל", "חולון", "..."],
  "sent_id": [0, 0, ...],
  "part_id": 0,
  "doc_key": "nw/65",
  "sentences": [["הפועל", "חולון", "..."]],
  "speakers": [["-", "-", "..."]],
  "clusters": [[[1, 2], [5, 6]]]
}
```

## Troubleshooting

### Common Issues

1. **Mapping Mismatch**: If document counts don't match, check the file lists and content similarity
2. **Alignment Failures**: If alignment quality is poor, examine the tokenization differences
3. **Empty Clusters**: Some clusters may become empty after conversion - use `fix_clusters.py` to review

### Debugging

Use the comparison tool to debug issues:

```bash
python compare_sota_tokenization.py \
    --orig /path/to/original/test.hebrew.jsonlines \
    --new /path/to/new_test.hebrew.jsonlines \
    --doc nw/3
```

This will show detailed alignment information and help identify problems.

## Integration with Evaluation

Once the conversion is complete, you can use the converted test set for evaluation:

1. **Model Training**: Train your model on the original training data
2. **Model Evaluation**: Use the converted test set for evaluation
3. **Results Comparison**: Compare results between original and SOTA tokenization

The evaluation is automatically integrated into the main experiment runner:

```bash
./src/run_all_experiments.sh onlplab/alephbert-base
```

This will automatically run SOTA tokenization evaluation alongside regular evaluation.

## Future Improvements

1. **Better Alignment Algorithm**: Implement more sophisticated alignment algorithms
2. **Quality Metrics**: Add quantitative measures of conversion quality
3. **Batch Processing**: Optimize for large-scale conversion
4. **Validation Tools**: Add more comprehensive validation checks

## Notes

- The conversion assumes that the SOTA tokenized files correspond 1:1 with the original test set
- The alignment algorithm uses sequence matching and may not find optimal alignments in all cases
- Some clusters may be lost or modified during conversion due to tokenization differences
- Always use the three-step workflow (convert → compare → fix) for best results
- The interactive fixing tool is essential for handling edge cases and ensuring quality 
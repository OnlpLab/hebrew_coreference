## Unified Experiment Runner

This project integrates [lingmess-coref](https://github.com/shon-otmazgin/lingmess-coref) and [wl-coref](https://github.com/vdobrovolskii/wl-coref) for reproducible coreference experiments.

### Prerequisites
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```
- Prepare data and weights as required by each model (see their respective READMEs).

### Running All Experiments

To run both models 5 times each (with fixed seeds) for a given base model (e.g., `onlplab/alephbert-base`):

```bash
chmod +x src/run_all_experiments.sh
./src/run_all_experiments.sh onlplab/alephbert-base
```

This will:
- Run **lingmess-coref** training and evaluation 5 times with seeds: 42, 123, 2021, 31415, 27182
- Run **SOTA tokenization evaluation** for lingmess-coref using the trained models
- Run **wl-coref** training and evaluation 5 times with the same seeds
- Save outputs in:
  - `results/lingmess/` (regular evaluation + SOTA tokenization evaluation)
  - `results/wlcoref/`
- Generate comprehensive summary tables including both regular and SOTA tokenization results

### SOTA Tokenized Evaluation

The project supports evaluation on SOTA tokenized data, allowing you to test models on text tokenized differently from the training data. This is now **automatically integrated** into the main experiment runner.

#### Integrated SOTA Evaluation

When you run `./src/run_all_experiments.sh`, the script automatically:

1. **Trains lingmess-coref models** on regular gold tokenized data
2. **Evaluates on regular test data** using the trained models
3. **Evaluates on SOTA tokenized test data** using the same trained models
4. **Generates summary tables** showing both regular and SOTA tokenization results

This allows you to compare how well models generalize to different tokenization schemes.

#### Standalone SOTA Evaluation

You can also run SOTA tokenization evaluation separately:

```bash
chmod +x src/run_sota_tokenized_evaluation.sh
./src/run_sota_tokenized_evaluation.sh onlplab/alephbert-base
```

This requires that you have already trained models using the main experiment runner.

#### Creating SOTA Tokenized Datasets

To create your own SOTA tokenized datasets for evaluation, use the tools in `src/sota_tokenization/`:

**Step 1: Convert Clusters to SOTA Tokenization**
```bash
cd src/sota_tokenization
python convert_clusters_to_sota_tokenization.py \
    --original /path/to/original/test.hebrew.jsonlines \
    --tokenized /path/to/sota/tokenized/documents \
    --output /path/to/new_test.hebrew.jsonlines
```

This script:
- Matches documents between original and SOTA tokenized versions
- Aligns original tokens with new tokens using sequence matching
- Updates coreference cluster indices to refer to new tokenization
- Handles token merging/splitting (e.g., "ה" + "פועל" → "הפועל")
- Preserves sentence structure and speaker information

**Step 2: Examine Changes**
```bash
python compare_sota_tokenization.py \
    --orig /path/to/original/test.hebrew.jsonlines \
    --new /path/to/new_test.hebrew.jsonlines \
    --doc nw/3  # optional: examine specific document
```

This provides a detailed cluster-by-cluster comparison showing:
- Original vs. new cluster spans
- Token-level differences with context
- Color-coded output for easy identification of changes

**Step 3: Fix Alignment Issues**
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

#### How it works

1. **Training**: Uses regular gold tokenized data (train/dev)
2. **Testing**: Uses SOTA tokenized text with aligned gold clusters
3. **Alignment**: Maps gold cluster indices to SOTA token indices
4. **Evaluation**: Standard coreference evaluation metrics

The key insight is that you train on the regular data but test on SOTA tokenized text to see how well the model generalizes to different tokenization schemes.

For detailed documentation, see [SOTA_TOKENIZED_EVALUATION.md](SOTA_TOKENIZED_EVALUATION.md).

### Results and Summary Tables

After running experiments, you can generate comprehensive summary tables:

```bash
python src/print_experiment_summary.py
```

This will display:
- **Regular evaluation results** (averaged across seeds)
- **SOTA tokenization evaluation results** (averaged across seeds)
- **Detailed individual run results** for both evaluation types
- **wl-coref results** (averaged across seeds)

The summary includes:
- Overall average F1 scores
- MUC, B³, and CEAF metrics
- Number of seeds used for averaging
- Clear distinction between regular and SOTA tokenization results

### Evaluating Outputs

To evaluate a model's output using the unified evaluation script:

```bash
python src/evaluate.py <eval_compatible_output.json> <output_dir>
```
- `<eval_compatible_output.json>`: The file produced by wl-coref with `--eval-compatible-output`, or the output from lingmess-coref in the correct format.
- `<output_dir>`: Directory to save evaluation results.

### Notes
- You can modify the seeds or add more by editing the `SEEDS` array in `src/run_all_experiments.sh`.
- Ensure all data paths and weights are set up as required by each model.
- SOTA tokenization evaluation is only available for lingmess-coref (not wl-coref).
- For more details, see the original READMEs:
  - [lingmess-coref](https://github.com/shon-otmazgin/lingmess-coref)
  - [wl-coref](https://github.com/vdobrovolskii/wl-coref) 
#!/bin/bash
# Evaluate a trained lingmess-coref model on the SOTA–tokenised test-set
# Usage:  ./evaluate_lingmess_sota.sh <MODEL_NAME_OR_PATH> <SEED>

set -e
MODEL_NAME_OR_PATH=${1:-onlplab/alephbert-base}
SEED=${2:-42}

# paths (relative to workspace/src)
SOTA_TEST=../data/lingmess/hebrew/sota_tokenized/test.sota_tokenized_danit_improved.jsonlines
TRAIN=../data/lingmess/hebrew/train.hebrew.jsonlines
DEV=../data/lingmess/hebrew/dev.hebrew.jsonlines

OUTDIR=../results/sota_evaluation/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}
BEST_MODEL_DIR=../results/lingmess/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}_model/model
mkdir -p "$OUTDIR"

PYTHON_PATH="/Users/s0g0a87/miniforge3/envs/neural_hebrew_coref/bin/python"

log(){ echo "[$(date '+%H:%M:%S')] $1"; }

# quick structural validation – abort if anything is wrong
$PYTHON_PATH validate_sota_quick.py "$SOTA_TEST"

if [ ! -d "$BEST_MODEL_DIR" ]; then
  echo "Model weights not found at $BEST_MODEL_DIR"; exit 1; fi

log "Running lingmess-coref evaluation on SOTA tokens"
# Clear any existing cache to avoid dataset conflicts
rm -rf "$OUTDIR/cache"

$PYTHON_PATH lingmess-coref/run_sota.py \
  --model_name_or_path "$BEST_MODEL_DIR" \
  --seed "$SEED" \
  --output_file "$OUTDIR/test_output.json" \
  --eval_split test \
  --output_dir "$OUTDIR" \
  --overwrite_output_dir \
  --cache_dir "$OUTDIR/cache" \
  --train_file "$TRAIN" \
  --dev_file "$DEV" \
  --test_file  "$SOTA_TEST" \
  --device cpu

mkdir -p "$OUTDIR/test_eval"
$PYTHON_PATH evaluate.py "$OUTDIR/test_output.json" "$OUTDIR/test_eval/"
log "Done. Results in $OUTDIR/test_eval/overall_F1.json"
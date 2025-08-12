#!/bin/bash

# Neural Hebrew Coreference Resolution - SOTA Tokenized Evaluation Runner
# This script runs lingmess-coref model evaluation on SOTA tokenized test data
# Usage: ./run_sota_tokenized_evaluation.sh <model_name_or_path>
# Example: ./run_sota_tokenized_evaluation.sh onlplab/alephbert-base

set -e  # Exit on any error
cd /workspace/src

# Check if model parameter is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <model_name_or_path>"
    echo "Example: $0 onlplab/alephbert-base"
    exit 1
fi

# Configuration
MODEL_NAME_OR_PATH="$1"  # Model name from command line argument
SEEDS=(42 123 2021 27182 31415)  # Fixed seeds for reproducibility

# Logging function
log() {
    echo "[$(date '+%m/%d/%Y %H:%M:%S')] - $1"
}

# Error handling function
run_step() {
    local step_name="$1"
    shift
    # shellcheck disable=SC2124
    local cmd="$@"
    
    log "Starting: $step_name"
    if eval "$cmd"; then
        log "SUCCESS: $step_name completed successfully."
    else
        log "ERROR: $step_name failed with exit code $?"
        exit 1
    fi
}

# Check if required files exist
check_file() {
    if [ ! -f "$1" ]; then
        log "ERROR: $2"
        exit 1
    fi
}

# Data file paths (relative to workspace/src)
SOTA_TOKENIZED_TEST=../data/lingmess/hebrew/sota_tokenized/new_sota.test.hebrew.jsonlines

# Output directories (relative to workspace/src)
LINGMESS_OUT=../results/lingmess
mkdir -p $LINGMESS_OUT

log "==== Starting SOTA tokenized evaluation for model: $MODEL_NAME_OR_PATH ===="

# Check data files exist
log "Checking data files..."
check_file "$SOTA_TOKENIZED_TEST" "SOTA tokenized test file missing."

# Run lingmess-coref evaluation on SOTA tokenized data for each seed
for SEED in "${SEEDS[@]}"; do
  OUTDIR=$LINGMESS_OUT/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}_sota_tokenized_eval
  # Use the trained model path from the server results
  TRAINED_MODEL_PATH=$LINGMESS_OUT/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}_model/model
  mkdir -p $OUTDIR
  log "---- [lingmess-coref] Seed $SEED: SOTA tokenized test evaluation ----"
  
  # Check if trained model exists
  if [ ! -d "$TRAINED_MODEL_PATH" ]; then
    log "ERROR: Trained model not found at $TRAINED_MODEL_PATH. Please ensure the model has been trained first."
    exit 1
  fi
  
  # Run evaluation without training (--do_train false)
  run_step "lingmess-coref SOTA tokenized test evaluation (seed $SEED)" \
    python lingmess-coref/run.py \
      --model_name_or_path $TRAINED_MODEL_PATH \
      --seed $SEED \
      --output_file $OUTDIR/sota_tokenized_test_output.json \
      --eval_split test \
      --output_dir $OUTDIR \
      --overwrite_output_dir \
      --test_file $SOTA_TOKENIZED_TEST \
      --device cuda:0
  
  # Convert lingmess-coref output to evaluate.py format
  run_step "lingmess-coref SOTA tokenized format conversion (seed $SEED)" \
    python convert_lingmess_output.py $OUTDIR/sota_tokenized_test_output.json $SOTA_TOKENIZED_TEST $OUTDIR/sota_tokenized_test_output_converted.json

  # Before evaluation, ensure test_eval directory exists
  mkdir -p $OUTDIR/test_eval
  run_step "lingmess-coref SOTA tokenized unified evaluation (seed $SEED)" \
    python evaluate.py $OUTDIR/sota_tokenized_test_output_converted.json $OUTDIR/test_eval/
  log "[lingmess-coref] Seed $SEED: SOTA tokenized test evaluation complete."
done

log "==== All SOTA tokenized evaluations completed. ===="

# Print summary table
python print_experiment_summary.py 
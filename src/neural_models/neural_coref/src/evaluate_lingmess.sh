#!/bin/bash

# Evaluation script for lingmess-coref
# This runs just the evaluation part if you already have a trained model

set -e  # Exit on any error

# Configuration
MODEL_NAME_OR_PATH="onlplab/alephbert-base"
SEED=42

# Logging function
log() {
    echo "[$(date '+%m/%d/%Y %H:%M:%S')] - $1"
}

# Error handling function
run_step() {
    local step_name="$1"
    shift
    local cmd="$@"
    
    log "Starting: $step_name"
    if eval "$cmd"; then
        log "SUCCESS: $step_name completed successfully."
    else
        log "ERROR: $step_name failed with exit code $?"
        return 1
    fi
}

# Data file paths
LINGMESS_TRAIN=../data/lingmess/hebrew/train.hebrew.jsonlines
LINGMESS_DEV=../data/lingmess/hebrew/dev.hebrew.jsonlines
LINGMESS_TEST=../data/lingmess/hebrew/test.hebrew.jsonlines

# Output directory
OUTDIR=../results/lingmess/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}_model
BEST_MODEL_DIR=$OUTDIR/model

log "==== Evaluating lingmess-coref for model: $MODEL_NAME_OR_PATH ===="

# Check if model directory exists
if [ ! -d "$BEST_MODEL_DIR" ]; then
    log "ERROR: Model directory not found: $BEST_MODEL_DIR"
    log "Please run training first or check if the model was saved correctly."
    exit 1
fi

log "Model directory found. Running test evaluation..."

# Run test evaluation
run_step "lingmess-coref test eval (seed $SEED)" \
  python lingmess-coref/run.py \
    --model_name_or_path $MODEL_NAME_OR_PATH \
    --seed $SEED \
    --output_file $OUTDIR/test_output.json \
    --do_train false \
    --eval_split test \
    --output_dir $BEST_MODEL_DIR \
    --train_file $LINGMESS_TRAIN \
    --dev_file $LINGMESS_DEV \
    --test_file $LINGMESS_TEST \
    --device cuda:0

# Run unified evaluation to get detailed metrics
if [ -f "$OUTDIR/test_output.json" ]; then
    log "Test output found. Running unified evaluation..."
    mkdir -p $OUTDIR/test_eval
    run_step "lingmess-coref unified evaluation (seed $SEED)" \
      python evaluate.py $OUTDIR/test_output.json $OUTDIR/test_eval/
    
    # Show the results
    if [ -f "$OUTDIR/test_eval/overall_F1.json" ]; then
        log "Evaluation completed. Results:"
        cat $OUTDIR/test_eval/overall_F1.json
    fi
else
    log "ERROR: test_output.json not found after test evaluation."
    exit 1
fi

log "==== Evaluation complete ====" 
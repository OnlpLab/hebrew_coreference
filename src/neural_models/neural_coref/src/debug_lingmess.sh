#!/bin/bash

# Debug script for lingmess-coref training
# This will help us see what's going wrong with the training

set -e  # Exit on any error
cd workspace/src

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
mkdir -p $OUTDIR

log "==== Debugging lingmess-coref for model: $MODEL_NAME_OR_PATH ===="

# Check data files exist
log "Checking data files..."
if [ ! -f "$LINGMESS_TRAIN" ]; then
    log "ERROR: lingmess-coref train file missing: $LINGMESS_TRAIN"
    exit 1
fi
if [ ! -f "$LINGMESS_DEV" ]; then
    log "ERROR: lingmess-coref dev file missing: $LINGMESS_DEV"
    exit 1
fi
if [ ! -f "$LINGMESS_TEST" ]; then
    log "ERROR: lingmess-coref test file missing: $LINGMESS_TEST"
    exit 1
fi

log "Data files found. Starting training..."

# Run lingmess-coref training and dev evaluation
run_step "lingmess-coref train+dev (seed $SEED)" \
  python lingmess-coref/run.py \
    --model_name_or_path $MODEL_NAME_OR_PATH \
    --seed $SEED \
    --output_file $OUTDIR/dev_output.json \
    --do_train \
    --eval_split dev \
    --output_dir $OUTDIR \
    --overwrite_output_dir \
    --train_file $LINGMESS_TRAIN \
    --dev_file $LINGMESS_DEV \
    --test_file $LINGMESS_TEST \
    --device cuda:0

# Check if training completed successfully
if [ -f "$OUTDIR/best_f1.json" ]; then
    log "Training completed. Checking best_f1.json..."
    cat $OUTDIR/best_f1.json
else
    log "ERROR: best_f1.json not found. Training may have failed."
    exit 1
fi

# Check if model directory exists
BEST_MODEL_DIR=$OUTDIR/model
if [ -d "$BEST_MODEL_DIR" ]; then
    log "Model directory found. Running test evaluation..."
    
    # Ensure test_model directory exists
    mkdir -p $OUTDIR/test_model
    
    # Run test evaluation
    run_step "lingmess-coref test eval (seed $SEED)" \
      python lingmess-coref/run.py \
        --model_name_or_path $OUTDIR/model \
        --seed $SEED \
        --output_file $OUTDIR/test_output.json \
        --overwrite_output_dir \
        --eval_split test \
        --output_dir $OUTDIR/test_model \
        --train_file $LINGMESS_TRAIN \
        --dev_file $LINGMESS_DEV \
        --test_file $LINGMESS_TEST \
        --device cuda:0
    
    # Run unified evaluation to get detailed metrics
    if [ -f "$OUTDIR/test_output.json" ]; then
        log "Test output found. Converting format for unified evaluation..."
        
        # Convert lingmess-coref output to evaluate.py format
        run_step "lingmess-coref format conversion (seed $SEED)" \
          python convert_lingmess_output.py $OUTDIR/test_output.json $LINGMESS_TEST $OUTDIR/test_output_converted.json
        
        log "Running unified evaluation..."
        mkdir -p $OUTDIR/test_eval
        run_step "lingmess-coref unified evaluation (seed $SEED)" \
          python evaluate.py $OUTDIR/test_output_converted.json $OUTDIR/test_eval/
        
        # Show the results
        if [ -f "$OUTDIR/test_eval/overall_F1.json" ]; then
            log "Evaluation completed. Results:"
            cat $OUTDIR/test_eval/overall_F1.json
        fi
    else
        log "ERROR: test_output.json not found after test evaluation."
    fi
else
    log "ERROR: Model directory not found: $BEST_MODEL_DIR"
    log "This means training failed to save a best model."
    exit 1
fi

log "==== Debug complete ====" 
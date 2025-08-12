#!/bin/bash

# Neural Hebrew Coreference Resolution - Unified Experiment Runner
# This script runs both lingmess-coref and wl-coref models for multiple seeds
# Usage: ./run_all_experiments.sh <model_name_or_path>
# Example: ./run_all_experiments.sh onlplab/alephbert-base

set -e  # Exit on any error
cd /workspace/src

# Suppress multiprocessing warnings
export PYTHONWARNINGS="ignore::UserWarning:multiprocessing.resource_tracker"

# Disable mixed precision for CUDA to prevent NaN issues
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128

# CUDA-specific optimizations
export CUDA_LAUNCH_BLOCKING=1
export TORCH_USE_CUDA_DSA=1

# Force PyTorch to use deterministic algorithms
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export TORCH_CUDNN_V8_API_DISABLED=1

# Check if model parameter is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <model_name_or_path>"
    echo "Example: $0 onlplab/alephbert-base"
    exit 1
fi

# Configuration
MODEL_NAME_OR_PATH="$1"  # Model name from command line argument
SEEDS=(42 123 2021 27182 31415)  # Fixed seeds for reproducibility

# Function to determine if model is large
is_large_model() {
    local model_name="$1"
    if [[ "$model_name" == *"large"* ]] || [[ "$model_name" == *"Large"* ]]; then
        return 0  # true
    else
        return 1  # false
    fi
}

# Logging function
log() {    # Print timestamped log messages
    echo "[$(date '+%m/%d/%Y %H:%M:%S')] - $1"
}

# Error handling function - more tolerant of warnings
run_step() {
    local step_name="$1"
    shift
    # shellcheck disable=SC2124
    local cmd="$@"

    log "Starting: $step_name"
    if eval "$cmd" 2>&1 | tee /tmp/step_output.log; then
        log "SUCCESS: $step_name completed successfully."
    else
        local exit_code=$?
        # Check if the failure is just due to multiprocessing warnings
        if grep -q "resource_tracker.*leaked" /tmp/step_output.log && [ $exit_code -eq 255 ]; then
            log "WARNING: $step_name completed with multiprocessing warnings (exit code $exit_code), but continuing..."
            log "SUCCESS: $step_name completed successfully (ignoring multiprocessing warnings)."
        else
            log "ERROR: $step_name failed with exit code $exit_code"
            log "Last 10 lines of output:"
            tail -10 /tmp/step_output.log
            exit 1
        fi
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
LINGMESS_TRAIN=../data/lingmess/hebrew/train.hebrew.jsonlines
LINGMESS_DEV=../data/lingmess/hebrew/dev.hebrew.jsonlines
LINGMESS_TEST=../data/lingmess/hebrew/test.hebrew.jsonlines

# Output directories (relative to workspace/src)
LINGMESS_OUT=../results/lingmess
mkdir -p $LINGMESS_OUT

log "==== Starting experiments for model: $MODEL_NAME_OR_PATH ===="

# Check data files exist
#log "Checking data files..."
check_file "$LINGMESS_TRAIN" "lingmess-coref train file missing."
check_file "$LINGMESS_DEV" "lingmess-coref dev file missing."
check_file "$LINGMESS_TEST" "lingmess-coref test file missing."

# Get optimized hyperparameters based on model size
get_training_params() {
    local model_name="$1"
    if is_large_model "$model_name"; then
        echo "--learning_rate 1e-5 --head_learning_rate 3e-4 --train_epochs 120 --device cuda:0"
    else
        echo "--learning_rate 1e-5 --head_learning_rate 3e-4 --train_epochs 150"
    fi
}

# Check if this is a large model
if is_large_model "$MODEL_NAME_OR_PATH"; then
    log "INFO: Detected large model, using CUDA training with optimized settings"
fi

# Run lingmess-coref 5 times
for SEED in "${SEEDS[@]}"; do
   OUTDIR=$LINGMESS_OUT/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}_model
   mkdir -p $OUTDIR
   log "---- [lingmess-coref] Seed $SEED: Training and dev evaluation ----"
   TRAINING_PARAMS=$(get_training_params "$MODEL_NAME_OR_PATH")
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
       $TRAINING_PARAMS
   log "---- [lingmess-coref] Seed $SEED: Test evaluation ----"
   BEST_MODEL_DIR=$OUTDIR/model
   if [ -d "$BEST_MODEL_DIR" ]; then
    # Ensure test_model directory exists
    mkdir -p $OUTDIR/test_model
    run_step "lingmess-coref test (seed $SEED)" \
      python lingmess-coref/run.py \
        --model_name_or_path $BEST_MODEL_DIR \
        --seed $SEED \
        --output_file $OUTDIR/test_output.json \
        --overwrite_output_dir \
        --eval_split test \
        --output_dir $OUTDIR/test_model \
        --train_file $LINGMESS_TRAIN \
        --dev_file $LINGMESS_DEV \
        --test_file $LINGMESS_TEST \
        $TRAINING_PARAMS
    # Convert lingmess-coref output to evaluate.py format
    run_step "lingmess-coref format conversion (seed $SEED)" \
      python convert_lingmess_output.py $OUTDIR/test_output.json $LINGMESS_TEST $OUTDIR/test_output_converted.json

    # Before evaluation, ensure test_eval directory exists
    mkdir -p $OUTDIR/test_eval
    run_step "lingmess-coref unified evaluation (seed $SEED)" \
      python evaluate.py $OUTDIR/test_output_converted.json $OUTDIR/test_eval/
    log "[lingmess-coref] Seed $SEED: Test evaluation complete."
  else
    log "[ERROR] [lingmess-coref] Seed $SEED: Best model directory not found, skipping test evaluation. Check if training completed successfully."
  fi
done

log "==== All experiments completed. ===="

# Print summary table
python print_experiment_summary.py

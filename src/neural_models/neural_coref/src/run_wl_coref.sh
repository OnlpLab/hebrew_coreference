#!/bin/bash

# Neural Hebrew Coreference Resolution - Unified Experiment Runner
# This script runs both lingmess-coref and wl-coref models for multiple seeds
# Usage: ./run_all_experiments.sh <model_name_or_path>
# Example: ./run_all_experiments.sh onlplab/alephbert-base

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
WL_TEST_INPUT=../data/wl/hebrew/wl_coref_docs/test_head.hebrew.jsonlines

# Output directories (relative to workspace/src)
WLCOREF_OUT=../results/wlcoref
mkdir -p $LINGMESS_OUT $WLCOREF_OUT

log "==== Starting experiments for model: $MODEL_NAME_OR_PATH ===="

# Check data files exist
#log "Checking data files..."
check_file "$WL_TEST_INPUT" "wl-coref test file missing."


# Map model name/path to wl-coref config section
get_wlcoref_section() {
    local model_name="$1"
    case "$model_name" in
        "alephbert-base")
            echo "hebrew_aleph"
            ;;
        "alephbert-large")
            echo "hebrew_aleph_large"
            ;;
        *)
            echo "hebrew_aleph"  # default
            ;;
    esac
}

# Run wl-coref 5 times
for SEED in "${SEEDS[@]}"; do
  OUTDIR=$WLCOREF_OUT/$(basename $MODEL_NAME_OR_PATH)_seed${SEED}
  mkdir -p $OUTDIR
  log "---- [wl-coref] Seed $SEED: Training ----"
  WLCOREF_SECTION=$(get_wlcoref_section "$MODEL_NAME_OR_PATH")
  run_step "wl-coref train (seed $SEED)" \
    python wl-coref/run.py train $WLCOREF_SECTION \
      --config-file wl-coref/config.toml \
      --batch-size 16 \
      --warm-start \
      --seed $SEED \
      --data-dir $OUTDIR \
      --conll-log-dir $OUTDIR/conll_logs \
      --output-dir $OUTDIR
  log "---- [wl-coref] Seed $SEED: Test prediction and evaluation ----"
  run_step "wl-coref test prediction (seed $SEED)" \
    python wl-coref/predict.py $WLCOREF_SECTION $WL_TEST_INPUT $OUTDIR/test_output.json \
      --config-file wl-coref/config.toml \
      --output-dir $OUTDIR \
      --data-dir $OUTDIR \
      --conll-log-dir $OUTDIR/conll_logs \
      --eval-compatible-output $OUTDIR/test_eval_new.json
  # Before evaluation, ensure test_eval directory exists
  mkdir -p $OUTDIR/test_eval
  run_step "wl-coref unified evaluation (seed $SEED)" \
    python evaluate.py $OUTDIR/test_eval_new.json $OUTDIR/test_eval/
  log "[wl-coref] Seed $SEED: Test evaluation complete."
done

log "==== All experiments completed. ===="

# Print summary table
python print_experiment_summary.py

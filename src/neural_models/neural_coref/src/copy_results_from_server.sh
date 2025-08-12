#!/usr/bin/env bash
set -euo pipefail

# ── configuration ──────────────────────────────────────────────────────────────
GCS_PREFIX="gs://p13n-asp-storage1/notebooks/jupyter/s0g0a87/Projects/neural-hebrew-coref/results"
LOCAL_BASE="/Users/s0g0a87/studies/neural_hebrew_coref/results"
MAX_SIZE=$((1024*1024*2))   # 2 MiB
PARALLEL_JOBS=24           # bump up/down to taste

# ── step 1: list every object with its size ────────────────────────────────────
tmp=$(mktemp)
gsutil ls -l -r "${GCS_PREFIX}/**" > "$tmp"

# ── step 2: filter (< MAX_SIZE) and exclude *.conll ─────────────────────────
pairfile=$(mktemp)
awk -v pfx="$GCS_PREFIX/" -v base="$LOCAL_BASE" -v max="$MAX_SIZE" '
  $1 > 0 && $1 < max && $NF !~ /\.conll$/ {
      rel=$NF; sub(pfx,"",rel)
      print $NF                 # src
      print base "/" rel        # dst
  }' "$tmp" > "$pairfile"
rm "$tmp"

# ── step 3: pre‑create destination directories ────────────────────────────────
awk 'NR%2==0' "$pairfile" | xargs -n1 dirname | sort -u | xargs -n1 mkdir -p

# ── step 4: parallel copy (2 args per cp) ──────────────────────────────────────
xargs -n2 -P "$PARALLEL_JOBS" gsutil cp < "$pairfile"

rm "$pairfile"
echo "✅  All files <1 MiB copied to $LOCAL_BASE  (parallel=$PARALLEL_JOBS)"
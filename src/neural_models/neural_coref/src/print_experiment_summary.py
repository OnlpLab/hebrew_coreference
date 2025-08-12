import os
import json
from glob import glob
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import platform
import re

def log(msg, level="INFO"):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{level}] {msg}")

def print_table(headers, rows):
    """Print a simple formatted table without external dependencies"""
    if not rows:
        return
    
    # Calculate column widths
    col_widths = []
    for i, header in enumerate(headers):
        max_width = len(str(header))
        for row in rows:
            max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)
    
    # Print header
    header_line = " | ".join(str(h).ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    
    # Print rows
    for row in rows:
        row_line = " | ".join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        print(row_line)

def extract_metrics_from_data(data):
    """Extract MUC, B³, and CEAF metrics from a single result file"""
    metrics = {}
    
    # Check for lingmess format (nested dictionaries)
    if 'muc' in data and 'muc_f1' in data['muc']:
        try:
            metrics['muc'] = float(data['muc']['muc_f1'])
        except (ValueError, TypeError):
            pass
    
    if 'bcubed' in data and 'bcubed_f1' in data['bcubed']:
        try:
            metrics['bcubed'] = float(data['bcubed']['bcubed_f1'])
        except (ValueError, TypeError):
            pass
    
    if 'ceafe' in data and 'ceafe_f1' in data['ceafe']:
        try:
            metrics['ceafe'] = float(data['ceafe']['ceafe_f1'])
        except (ValueError, TypeError):
            pass
    
    # Check for wl-coref format (Detailed_F1 section with string descriptions)
    if 'Detailed_F1' in data:
        detailed = data['Detailed_F1']
        
        # Extract F-score from string descriptions
        if 'muc' in detailed:
            try:
                # Extract F-score from "Recall: 37.2, Precision: 63.9, F-score:  47.0"
                f_score_str = detailed['muc'].split('F-score:')[1].strip().split('\n')[0]
                metrics['muc'] = float(f_score_str) / 100.0  # Convert percentage to decimal
            except (ValueError, TypeError, IndexError):
                pass
        
        if 'b_cubed' in detailed:
            try:
                f_score_str = detailed['b_cubed'].split('F-score:')[1].strip().split('\n')[0]
                metrics['bcubed'] = float(f_score_str) / 100.0
            except (ValueError, TypeError, IndexError):
                pass
        
        if 'ceafe' in detailed:
            try:
                f_score_str = detailed['ceafe'].split('F-score:')[1].strip().split('\n')[0]
                metrics['ceafe'] = float(f_score_str) / 100.0
            except (ValueError, TypeError, IndexError):
                pass
    
    return metrics

def calculate_avg_metrics_across_seeds(model_metrics):
    """Calculate average of each metric across all seeds for a model/base_model pair"""
    if not model_metrics:
        return None
    
    # Initialize metric sums
    metric_sums = defaultdict(list)
    
    # Collect all metric values across seeds
    for seed_metrics in model_metrics.values():
        for metric_name, value in seed_metrics.items():
            metric_sums[metric_name].append(value)
    
    # Calculate averages
    avg_metrics = {}
    for metric_name, values in metric_sums.items():
        if values:
            avg_metrics[metric_name] = sum(values) / len(values)
    
    return avg_metrics

def get_outdir(model):
    if platform.system() == "Darwin":  # Darwin is macOS
        base = "/Users/s0g0a87/studies/neural_hebrew_coref/results"
    else:  # Assume Linux
        base = "/workspace/results"
    return {
        "lingmess-coref": f"{base}/lingmess",
        "wl-coref": f"{base}/wlcoref"
    }[model]

def extract_base_model_from_dir(dirname):
    # e.g., dictabert_seed42_model -> dictabert
    m = re.match(r"([a-zA-Z0-9\-]+)_seed\d+", dirname)
    if m:
        return m.group(1)
    # fallback: try to get the part before _model
    if "_model" in dirname:
        return dirname.split("_model")[0]
    return dirname

# Group metrics by (model, base_model)
model_metrics = defaultdict(lambda: defaultdict(dict))

# Group SOTA tokenization metrics by (model, base_model) - only for lingmess-coref
sota_model_metrics = defaultdict(lambda: defaultdict(dict))

for model in ["lingmess-coref", "wl-coref"]:
    outdir = get_outdir(model)
    if model == "lingmess-coref":
        # Regular evaluation results
        for path in glob(f"{outdir}/*/result_test.json"):
            parts = Path(path).parts
            # Extract base model and seed from directory name
            base_model = extract_base_model_from_dir(Path(path).parent.name)
            seed = "?"
            for part in parts:
                if "seed" in part:
                    seed = part.split("seed")[-1].split("_")[0]
                    break
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith("c{"):
                        content = content[1:]
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = eval(content)
                metrics = extract_metrics_from_data(data)
                if metrics:
                    model_metrics[(model, base_model)][seed] = metrics
                    log(f"Successfully loaded metrics for {model} {base_model} seed {seed}: {metrics}", level="INFO")
                else:
                    log(f"No valid metrics found in {path}", level="WARNING")
            except Exception as e:
                log(f"Error loading {path}: {e}", level="ERROR")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        log(f"File content (first 200 chars): {content[:200]}", level="ERROR")
                except Exception as read_error:
                    log(f"Could not read file content: {read_error}", level="ERROR")
        
        # SOTA tokenization evaluation results
        for path in glob(f"{outdir}/*_sota_tokenized_eval/result_test.json"):
            parts = Path(path).parts
            # Extract base model and seed from directory name
            dirname = Path(path).parent.name
            # Remove _sota_tokenized_eval suffix to get the base directory name
            base_dirname = dirname.replace("_sota_tokenized_eval", "")
            base_model = extract_base_model_from_dir(base_dirname)
            seed = "?"
            for part in parts:
                if "seed" in part:
                    seed = part.split("seed")[-1].split("_")[0]
                    break
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.startswith("c{"):
                        content = content[1:]
                    try:
                        data = json.loads(content)
                    except json.JSONDecodeError:
                        data = eval(content)
                metrics = extract_metrics_from_data(data)
                if metrics:
                    sota_model_metrics[(model, base_model)][seed] = metrics
                    log(f"Successfully loaded SOTA tokenization metrics for {model} {base_model} seed {seed}: {metrics}", level="INFO")
                else:
                    log(f"No valid SOTA tokenization metrics found in {path}", level="WARNING")
            except Exception as e:
                log(f"Error loading SOTA tokenization {path}: {e}", level="ERROR")
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        log(f"File content (first 200 chars): {content[:200]}", level="ERROR")
                except Exception as read_error:
                    log(f"Could not read file content: {read_error}", level="ERROR")
    elif model == "wl-coref":
        for path in glob(f"{outdir}/*/test_eval_new.json"):
            parts = Path(path).parts
            # Extract base model and seed from directory name
            base_model = extract_base_model_from_dir(Path(path).parent.name)
            seed = "?"
            for part in parts:
                if "seed" in part:
                    seed = part.split("seed")[-1].split("_")[0]
                    break
            test_eval_dir = str(Path(path).parent / "test_eval")
            overall_f1_path = os.path.join(test_eval_dir, "overall_F1.json")
            if os.path.exists(overall_f1_path):
                try:
                    with open(overall_f1_path) as f:
                        data = json.load(f)
                    metrics = extract_metrics_from_data(data)
                    if metrics:
                        model_metrics[(model, base_model)][seed] = metrics
                        log(f"Successfully loaded metrics for {model} {base_model} seed {seed}: {metrics}", level="INFO")
                except Exception as e:
                    log(f"Error loading {overall_f1_path}: {e}", level="ERROR")

# Create detailed results table with individual runs
detailed_results = []
for (model, base_model), seeds_metrics in model_metrics.items():
    for seed, metrics in seeds_metrics.items():
        muc_val = f"{metrics.get('muc', 0)*100:.2f}"
        bcubed_val = f"{metrics.get('bcubed', 0)*100:.2f}"
        ceafe_val = f"{metrics.get('ceafe', 0)*100:.2f}"
        metric_values = list(metrics.values())
        if metric_values:
            overall_avg = sum(metric_values) / len(metric_values)
            overall_str = f"{overall_avg*100:.2f}"
        else:
            overall_str = "N/A"
        detailed_results.append([
            model, 
            base_model,
            seed, 
            overall_str,
            muc_val,
            bcubed_val,
            ceafe_val
        ])

# Create SOTA tokenization detailed results table
sota_detailed_results = []
for (model, base_model), seeds_metrics in sota_model_metrics.items():
    for seed, metrics in seeds_metrics.items():
        muc_val = f"{metrics.get('muc', 0)*100:.2f}"
        bcubed_val = f"{metrics.get('bcubed', 0)*100:.2f}"
        ceafe_val = f"{metrics.get('ceafe', 0)*100:.2f}"
        metric_values = list(metrics.values())
        if metric_values:
            overall_avg = sum(metric_values) / len(metric_values)
            overall_str = f"{overall_avg*100:.2f}"
        else:
            overall_str = "N/A"
        sota_detailed_results.append([
            f"{model} (SOTA)", 
            base_model,
            seed, 
            overall_str,
            muc_val,
            bcubed_val,
            ceafe_val
        ])

# Calculate summary averages across all seeds
summary_results = []
for (model, base_model), seeds_metrics in model_metrics.items():
    if seeds_metrics:
        avg_metrics = calculate_avg_metrics_across_seeds(seeds_metrics)
        if avg_metrics:
            metric_values = list(avg_metrics.values())
            overall_avg = sum(metric_values) / len(metric_values)
            num_seeds = len(seeds_metrics)
            muc_avg = f"{avg_metrics.get('muc', 0)*100:.2f}"
            bcubed_avg = f"{avg_metrics.get('bcubed', 0)*100:.2f}"
            ceafe_avg = f"{avg_metrics.get('ceafe', 0)*100:.2f}"
            overall_avg_str = f"{overall_avg*100:.2f}"
            summary_results.append([
                f"{model} (AVG)",
                base_model,
                f"{num_seeds} seeds", 
                overall_avg_str,
                muc_avg,
                bcubed_avg,
                ceafe_avg
            ])
    else:
        summary_results.append([f"{model} (AVG)", base_model, "No data", "Pending", "Pending", "Pending", "Pending"])

# Calculate SOTA tokenization summary averages across all seeds
sota_summary_results = []
for (model, base_model), seeds_metrics in sota_model_metrics.items():
    if seeds_metrics:
        avg_metrics = calculate_avg_metrics_across_seeds(seeds_metrics)
        if avg_metrics:
            metric_values = list(avg_metrics.values())
            overall_avg = sum(metric_values) / len(metric_values)
            num_seeds = len(seeds_metrics)
            muc_avg = f"{avg_metrics.get('muc', 0)*100:.2f}"
            bcubed_avg = f"{avg_metrics.get('bcubed', 0)*100:.2f}"
            ceafe_avg = f"{avg_metrics.get('ceafe', 0)*100:.2f}"
            overall_avg_str = f"{overall_avg*100:.2f}"
            sota_summary_results.append([
                f"{model} (SOTA AVG)",
                base_model,
                f"{num_seeds} seeds", 
                overall_avg_str,
                muc_avg,
                bcubed_avg,
                ceafe_avg
            ])
    else:
        sota_summary_results.append([f"{model} (SOTA AVG)", base_model, "No data", "Pending", "Pending", "Pending", "Pending"])
        
if not detailed_results and not sota_detailed_results:
    log("No evaluation results found.", level="ERROR")
else:
    # Print summary table first
    log("\n===== SUMMARY TABLE (AVERAGED ACROSS SEEDS) =====\n", level="SUCCESS")
    print_table(["Model", "Base Model", "Seeds", "Overall Avg", "MUC", "B³", "CEAF"], summary_results)
    
    # Print SOTA tokenization summary table
    if sota_summary_results:
        log("\n===== SOTA TOKENIZATION SUMMARY TABLE (AVERAGED ACROSS SEEDS) =====\n", level="SUCCESS")
        print_table(["Model", "Base Model", "Seeds", "Overall Avg", "MUC", "B³", "CEAF"], sota_summary_results)
    
    # Print detailed table with individual runs
    log("\n===== DETAILED RESULTS (INDIVIDUAL RUNS) =====\n", level="SUCCESS")
    print_table(["Model", "Base Model", "Seed", "Overall Avg", "MUC", "B³", "CEAF"], detailed_results)
    
    # Print SOTA tokenization detailed table
    if sota_detailed_results:
        log("\n===== SOTA TOKENIZATION DETAILED RESULTS (INDIVIDUAL RUNS) =====\n", level="SUCCESS")
        print_table(["Model", "Base Model", "Seed", "Overall Avg", "MUC", "B³", "CEAF"], sota_detailed_results)
    
    log("\n========================\n", level="SUCCESS")
#!/usr/bin/env python3
"""
compare_neural.py  —  Compare neural model predictions vs gold annotations for Hebrew-coref.

USAGE
-----
python compare_neural.py \
    --neural /path/to/neural_predictions.json \
    --gold   /path/to/gold_annotations.jsonlines \
    [--doc  htb:232]         # only this doc_key
    [--context 6]            # # tokens around span preview
    [--width 110]            # max line width
    [--metrics]              # show precision/recall/F1 metrics
    [--full-doc]             # show full document with colored clusters
    [--compare-files]        # compare multiple neural result files
    [--show-diff]            # show detailed differences between results
    [--correct-mistaken]     # highlight correct vs mistaken predictions
"""
import argparse
import json
import os
import shutil
from collections import namedtuple, defaultdict
from itertools import zip_longest

Span = namedtuple("Span", ["s", "e"])
CLHDR = "idx │ neural cluster                              │ gold cluster"
SEP = "─" * len(CLHDR)

# Color codes for clusters (using bright colors for better visibility)
try:
    from colorama import Fore, Style, init as color_init
    color_init()
    COLORS = [
        Fore.RED + Style.BRIGHT,           # 0: Bright Red
        Fore.GREEN + Style.BRIGHT,         # 1: Bright Green  
        Fore.YELLOW + Style.BRIGHT,        # 2: Bright Yellow
        Fore.BLUE + Style.BRIGHT,          # 3: Bright Blue
        Fore.MAGENTA + Style.BRIGHT,       # 4: Bright Magenta
        Fore.CYAN + Style.BRIGHT,          # 5: Bright Cyan
        Fore.WHITE + Style.BRIGHT,         # 6: Bright White
        Fore.RED,                          # 7: Normal Red
        Fore.GREEN,                        # 8: Normal Green
        Fore.YELLOW,                       # 9: Normal Yellow
        Fore.BLUE,                         # 10: Normal Blue
        Fore.MAGENTA,                      # 11: Normal Magenta
        Fore.CYAN,                         # 12: Normal Cyan
        Fore.WHITE,                        # 13: Normal White
        # Add more color combinations for better distinction
        Fore.RED + Fore.BLUE,              # 14: Red on Blue
        Fore.GREEN + Fore.BLUE,            # 15: Green on Blue
        Fore.YELLOW + Fore.BLUE,           # 16: Yellow on Blue
        Fore.MAGENTA + Fore.BLUE,          # 17: Magenta on Blue
        Fore.CYAN + Fore.BLUE,             # 18: Cyan on Blue
        Fore.WHITE + Fore.BLUE,            # 19: White on Blue
        Fore.RED + Fore.GREEN,             # 20: Red on Green
        Fore.GREEN + Fore.RED,             # 21: Green on Red
        Fore.YELLOW + Fore.RED,            # 22: Yellow on Red
        Fore.MAGENTA + Fore.RED,           # 23: Magenta on Red
        Fore.CYAN + Fore.RED,              # 24: Cyan on Red
        Fore.WHITE + Fore.RED,             # 25: White on Red
    ]
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
except ImportError:
    # Fallback colors if colorama is not available
    COLORS = [""] * 26  # 26 empty strings for fallback
    RESET = ""
    BOLD = ""

def load_neural_data(result_data_path):
    """Load neural model predictions from JSONLines file."""
    docs = {}
    with open(result_data_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)
            doc_key = item.get("doc_id", item.get("doc_key"))
            if doc_key:
                docs[doc_key] = item
    return docs

def load_llm_data(llm_path):
    """Load LLM predictions from JSONL file with predicted_clusters and gold_clusters."""
    docs = {}
    
    with open(llm_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                doc_key = data.get("doc_key", f"doc_{line_num}")
                
                # Extract predicted and gold clusters
                predicted_clusters = data.get("predicted_clusters", [])
                gold_clusters = data.get("gold_clusters", [])
                
                # Convert to the standard format expected by the script
                doc_data = {
                    "clusters": predicted_clusters,  # Use predicted clusters as neural clusters
                    "doc_key": doc_key
                }
                
                docs[doc_key] = doc_data
                
                # Store gold clusters separately for comparison
                docs[f"{doc_key}_gold"] = {
                    "clusters": gold_clusters,
                    "doc_key": f"{doc_key}_gold"
                }
                
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse line {line_num} in {llm_path}: {e}")
                continue
            except Exception as e:
                print(f"Warning: Error processing line {line_num} in {llm_path}: {e}")
                continue
    
    return docs

def load_conllu_data(conllu_path):
    """Load gold annotations from CONLLU file."""
    docs = {}
    
    with open(conllu_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Split into documents
    document_sections = content.split("#begin document")
    
    for i, section in enumerate(document_sections[1:], 1):  # Skip first empty section
        lines = section.strip().split('\n')
        if not lines:
            continue
        
        # Extract document key from first line (e.g., "#begin document 107" -> "107")
        first_line = lines[0]
        doc_key = first_line.strip()
        
        # If the doc_key is just a number, try to use the filename instead
        if doc_key.isdigit():
            # Extract filename from the path and use it as document key
            filename = os.path.basename(conllu_path)
            if filename.endswith('.conllu'):
                filename = filename[:-7]  # Remove .conllu extension
            doc_key = filename
        
        clusters = {}
        tokens = []
        current_sentence = []
        
        # Parse CONLLU format
        for line in lines[1:]:
            if line.startswith('#') or not line.strip():
                # End of sentence, add to tokens
                if current_sentence:
                    tokens.extend(current_sentence)
                    current_sentence = []
                continue
            
            parts = line.split('\t')
            if len(parts) < 5:  # Need at least 5 columns
                continue
            
            try:
                sentence_id = int(parts[1])  # Sentence ID is in 2nd column
                token_id = int(parts[2])     # Token ID within sentence is in 3rd column
                token_text = parts[0]        # Token text is in 1st column
                coref_info = parts[4]        # Coreference info is in 5th column
                
                # Add token to current sentence
                current_sentence.append(token_text)
                
                # Parse coreference information
                if coref_info != '_':
                    # Handle multiple cluster assignments (e.g., "(0|(1")
                    cluster_parts = coref_info.strip('()').split('|')
                    for part in cluster_parts:
                        if part.startswith('('):
                            part = part[1:]  # Remove opening parenthesis
                        if part.endswith(')'):
                            part = part[:-1]  # Remove closing parenthesis
                        
                        if part.isdigit():
                            cluster_id = int(part)
                            if cluster_id not in clusters:
                                clusters[cluster_id] = []
                            # Calculate global token index
                            global_token_idx = len(tokens) + len(current_sentence) - 1
                            clusters[cluster_id].append([global_token_idx, global_token_idx + 1])
            except (ValueError, IndexError) as e:
                continue
        
        # Add any remaining tokens from the last sentence
        if current_sentence:
            tokens.extend(current_sentence)
        
        # Convert to standard format
        cluster_list = list(clusters.values())
        docs[doc_key] = {
            "clusters": cluster_list,
            "doc_key": doc_key,
            "tokens": tokens,  # Add the actual text tokens
            "cased_words": tokens  # For compatibility with existing code
        }
    
    return docs

def detect_file_format(file_path):
    """Detect the format of the input file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            
        # Try to parse as JSON
        data = json.loads(first_line)
        
        # Check if it's LLM format
        if "predicted_clusters" in data and "gold_clusters" in data:
            return "llm"
        # Check if it's neural format
        elif "clusters" in data and "cased_words" in data:
            return "neural"
        else:
            return "unknown"
            
    except (json.JSONDecodeError, UnicodeDecodeError):
        # Check if it's CONLLU format
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("#begin document") or first_line.startswith("#"):
                    return "conllu"
        except:
            pass
    
    return "unknown"

def load_data_smart(file_path):
    """Automatically detect and load data in the appropriate format."""
    file_format = detect_file_format(file_path)
    
    if file_format == "llm":
        return load_llm_data(file_path)
    elif file_format == "neural":
        return load_neural_data(file_path)
    elif file_format == "conllu":
        return load_conllu_data(file_path)
    else:
        raise ValueError(f"Unknown file format for {file_path}. Supported formats: LLM (JSONL with predicted_clusters), Neural (JSONL with clusters), CONLLU")

def load_gold_data(gold_data_path):
    """Load gold annotations from JSONLines file."""
    docs = {}
    with open(gold_data_path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            doc_key = d.get("doc_key", d.get("doc_id"))
            if doc_key:
                docs[doc_key] = d
    return docs

def spans_of_cluster(cl):
    """Convert cluster to list of Span tuples."""
    return [Span(s, e) for s, e in cl]

def cluster_key(cl):
    """(min_start, max_end) for ordering clusters."""
    if not cl:
        return (0, 0)
    starts = [s for s, _ in cl]
    ends = [e for _, e in cl]
    return (min(starts), max(ends))

def preview(tokens, span, ctx):
    """Return a short preview for one span."""
    # Handle both list and tuple spans
    if isinstance(span, (list, tuple)) and len(span) == 2:
        s, e = span
        left = " ".join(tokens[max(0, s - ctx): s])
        mid = " ".join(tokens[s:e])
        right = " ".join(tokens[e:e + ctx])
        return f"... {left} >>>{mid}<<< {right} ..."
    else:
        return f"... >>>{str(span)}<<< ..."

def format_cluster(tokens, cl, ctx, width):
    """Format a cluster for display."""
    if not cl:
        return "—"
    # Handle spans that might be lists or tuples
    spans_txt = ", ".join(f"[{s},{e}]" for s, e in cl if isinstance((s, e), (list, tuple)) and len((s, e)) == 2)
    # pick the span with the earliest start for preview
    if cl:
        first_span = min(cl, key=lambda x: x[0] if isinstance(x, (list, tuple)) and len(x) == 2 else 0)
        sneak = preview(tokens, first_span, ctx)
        txt = f"{spans_txt}  {sneak}"
        return (txt[:width - 3] + "…") if len(txt) > width else txt
    return "—"

def words(tokens, span):
    """Get words for a span."""
    # Handle both list and tuple spans
    if isinstance(span, (list, tuple)) and len(span) == 2:
        s, e = span
        return " ".join(tokens[s:e])
    else:
        return str(span)

def calculate_metrics(neural_doc, gold_doc):
    """Calculate precision, recall, and F1 for cluster matching."""
    # Convert to sets of spans for comparison
    neural_spans = set()
    for cl in neural_doc.get("clusters", []):
        # Convert spans to tuples for hashing
        for span in cl:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                neural_spans.add(tuple(span))
    
    gold_spans = set()
    for cl in gold_doc.get("clusters", []):
        # Convert spans to tuples for hashing
        for span in cl:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                gold_spans.add(tuple(span))
    
    # Calculate metrics
    correct = len(neural_spans & gold_spans)
    predicted = len(neural_spans)
    actual = len(gold_spans)
    
    precision = correct / predicted if predicted > 0 else 0
    recall = correct / actual if actual > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'correct_spans': correct,
        'predicted_spans': predicted,
        'actual_spans': actual,
        'neural_spans': neural_spans,
        'gold_spans': gold_spans
    }

def jaccard_similarity(set1, set2):
    """Calculate Jaccard similarity between two sets."""
    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0

def analyze_predictions(neural_doc, gold_doc):
    """Analyze which predictions are correct vs mistaken at the cluster level."""
    neural_clusters = neural_doc.get("clusters", [])
    gold_clusters = gold_doc.get("clusters", [])
    
    # Convert clusters to sets of spans for comparison
    neural_cluster_spans = []
    for cl in neural_clusters:
        spans = set()
        for span in cl:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                spans.add(tuple(span))
        neural_cluster_spans.append(spans)
    
    gold_cluster_spans = []
    for cl in gold_clusters:
        spans = set()
        for span in cl:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                spans.add(tuple(span))
        gold_cluster_spans.append(spans)
    
    # Find best cluster matches using Jaccard similarity
    # Create similarity matrix
    similarity_matrix = []
    for neural_spans in neural_cluster_spans:
        row = []
        for gold_spans in gold_cluster_spans:
            similarity = jaccard_similarity(neural_spans, gold_spans)
            row.append(similarity)
        similarity_matrix.append(row)
    
    # Find best matches using greedy assignment
    matched_neural = set()
    matched_gold = set()
    cluster_matches = []
    
    # Sort by similarity (highest first)
    all_pairs = []
    for i, neural_spans in enumerate(neural_cluster_spans):
        for j, gold_spans in enumerate(gold_cluster_spans):
            similarity = similarity_matrix[i][j]
            if similarity > 0:  # Only consider non-zero similarities
                all_pairs.append((similarity, i, j))
    
    all_pairs.sort(reverse=True)  # Highest similarity first
    
    # Greedy assignment
    for similarity, neural_idx, gold_idx in all_pairs:
        if neural_idx not in matched_neural and gold_idx not in matched_gold:
            matched_neural.add(neural_idx)
            matched_gold.add(gold_idx)
            cluster_matches.append({
                'neural_idx': neural_idx,
                'gold_idx': gold_idx,
                'similarity': similarity,
                'neural_spans': neural_cluster_spans[neural_idx],
                'gold_spans': gold_cluster_spans[gold_idx]
            })
    
    # Categorize clusters
    correct_clusters = []
    extra_clusters = []
    missed_clusters = []
    
    # Correct matches (high similarity)
    for match in cluster_matches:
        if match['similarity'] >= 0.5:  # Threshold for considering a match correct
            correct_clusters.append(match)
        else:
            # Low similarity matches - could be partial or incorrect
            extra_clusters.append(match)
    
    # Extra clusters (neural clusters not matched to gold)
    for i, neural_spans in enumerate(neural_cluster_spans):
        if i not in matched_neural:
            extra_clusters.append({
                'neural_idx': i,
                'gold_idx': None,
                'similarity': 0.0,
                'neural_spans': neural_spans,
                'gold_spans': set()
            })
    
    # Missed clusters (gold clusters not matched to neural)
    for i, gold_spans in enumerate(gold_cluster_spans):
        if i not in matched_gold:
            missed_clusters.append({
                'neural_idx': None,
                'gold_idx': i,
                'similarity': 0.0,
                'neural_spans': set(),
                'gold_spans': gold_spans
            })
    
    return {
        'correct_clusters': correct_clusters,
        'extra_clusters': extra_clusters,
        'missed_clusters': missed_clusters,
        'total_correct': len(correct_clusters),
        'total_extra': len(extra_clusters),
        'total_missed': len(missed_clusters),
        'cluster_matches': cluster_matches,
        'similarity_matrix': similarity_matrix
    }

def get_cluster_color(cluster_idx, total_clusters):
    """Get a color for a cluster with better contrast distribution."""
    if total_clusters <= len(COLORS):
        # If we have enough colors, use them directly
        return COLORS[cluster_idx]
    else:
        # For many clusters, use a more sophisticated distribution
        # This creates better contrast by spacing colors out
        if cluster_idx < len(COLORS):
            return COLORS[cluster_idx]
        else:
            # For clusters beyond our color palette, cycle with offset
            # This creates better visual separation
            offset = (cluster_idx // len(COLORS)) * 3
            adjusted_idx = (cluster_idx + offset) % len(COLORS)
            return COLORS[adjusted_idx]

def display_full_document(neural_doc, gold_doc):
    """Display full document with colored clusters."""
    print(f"\n{'='*80}")
    print(f"{BOLD}FULL DOCUMENT COMPARISON{RESET}")
    print(f"{'='*80}")
    
    # Check text availability
    neural_has_text = neural_doc.get("cased_words") or neural_doc.get("tokens")
    gold_has_text = gold_doc.get("cased_words") or gold_doc.get("tokens")
    
    # Get tokens
    neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
    gold_tokens = gold_doc.get("cased_words", gold_doc.get("tokens", []))
    
    # Get clusters
    neural_clusters = neural_doc.get("clusters", [])
    gold_clusters = gold_doc.get("clusters", [])
    
    # Color scheme
    total_clusters = max(len(neural_clusters), len(gold_clusters))
    print(f"Color scheme: Each cluster gets a unique color (total: {total_clusters} clusters)")
    
    # Create span maps for neural clusters
    neural_span_map = {}
    for i, cluster in enumerate(neural_clusters):
        color = get_cluster_color(i, total_clusters)
        for span in cluster:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                s, e = span
                # Handle LLM vs CONLLU span differences
                # LLM typically uses [start, start] for single tokens
                # CONLLU uses [start, end) where end is exclusive
                if s == e:  # LLM single token format
                    span_key = (s, s)
                else:  # CONLLU range format
                    span_key = (s, e)
                neural_span_map[span_key] = (i, color)
    
    # Create span maps for gold clusters
    gold_span_map = {}
    for i, cluster in enumerate(gold_clusters):
        color = get_cluster_color(i, total_clusters)
        for span in cluster:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                s, e = span
                span_key = (s, e)
                gold_span_map[span_key] = (i, color)
    
    # Display neural predictions
    print(f"\n{COLORS[1]}{BOLD}NEURAL PREDICTIONS:{RESET}")
    print(f"{'─'*40}")
    
    if neural_has_text:
        # Display with text content
        for i, token in enumerate(neural_tokens):
            span_key = (i, i)
            if span_key in neural_span_map:
                cluster_idx, color = neural_span_map[span_key]
                print(f"{color}[{token}]{RESET}", end=" ")
            else:
                print(token, end=" ")
    else:
        # Display with span indices only
        print("(LLM file - no text content available)")
        print("Showing span indices only:")
        for i, cluster in enumerate(neural_clusters):
            color = get_cluster_color(i, total_clusters)
            spans_text = []
            for span in cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    if s == e:
                        spans_text.append(f"[{s}]")
                    else:
                        spans_text.append(f"[{s},{e}]")
            print(f"{color}Cluster {i}: {', '.join(spans_text)}{RESET}")
    
    # Display gold annotations
    print(f"\n\n{COLORS[2]}{BOLD}GOLD ANNOTATIONS:{RESET}")
    print(f"{'─'*40}")
    
    if gold_has_text:
        # Display with text content
        for i, token in enumerate(gold_tokens):
            span_key = (i, i)
            if span_key in gold_span_map:
                cluster_idx, color = gold_span_map[span_key]
                print(f"{color}[{token}]{RESET}", end=" ")
            else:
                print(token, end=" ")
    else:
        print("(No text content available)")
    
    # Display cluster legend
    print(f"\n\n{COLORS[3]}{BOLD}CLUSTER LEGEND:{RESET}")
    print(f"{'─'*40}")
    
    # Neural clusters
    print(f"{BOLD}Neural Clusters:{RESET}")
    for i, cluster in enumerate(neural_clusters):
        color = get_cluster_color(i, total_clusters)
        spans_text = []
        cluster_text = []
        for span in cluster:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                s, e = span
                if s == e:  # LLM single token format
                    spans_text.append(f"[{s}]")
                    # Try to get text from gold tokens if available
                    if gold_has_text and 0 <= s < len(gold_tokens):
                        cluster_text.append(gold_tokens[s])
                    else:
                        cluster_text.append("(no text)")
                else:  # CONLLU range format
                    spans_text.append(f"[{s},{e}]")
                    if gold_has_text and 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                        cluster_text.append(" ".join(gold_tokens[s:e]))
                    else:
                        cluster_text.append("(no text)")
        
        text_display = " → " + " | ".join(cluster_text) if cluster_text else " → (no text)"
        print(f"  {color}Cluster {i}: {', '.join(spans_text)}{text_display}{RESET}")
    
    # Gold clusters
    print(f"\n{BOLD}Gold Clusters:{RESET}")
    for i, cluster in enumerate(gold_clusters):
        color = get_cluster_color(i, total_clusters)
        spans_text = []
        cluster_text = []
        for span in cluster:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                s, e = span
                spans_text.append(f"[{s},{e}]")
                
                # Try to get text if available
                if gold_has_text:
                    if 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                        cluster_text.append(" ".join(gold_tokens[s:e]))
                    else:
                        cluster_text.append("(no text)")
                else:
                    cluster_text.append("(no text)")
        
        text_display = " → " + " | ".join(cluster_text) if cluster_text else " → (no text)"
        print(f"  {color}Cluster {i}: {', '.join(spans_text)}{text_display}{RESET}")

def display_prediction_analysis(neural_doc, gold_doc):
    """Display detailed analysis of correct vs mistaken predictions at cluster level."""
    analysis = analyze_predictions(neural_doc, gold_doc)
    neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
    gold_tokens = gold_doc.get("cased_words", gold_doc.get("tokens", []))
    
    print(f"\n{'='*80}")
    print(f"{BOLD}CLUSTER-LEVEL PREDICTION ANALYSIS{RESET}")
    print(f"{'='*80}")
    
    print(f"\n{BOLD}Summary:{RESET}")
    print(f"  ✅ Correct clusters: {analysis['total_correct']}")
    print(f"  ❌ Extra clusters: {analysis['total_extra']}")
    print(f"  🔍 Missed clusters: {analysis['total_missed']}")
    
    # Show correct clusters
    if analysis['correct_clusters']:
        print(f"\n{BOLD}✅ CORRECT CLUSTERS (High Similarity):{RESET}")
        print(f"{'─'*70}")
        for match in analysis['correct_clusters']:
            neural_idx = match['neural_idx']
            gold_idx = match['gold_idx']
            similarity = match['similarity']
            
            # Get cluster words
            neural_words = []
            for span in sorted(match['neural_spans']):
                s, e = span
                words_text = " ".join(neural_tokens[s:e])
                neural_words.append(f"[{s},{e}] {words_text}")
            
            gold_words = []
            for span in sorted(match['gold_spans']):
                s, e = span
                words_text = " ".join(gold_tokens[s:e])
                gold_words.append(f"[{s},{e}] {words_text}")
            
            print(f"  Neural Cluster {neural_idx} ↔ Gold Cluster {gold_idx} (Similarity: {similarity:.3f})")
            print(f"    Neural: {' | '.join(neural_words)}")
            print(f"    Gold:   {' | '.join(gold_words)}")
            print()
    
    # Show extra clusters (neural clusters not well matched)
    if analysis['extra_clusters']:
        print(f"\n{BOLD}❌ EXTRA/INCORRECT CLUSTERS:{RESET}")
        print(f"{'─'*70}")
        for match in analysis['extra_clusters']:
            neural_idx = match['neural_idx']
            gold_idx = match['gold_idx']
            similarity = match['similarity']
            
            # Get cluster words
            neural_words = []
            for span in sorted(match['neural_spans']):
                s, e = span
                words_text = " ".join(neural_tokens[s:e])
                neural_words.append(f"[{s},{e}] {words_text}")
            
            if gold_idx is not None:
                # Low similarity match
                gold_words = []
                for span in sorted(match['gold_spans']):
                    s, e = span
                    words_text = " ".join(gold_tokens[s:e])
                    gold_words.append(f"[{s},{e}] {words_text}")
                
                print(f"  Neural Cluster {neural_idx} ↔ Gold Cluster {gold_idx} (Low Similarity: {similarity:.3f})")
                print(f"    Neural: {' | '.join(neural_words)}")
                print(f"    Gold:   {' | '.join(gold_words)}")
            else:
                # Completely unmatched
                print(f"  Neural Cluster {neural_idx} (No Gold Match)")
                print(f"    Spans: {' | '.join(neural_words)}")
            print()
    
    # Show missed clusters (gold clusters not matched)
    if analysis['missed_clusters']:
        print(f"\n{BOLD}🔍 MISSED CLUSTERS (In Gold, Not Predicted):{RESET}")
        print(f"{'─'*70}")
        for match in analysis['missed_clusters']:
            gold_idx = match['gold_idx']
            
            # Get cluster words
            gold_words = []
            for span in sorted(match['gold_spans']):
                s, e = span
                words_text = " ".join(gold_tokens[s:e])
                gold_words.append(f"[{s},{e}] {words_text}")
            
            print(f"  Gold Cluster {gold_idx} (No Neural Match)")
            print(f"    Spans: {' | '.join(gold_words)}")
            print()
    
    # Show similarity matrix for debugging
    if analysis['similarity_matrix']:
        print(f"\n{BOLD}📊 CLUSTER SIMILARITY MATRIX:{RESET}")
        print(f"{'─'*70}")
        print("      ", end="")
        for j in range(len(analysis['similarity_matrix'][0])):
            print(f"Gold{j:>6}", end="")
        print()
        
        for i, row in enumerate(analysis['similarity_matrix']):
            print(f"Neural{i:>2}", end="")
            for similarity in row:
                if similarity > 0.5:
                    print(f"{COLORS[1]}{similarity:>6.3f}{RESET}", end="")
                elif similarity > 0.1:
                    print(f"{COLORS[2]}{similarity:>6.3f}{RESET}", end="")
                else:
                    print(f"{similarity:>6.3f}", end="")
            print()

def calculate_metrics_word_level(neural_doc, gold_doc):
    """Calculate precision, recall, and F1 using word-level comparison instead of index-level."""
    neural_clusters = neural_doc.get("clusters", [])
    gold_clusters = gold_doc.get("clusters", [])
    
    # Convert clusters to sets of word sequences for comparison
    neural_word_sets = []
    for cluster in neural_clusters:
        word_set = set()
        for span in cluster:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                s, e = span
                neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
                if 0 <= s < len(neural_tokens) and 0 <= e <= len(neural_tokens):
                    span_text = " ".join(neural_tokens[s:e])
                    word_set.add(span_text)
        if word_set:
            neural_word_sets.append(word_set)
    
    gold_word_sets = []
    for cluster in gold_clusters:
        word_set = set()
        for span in cluster:
            if isinstance(span, (list, tuple)) and len(span) == 2:
                s, e = span
                gold_tokens = gold_doc.get("cased_words", gold_doc.get("tokens", []))
                if 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                    span_text = " ".join(gold_tokens[s:e])
                    word_set.add(span_text)
        if word_set:
            gold_word_sets.append(word_set)
    
    # Use the weighted similarity analysis to get proper cluster-level metrics
    analysis = analyze_predictions_word_level(neural_doc, gold_doc)
    
    # Calculate metrics based on cluster-level analysis
    correct_clusters = analysis['total_correct']
    extra_clusters = analysis['total_extra'] 
    missed_clusters = analysis['total_missed']
    
    # Precision = correct / (correct + extra)
    precision = correct_clusters / (correct_clusters + extra_clusters) if (correct_clusters + extra_clusters) > 0 else 0.0
    
    # Recall = correct / (correct + missed)
    recall = correct_clusters / (correct_clusters + missed_clusters) if (correct_clusters + missed_clusters) > 0 else 0.0
    
    # F1 = 2 * precision * recall / (precision + recall)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'correct_clusters': correct_clusters,
        'extra_clusters': extra_clusters,
        'missed_clusters': missed_clusters
    }

def is_pronoun(text):
    """Check if a text span is a pronoun."""
    # Hebrew pronouns only - these are the actual pronouns that should get lower weight
    hebrew_pronouns = {
        # Personal pronouns
        'הוא', 'היא', 'הם', 'הן', 'אני', 'אתה', 'את', 'אנחנו', 'אתם', 'אתן',
        # Demonstrative pronouns
        'זה', 'זו', 'אלה', 'אלו', 'הזה', 'הזו', 'האלה', 'האלו',
        # Possessive pronouns
        'שלו', 'שלה', 'שלהם', 'שלהן', 'שלי', 'שלך', 'שלכם', 'שלכן', 'שלנו',
        # Relative pronouns
        'ש', 'אשר',
        # Interrogative pronouns
        'מי', 'מה', 'איזה', 'איזו', 'איזהו', 'איזוהו',
        # Indefinite pronouns
        'כולם', 'כולן', 'כלום', 'שום', 'איש', 'אף אחד', 'מישהו', 'משהו'
    }
    
    # Strip underscores before checking (common in neural model outputs)
    cleaned_text = text.replace('_', '')
    
    # Only classify as pronoun if it's exactly a known Hebrew pronoun
    return cleaned_text in hebrew_pronouns

def calculate_weighted_similarity(neural_words, gold_words):
    """Calculate weighted similarity giving less weight to pronouns and short mentions."""
    if not neural_words and not gold_words:
        return 1.0
    if not neural_words or not gold_words:
        return 0.0
    
    # Separate pronouns and content words
    neural_pronouns = {w for w in neural_words if is_pronoun(w)}
    neural_content = neural_words - neural_pronouns
    gold_pronouns = {w for w in gold_words if is_pronoun(w)}
    gold_content = gold_words - gold_pronouns
    
    # Calculate weighted scores
    pronoun_weight = 0.2  # Pronouns get much lower weight
    content_weight = 1.0  # Content words get full weight
    
    # Content word similarity (most important)
    if neural_content and gold_content:
        content_intersection = len(neural_content & gold_content)
        content_union = len(neural_content | gold_content)
        content_similarity = content_intersection / content_union if content_union > 0 else 0.0
    else:
        content_similarity = 0.0
    
    # Pronoun similarity (less important)
    if neural_pronouns and gold_pronouns:
        pronoun_intersection = len(neural_pronouns & gold_pronouns)
        pronoun_union = len(neural_pronouns | gold_pronouns)
        pronoun_similarity = pronoun_intersection / pronoun_union if pronoun_union > 0 else 0.0
    else:
        pronoun_similarity = 0.0
    
    # Weighted combination
    total_weight = content_weight + pronoun_weight
    weighted_similarity = (content_weight * content_similarity + pronoun_weight * pronoun_similarity) / total_weight
    
    return weighted_similarity

def analyze_predictions_word_level(neural_doc, gold_doc):
    """Analyze predictions using word-level comparison with fallback to span-based similarity."""
    neural_clusters = neural_doc.get("clusters", [])
    gold_clusters = gold_doc.get("clusters", [])
    
    # Check if we have text content for word-level analysis
    neural_has_text = neural_doc.get("cased_words") or neural_doc.get("tokens")
    gold_has_text = gold_doc.get("cased_words") or neural_doc.get("tokens", [])
    
    # If gold has text, we can do word-level analysis even if neural doesn't
    if gold_has_text:
        # Use word-level comparison with weighted similarity
        return analyze_predictions_with_weighted_similarity(neural_doc, gold_doc)
    else:
        # Fall back to span-based similarity (for LLM files without text)
        return analyze_predictions_span_based(neural_doc, gold_doc)

def analyze_predictions_span_based(neural_doc, gold_doc):
    """Analyze predictions using span-based similarity when text is not available."""
    neural_clusters = neural_doc.get("clusters", [])
    gold_clusters = gold_doc.get("clusters", [])
    
    # Get tokens for content-based matching
    neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
    gold_tokens = gold_doc.get("cased_words", gold_doc.get("tokens", []))
    
    # Calculate similarity matrix based on content overlap and position proximity
    similarity_matrix = []
    for neural_cluster in neural_clusters:
        row = []
        for gold_cluster in gold_clusters:
            # Convert clusters to sets of spans and text content
            neural_spans = set()
            neural_texts = set()
            for span in neural_cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    if s == e:  # LLM single token format [39,39]
                        neural_spans.add((s, s))
                        # Try to get text from neural tokens first, then from gold tokens
                        if 0 <= s < len(neural_tokens):
                            neural_texts.add(neural_tokens[s])
                        elif 0 <= s < len(gold_tokens):
                            neural_texts.add(gold_tokens[s])
                    else:  # CONLLU range format [39,40]
                        neural_spans.add((s, e))
                        # Try to get text from neural tokens first, then from gold tokens
                        if 0 <= s < len(neural_tokens) and 0 <= e <= len(neural_tokens):
                            neural_texts.add(" ".join(neural_tokens[s:e]))
                        elif 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                            neural_texts.add(" ".join(gold_tokens[s:e]))
            
            gold_spans = set()
            gold_texts = set()
            for span in gold_cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    gold_spans.add((s, e))
                    if 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                        gold_texts.add(" ".join(gold_tokens[s:e]))
            
            if neural_texts and gold_texts:
                # Calculate content-based similarity
                text_intersection = len(neural_texts & gold_texts)
                text_union = len(neural_texts | gold_texts)
                text_similarity = text_intersection / text_union if text_union > 0 else 0.0
                
                # Check if there's at least one exact content word match (not a pronoun)
                has_content_match = False
                for text in neural_texts:
                    if text in gold_texts and not is_pronoun(text):
                        has_content_match = True
                        break
                
                # Calculate position-based similarity (more forgiving)
                position_similarity = 0.0
                if neural_spans and gold_spans:
                    # Count spans that are close or overlapping
                    close_spans = 0
                    for n_span in neural_spans:
                        for g_span in gold_spans:
                            # Check if spans overlap or are very close
                            if (n_span[0] <= g_span[1] and n_span[1] >= g_span[0]) or \
                               abs(n_span[0] - g_span[0]) <= 1 or abs(n_span[1] - g_span[1]) <= 1:
                                close_spans += 1
                    
                    if close_spans > 0:
                        position_similarity = close_spans / max(len(neural_spans), len(gold_spans))
                
                # Combine similarities (give more weight to content)
                similarity = 0.8 * text_similarity + 0.2 * position_similarity
                
                # Additional requirement: minimum content overlap
                min_content_overlap = 0.3  # At least 30% of content should overlap
                if text_similarity < min_content_overlap:
                    similarity *= 0.5  # Penalize low content overlap
                
                # Critical requirement: must have at least one content word match
                if not has_content_match:
                    similarity *= 0.3  # Heavily penalize clusters with no content word matches
            elif gold_texts:
                # Neural has no text but gold does - try to extract text from neural spans using gold tokens
                neural_texts_from_gold = set()
                for span in neural_cluster:
                    if isinstance(span, (list, tuple)) and len(span) == 2:
                        s, e = span
                        if s == e:  # LLM single token format [39,39]
                            if 0 <= s < len(gold_tokens):
                                neural_texts_from_gold.add(gold_tokens[s])
                        else:  # CONLLU range format [39,40]
                            if 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                                neural_texts_from_gold.add(" ".join(gold_tokens[s:e]))
                
                if neural_texts_from_gold and gold_texts:
                    # Calculate content-based similarity using gold-derived neural text
                    text_intersection = len(neural_texts_from_gold & gold_texts)
                    text_union = len(neural_texts_from_gold | gold_texts)
                    text_similarity = text_intersection / text_union if text_union > 0 else 0.0
                    
                    # Check if there's at least one exact content word match (not a pronoun)
                    has_content_match = False
                    content_matches = []
                    for text in neural_texts_from_gold:
                        if text in gold_texts and not is_pronoun(text):
                            has_content_match = True
                            content_matches.append(text)
                            break
                    
                    # Calculate position-based similarity
                    position_similarity = 0.0
                    if neural_spans and gold_spans:
                        close_spans = 0
                        for n_span in neural_spans:
                            for g_span in gold_spans:
                                if (n_span[0] <= g_span[1] and n_span[1] >= g_span[0]) or \
                                   abs(n_span[0] - g_span[0]) <= 1 or abs(n_span[1] - g_span[1]) <= 1:
                                    close_spans += 1
                        
                        if close_spans > 0:
                            position_similarity = close_spans / max(len(neural_spans), len(gold_spans))
                    
                    # Combine similarities
                    similarity = 0.8 * text_similarity + 0.2 * position_similarity
                    
                    # Additional requirements
                    min_content_overlap = 0.3
                    if text_similarity < min_content_overlap:
                        similarity *= 0.5
                    
                    if not has_content_match:
                        similarity *= 0.3
                    
                    # Debug output for problematic matches

                else:
                    # Fallback to span overlap
                    similarity = 0.0
                    if neural_spans and gold_spans:
                        overlap = 0
                        total_neural = len(neural_spans)
                        total_gold = len(gold_spans)
                        
                        for n_span in neural_spans:
                            for g_span in gold_spans:
                                if (n_span[0] <= g_span[1] and n_span[1] >= g_span[0]) or \
                                   abs(n_span[0] - g_span[0]) <= 1 or abs(n_span[1] - g_span[1]) <= 1:
                                    overlap += 1
                        
                        if total_neural > 0 and total_gold > 0:
                            similarity = overlap / max(total_neural, total_gold)
            else:
                # Fallback to span overlap if no text available
                if neural_spans and gold_spans:
                    overlap = 0
                    total_neural = len(neural_spans)
                    total_gold = len(gold_spans)
                    
                    for n_span in neural_spans:
                        for g_span in gold_spans:
                            # Check if spans overlap or are close
                            if (n_span[0] <= g_span[1] and n_span[1] >= g_span[0]) or \
                               abs(n_span[0] - g_span[0]) <= 1 or abs(n_span[1] - g_span[1]) <= 1:
                                overlap += 1
                    
                    if total_neural > 0 and total_gold > 0:
                        similarity = overlap / max(total_neural, total_gold)
                    else:
                        similarity = 0.0
                else:
                    similarity = 0.0
            row.append(similarity)
        similarity_matrix.append(row)
    
    # Find best matches using greedy assignment with lower threshold
    correct_clusters = []
    extra_clusters = []
    missed_clusters = []
    
    # Track which gold clusters have been matched
    matched_gold = set()
    
    # Find correct matches (more forgiving threshold)
    for neural_idx, row in enumerate(similarity_matrix):
        best_gold_idx = max(range(len(row)), key=lambda i: row[i])
        best_similarity = row[best_gold_idx]
        
        if best_similarity >= 0.4 and best_gold_idx not in matched_gold:  # Higher threshold for more strict matching
            correct_clusters.append({
                'neural_idx': neural_idx,
                'gold_idx': best_gold_idx,
                'similarity': best_similarity
            })
            matched_gold.add(best_gold_idx)
        else:
            extra_clusters.append({
                'neural_idx': neural_idx,
                'similarity': best_similarity
            })
    
    # Find missed clusters
    for gold_idx in range(len(gold_clusters)):
        if gold_idx not in matched_gold:
            missed_clusters.append({
                'gold_idx': gold_idx
            })
    
    return {
        'correct_clusters': correct_clusters,
        'extra_clusters': extra_clusters,
        'missed_clusters': missed_clusters,
        'total_correct': len(correct_clusters),
        'total_extra': len(extra_clusters),
        'total_missed': len(missed_clusters),
        'similarity_matrix': similarity_matrix
    }

def analyze_predictions_with_weighted_similarity(neural_doc, gold_doc):
    """Analyze predictions using word-level comparison with weighted similarity."""
    neural_clusters = neural_doc.get("clusters", [])
    gold_clusters = gold_doc.get("clusters", [])
    
    # Check text availability
    neural_has_text = neural_doc.get("cased_words") or neural_doc.get("tokens")
    gold_has_text = gold_doc.get("cased_words") or neural_doc.get("tokens")
    
    # Get tokens for content-based matching
    neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
    gold_tokens = gold_doc.get("cased_words", neural_doc.get("tokens", []))
    
    # Calculate similarity matrix
    similarity_matrix = []
    for neural_idx, neural_cluster in enumerate(neural_clusters):
        row = []
        for gold_idx, gold_cluster in enumerate(gold_clusters):
            if gold_has_text:
                # Use content-based comparison with weighted similarity
                # Convert clusters to sets of spans and text content
                neural_spans = set()
                neural_texts = set()
                for span in neural_cluster:
                    if isinstance(span, (list, tuple)) and len(span) == 2:
                        s, e = span
                        if s == e:  # LLM single token format [39,39]
                            neural_spans.add((s, s))
                            # Try to get text from neural tokens first, then from gold tokens
                            if 0 <= s < len(neural_tokens):
                                neural_texts.add(neural_tokens[s])
                            elif 0 <= s < len(gold_tokens):
                                neural_texts.add(gold_tokens[s])
                        else:  # CONLLU range format [39,40]
                            neural_spans.add((s, e))
                            # Try to get text from neural tokens first, then from gold tokens
                            if 0 <= s < len(neural_tokens) and 0 <= e <= len(neural_tokens):
                                neural_texts.add(" ".join(neural_tokens[s:e]))
                            elif 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                                neural_texts.add(" ".join(gold_tokens[s:e]))
                
                gold_spans = set()
                gold_texts = set()
                for span in gold_cluster:
                    if isinstance(span, (list, tuple)) and len(span) == 2:
                        s, e = span
                        gold_spans.add((s, e))
                        if 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                            gold_texts.add(" ".join(gold_tokens[s:e]))
                

                if neural_texts and gold_texts:
                    # Calculate content-based similarity
                    text_intersection = len(neural_texts & gold_texts)
                    text_union = len(neural_texts | gold_texts)
                    text_similarity = text_intersection / text_union if text_union > 0 else 0.0
                    
                    # Check if there's at least one exact content word match (not a pronoun)
                    has_content_match = False
                    for text in neural_texts:
                        if text in gold_texts and not is_pronoun(text):
                            has_content_match = True
                            break
                    
                    # Calculate position-based similarity (more forgiving)
                    position_similarity = 0.0
                    if neural_spans and gold_spans:
                        # Count spans that are close or overlapping
                        close_spans = 0
                        for n_span in neural_spans:
                            for g_span in gold_spans:
                                # Check if spans overlap or are very close
                                if (n_span[0] <= g_span[1] and n_span[1] >= g_span[0]) or \
                                   abs(n_span[0] - g_span[0]) <= 1 or abs(n_span[1] - g_span[1]) <= 1:
                                    close_spans += 1
                        
                        if close_spans > 0:
                            position_similarity = close_spans / max(len(neural_spans), len(gold_spans))
                    
                    # Combine similarities (give more weight to content)
                    similarity = 0.8 * text_similarity + 0.2 * position_similarity
                    
                    # Additional requirement: minimum content overlap
                    min_content_overlap = 0.3  # At least 30% of content should overlap
                    if text_similarity < min_content_overlap:
                        similarity *= 0.5  # Penalize low content overlap
                    
                    # Critical requirement: must have at least one content word match
                    if not has_content_match:
                        similarity *= 0.3  # Heavily penalize clusters with no content word matches
                else:
                    # Fallback to span overlap if no text available
                    if neural_spans and gold_spans:
                        overlap = 0
                        total_neural = len(neural_spans)
                        total_gold = len(gold_spans)
                        
                        for n_span in neural_spans:
                            for g_span in gold_spans:
                                # Check if spans overlap or are close
                                if (n_span[0] <= g_span[1] and n_span[1] >= g_span[0]) or \
                                   abs(n_span[0] - g_span[0]) <= 1 or abs(n_span[1] - g_span[1]) <= 1:
                                    overlap += 1
                        
                        if total_neural > 0 and total_gold > 0:
                            similarity = overlap / max(total_neural, total_gold)
                        else:
                            similarity = 0.0
                    else:
                        similarity = 0.0
            else:
                # Fall back to span overlap if no text available
                neural_spans = set(tuple(span) for span in neural_cluster if isinstance(span, (list, tuple)) and len(span) == 2)
                gold_spans = set(tuple(span) for span in gold_cluster if isinstance(span, (list, tuple)) and len(span) == 2)
                
                if neural_spans and gold_spans:
                    intersection = len(neural_spans & gold_spans)
                    union = len(neural_spans | gold_spans)
                    similarity = intersection / union if union > 0 else 0.0
                else:
                    similarity = 0.0
            row.append(similarity)
        similarity_matrix.append(row)
    
    # Find best matches using greedy assignment with more forgiving threshold
    correct_clusters = []
    extra_clusters = []
    missed_clusters = []
    
    # Track which gold clusters have been matched
    matched_gold = set()
    
    # Find correct matches (more forgiving threshold)
    for neural_idx, row in enumerate(similarity_matrix):
        best_gold_idx = max(range(len(row)), key=lambda i: row[i])
        best_similarity = row[best_gold_idx]
        
        if best_similarity >= 0.4 and best_gold_idx not in matched_gold:  # Higher threshold for more strict matching
            correct_clusters.append({
                'neural_idx': neural_idx,
                'gold_idx': best_gold_idx,
                'similarity': best_similarity
            })
            matched_gold.add(best_gold_idx)
        else:
            extra_clusters.append({
                'neural_idx': neural_idx,
                'similarity': best_similarity
            })
    
    # Find missed clusters
    for gold_idx in range(len(gold_clusters)):
        if gold_idx not in matched_gold:
            missed_clusters.append({
                'gold_idx': gold_idx
            })
    
    return {
        'correct_clusters': correct_clusters,
        'extra_clusters': extra_clusters,
        'missed_clusters': missed_clusters,
        'total_correct': len(correct_clusters),
        'total_extra': len(extra_clusters),
        'total_missed': len(missed_clusters),
        'similarity_matrix': similarity_matrix
    }

def display_prediction_analysis_word_level(neural_doc, gold_doc):
    """Display prediction analysis with word-level comparison."""
    print(f"\n{'='*80}")
    print(f"{BOLD}CLUSTER-LEVEL PREDICTION ANALYSIS (Word-Level + Weighted Similarity){RESET}")
    print(f"{'='*80}")
    
    # Check text availability
    neural_has_text = neural_doc.get("cased_words") or neural_doc.get("tokens")
    gold_has_text = gold_doc.get("cased_words") or gold_doc.get("tokens")
    
    # Get tokens for text display
    neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
    gold_tokens = gold_doc.get("cased_words", gold_doc.get("tokens", []))
    
    # Analyze predictions
    analysis = analyze_predictions_word_level(neural_doc, gold_doc)
    
    # Display summary
    print(f"\nSummary:")
    print(f"  ✅ Correct clusters: {analysis['total_correct']}")
    print(f"  ❌ Extra clusters: {analysis['total_extra']}")
    print(f"  🔍 Missed clusters: {analysis['total_missed']}")
    
    # Display correct clusters
    if analysis['correct_clusters']:
        print(f"\n✅ CORRECT CLUSTERS (High Similarity):")
        print(f"{'─'*80}")
        for match in analysis['correct_clusters']:
            neural_idx = match['neural_idx']
            gold_idx = match['gold_idx']
            similarity = match['similarity']
            
            # Get cluster spans and text
            neural_cluster = neural_doc.get("clusters", [])[neural_idx]
            gold_cluster = gold_doc.get("clusters", [])[gold_idx]
            
            # Display neural cluster with text from gold if available
            neural_spans_text = []
            neural_text_parts = []
            for span in neural_cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    if s == e:  # LLM single token format
                        span_text = f"[{s}]"
                        # Try to get text from gold tokens if available
                        if gold_has_text and 0 <= s < len(gold_tokens):
                            neural_text_parts.append(gold_tokens[s])
                        else:
                            neural_text_parts.append("(no text)")
                    else:  # CONLLU range format
                        span_text = f"[{s},{e}]"
                        if gold_has_text and 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                            neural_text_parts.append(" ".join(gold_tokens[s:e]))
                        else:
                            neural_text_parts.append("(no text)")
                    neural_spans_text.append(span_text)
            
            # Display gold cluster
            gold_spans_text = []
            gold_text_parts = []
            for span in gold_cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    span_text = f"[{s},{e}]"
                    gold_spans_text.append(span_text)
                    if gold_has_text and 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                        gold_text_parts.append(" ".join(gold_tokens[s:e]))
                    else:
                        gold_text_parts.append("(no text)")
            
            print(f"Neural Cluster {neural_idx} ↔ Gold Cluster {gold_idx} (Similarity: {similarity:.3f})")
            print(f"Neural: {' | '.join(neural_spans_text)} → {' | '.join(neural_text_parts)}")
            print(f"Gold: {' | '.join(gold_spans_text)} → {' | '.join(gold_text_parts)}")
            print()
    
    # Display extra clusters
    if analysis['extra_clusters']:
        print(f"\n❌ EXTRA/INCORRECT CLUSTERS:")
        print(f"{'─'*80}")
        for extra in analysis['extra_clusters']:
            neural_idx = extra['neural_idx']
            neural_cluster = neural_doc.get("clusters", [])[neural_idx]
            
            spans_text = []
            text_parts = []
            for span in neural_cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    if s == e:  # LLM single token format
                        span_text = f"[{s}]"
                        # Try to get text from gold tokens if available
                        if gold_has_text and 0 <= s < len(gold_tokens):
                            text_parts.append(gold_tokens[s])
                        else:
                            text_parts.append("(no text)")
                    else:  # CONLLU range format
                        span_text = f"[{s},{e}]"
                        if gold_has_text and 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                            text_parts.append(" ".join(gold_tokens[s:e]))
                        else:
                            text_parts.append("(no text)")
                    spans_text.append(span_text)
            
            print(f"  Neural Cluster {neural_idx} (No Gold Match)")
            print(f"    Spans: {' | '.join(spans_text)}")
            if text_parts:
                print(f"    Text: {' | '.join(text_parts)}")
            print()
    
    # Display missed clusters
    if analysis['missed_clusters']:
        print(f"\n🔍 MISSED CLUSTERS (In Gold, Not Predicted):")
        print(f"{'─'*80}")
        for missed in analysis['missed_clusters']:
            gold_idx = missed['gold_idx']
            gold_cluster = gold_doc.get("clusters", [])[gold_idx]
            
            spans_text = []
            text_parts = []
            pronouns = []
            content = []
            
            for span in gold_cluster:
                if isinstance(span, (list, tuple)) and len(span) == 2:
                    s, e = span
                    span_text = f"[{s},{e}]"
                    spans_text.append(span_text)
                    
                    if gold_has_text and 0 <= s < len(gold_tokens) and 0 <= e <= len(gold_tokens):
                        span_text_content = " ".join(gold_tokens[s:e])
                        text_parts.append(span_text_content)
                        
                        # Categorize as pronoun or content
                        if is_pronoun(span_text_content):
                            pronouns.append(span_text_content)
                        else:
                            content.append(span_text_content)
                    else:
                        text_parts.append("(no text)")
            
            print(f"  Gold Cluster {gold_idx} (No Neural Match)")
            print(f"    Spans: {' | '.join(spans_text)}")
            if text_parts:
                print(f"    Text: {' | '.join(text_parts)}")
                if pronouns:
                    print(f"    Pronouns: {', '.join(pronouns)}")
                if content:
                    print(f"    Content: {', '.join(content)}")
            print()
    
    # Display similarity matrix
    if analysis.get('similarity_matrix'):
        print(f"\n📊 CLUSTER SIMILARITY MATRIX (Weighted)")
        print(f"{'─'*80}")
        
        if neural_has_text and gold_has_text:
            print("Note: Using weighted similarity with pronoun detection")
        else:
            print("Note: Similarity based on span overlap only (no text content available)")
        
        print(f"{'─'*80}")
        
        # Show matrix headers
        gold_clusters = gold_doc.get("clusters", [])
        neural_clusters = neural_doc.get("clusters", [])
        
        # Print gold cluster headers
        header_line = "            "
        for i in range(len(gold_clusters)):
            header_line += f"Gold {i:4d}  "
        print(header_line)
        
        # Print matrix rows
        for i, row in enumerate(analysis['similarity_matrix']):
            row_line = f"Neural {i:3d}  "
            for similarity in row:
                if similarity >= 0.5:
                    row_line += f"{COLORS[1]}{similarity:.3f}{RESET}   "
                elif similarity >= 0.3:
                    row_line += f"{COLORS[2]}{similarity:.3f}{RESET}   "
                else:
                    row_line += f"{similarity:.3f}   "
            print(row_line)
        
        # Show key differences
        if analysis['total_extra'] > 0 or analysis['total_missed'] > 0:
            print(f"\nKey Differences:")
            if analysis['total_extra'] > 0:
                print(f"Extra clusters: {analysis['total_extra']}")
            if analysis['total_missed'] > 0:
                print(f"Missed clusters: {analysis['total_missed']}")
    
    # Show weighted similarity note
    if neural_has_text or gold_has_text:
        print(f"\nℹ️  Note: Using weighted similarity (pronouns: 0.2, content words: 1.0)")
        if neural_has_text and gold_has_text:
            print("   Both files have text content - full word-level analysis available")
        elif gold_has_text:
            print("   Using text content from gold file for analysis")
        else:
            print("   Using text content from neural file for analysis")
    else:
        print(f"\nℹ️  Note: No text content available - using span-based similarity only")

def demonstrate_weighted_similarity():
    """Demonstrate how weighted similarity handles pronouns vs. long mentions."""
    print(f"\n{'='*80}")
    print(f"{BOLD}WEIGHTED SIMILARITY DEMONSTRATION{RESET}")
    print(f"{'='*80}")
    
    # Example 1: Problematic case from user's example
    neural_cluster = {"הוא", "הוא", "הוא"}  # Just pronouns
    gold_cluster = {"הוא", "עולם חדש אידאליסטי ש ב הוא ה אירועים ה שונים ו ה מורכבים אינם מתרחקים מ מרכז ה מקרין עידון רב ו יופי עתיר גוונים"}
    
    print(f"\n📝 Example 1: Problematic Case (Old vs. New System)")
    print(f"Neural Cluster: {neural_cluster}")
    print(f"Gold Cluster: {gold_cluster}")
    
    # Old Jaccard similarity
    old_similarity = len(neural_cluster & gold_cluster) / len(neural_cluster | gold_cluster)
    print(f"\n🔴 Old Jaccard Similarity: {old_similarity:.3f}")
    print(f"   Problem: Treats pronouns and long mentions equally!")
    
    # New weighted similarity
    new_similarity = calculate_weighted_similarity(neural_cluster, gold_cluster)
    print(f"\n✅ New Weighted Similarity: {new_similarity:.3f}")
    print(f"   Solution: Pronouns get lower weight (0.2), content gets full weight (1.0)")
    
    # Example 2: Good match case
    neural_cluster2 = {"פאראצטמול", "פאראצטמול , תרופה דמוית אספירין", "תרופה דמוית אספירין"}
    gold_cluster2 = {"פאראצטמול", "תרופה דמוית אספירין", "פאראצטמול , תרופה דמוית אספירין", "ה תרופה"}
    
    print(f"\n📝 Example 2: Good Match Case")
    print(f"Neural Cluster: {neural_cluster2}")
    print(f"Gold Cluster: {gold_cluster2}")
    
    old_similarity2 = len(neural_cluster2 & gold_cluster2) / len(neural_cluster2 | gold_cluster2)
    new_similarity2 = calculate_weighted_similarity(neural_cluster2, gold_cluster2)
    
    print(f"Old Jaccard: {old_similarity2:.3f}")
    print(f"New Weighted: {new_similarity2:.3f}")
    print(f"Both systems work well for content-rich clusters!")
    
    # Example 3: Mixed case
    neural_cluster3 = {"הוא", "המנהל", "הוא"}
    gold_cluster3 = {"הוא", "המנהל", "הוא", "המנהל החדש"}
    
    print(f"\n📝 Example 3: Mixed Case (Pronouns + Content)")
    print(f"Neural Cluster: {neural_cluster3}")
    print(f"Gold Cluster: {gold_cluster3}")
    
    old_similarity3 = len(neural_cluster3 & gold_cluster3) / len(neural_cluster3 | gold_cluster3)
    new_similarity3 = calculate_weighted_similarity(neural_cluster3, gold_cluster3)
    
    print(f"Old Jaccard: {old_similarity3:.3f}")
    print(f"New Weighted: {new_similarity3:.3f}")
    print(f"Balanced approach for mixed content!")
    
    # Example 4: Underscore handling (new)
    neural_cluster4 = {"הוא", "ה_תרופה", "הוא"}
    gold_cluster4 = {"הוא", "ה תרופה", "הוא", "התרופה החדשה"}
    
    print(f"\n📝 Example 4: Underscore Handling (New Feature)")
    print(f"Neural Cluster: {neural_cluster4}")
    print(f"Gold Cluster: {gold_cluster4}")
    print(f"Note: 'ה_תרופה' vs 'ה תרופה' - underscores are stripped for pronoun detection")
    
    old_similarity4 = len(neural_cluster4 & gold_cluster4) / len(neural_cluster4 | gold_cluster4)
    new_similarity4 = calculate_weighted_similarity(neural_cluster4, gold_cluster4)
    
    print(f"Old Jaccard: {old_similarity4:.3f}")
    print(f"New Weighted: {new_similarity4:.3f}")
    print(f"Underscore stripping ensures proper pronoun detection!")
    
    print(f"\n{'─'*80}")
    print(f"Key Benefits of Weighted Similarity:")
    print(f"  ✅ Prevents false matches between pronoun-only and content-rich clusters")
    print(f"  ✅ Gives appropriate weight to meaningful content")
    print(f"  ✅ Maintains good matching for similar content clusters")
    print(f"  ✅ Configurable weights (currently: content=1.0, pronouns=0.2)")
    print(f"  ✅ Handles underscores in text (e.g., 'ה_תרופה' → 'ה תרופה')")

def compare_multiple_files_with_corresponding_gold(all_neural_docs, all_gold_docs, doc_id=None, show_diff=False, show_correct_mistaken=False, show_full_doc=False):
    """Compare multiple neural files against their corresponding gold files."""
    print(f"{'='*100}")
    print(f"{BOLD}MULTIPLE FILE COMPARISON WITH CORRESPONDING GOLD{RESET}")
    print(f"{'='*100}")
    
    # Get all unique document keys
    all_doc_keys = set()
    for neural_docs in all_neural_docs.values():
        all_doc_keys.update(neural_docs.keys())
    for gold_docs in all_gold_docs.values():
        all_doc_keys.update(gold_docs.keys())
    
    # Filter by specific document if requested
    if doc_id:
        all_doc_keys = {doc_id}
    
    # Sort documents by key
    keys = sorted(all_doc_keys)
    
    for doc_key in keys:
        print(f"\n{'='*80}")
        print(f"{BOLD}DOCUMENT: {doc_key}{RESET}")
        print(f"{'='*80}")
        
        # Show gold standards for this document
        print(f"\n{BOLD}GOLD STANDARDS:{RESET}\n")
        for gold_name, gold_docs in all_gold_docs.items():
            if doc_key in gold_docs:
                gold_doc = gold_docs[doc_key]
                gold_clusters = gold_doc.get("clusters", [])
                print(f"  {gold_name.upper()}:")
                print(f"    Tokens: {len(gold_doc.get('cased_words', gold_doc.get('tokens', [])))}")
                print(f"    Clusters: {len(gold_clusters)}")
                print(f"    Gold Cluster Summary:")
                for i, cluster in enumerate(gold_clusters):
                    spans_text = []
                    for span in cluster:
                        if isinstance(span, (list, tuple)) and len(span) == 2:
                            s, e = span
                            spans_text.append(f"[{s},{e}]")
                    print(f"      Cluster {i}: {', '.join(spans_text)}")
                print()
        
        # Show neural model comparisons
        print(f"{'─'*80}")
        print(f"{BOLD}NEURAL MODEL COMPARISONS:{RESET}")
        print(f"{'─'*80}")
        
        # Find corresponding gold data for each neural file
        neural_results = {}
        neural_names = list(all_neural_docs.keys())
        gold_names = list(all_gold_docs.keys())
        
        for i, (neural_name, neural_docs) in enumerate(all_neural_docs.items()):
            if doc_key in neural_docs:
                neural_doc = neural_docs[doc_key]
                
                # Find corresponding gold data by index (maintains order correspondence)
                corresponding_gold = None
                corresponding_gold_name = None
                
                if i < len(gold_names):
                    # Use corresponding gold file by index
                    gold_name = gold_names[i]
                    if doc_key in all_gold_docs[gold_name]:
                        corresponding_gold = all_gold_docs[gold_name][doc_key]
                        corresponding_gold_name = gold_name
                
                # Fallback: if no corresponding gold found by index, try to find any gold
                if not corresponding_gold:
                    for gold_name, gold_docs in all_gold_docs.items():
                        if doc_key in gold_docs:
                            corresponding_gold = gold_docs[doc_key]
                            corresponding_gold_name = gold_name
                            break
                
                if corresponding_gold:
                    print(f"\n✅ {neural_name}: Comparing with {corresponding_gold_name}")
                    
                    # Calculate metrics
                    metrics = calculate_metrics_word_level(neural_doc, corresponding_gold)
                    neural_results[neural_name] = metrics
                    
                    print(f"  Precision: {metrics['precision']:.3f}")
                    print(f"  Recall: {metrics['recall']:.3f}")
                    print(f"  F1: {metrics['f1']:.3f}")
                    print(f"  Neural clusters: {len(neural_doc.get('clusters', []))}")
                    print(f"  Gold clusters: {len(corresponding_gold.get('clusters', []))}")
                    
                    if show_correct_mistaken:
                        display_prediction_analysis_word_level(neural_doc, corresponding_gold)
                    
                    if show_full_doc:
                        display_full_document(neural_doc, corresponding_gold)
                else:
                    print(f"❌ {neural_name}: Corresponding gold file not found")
            else:
                print(f"❌ {neural_name}: Document not found")
        
        # Show summary comparison table
        if neural_results:
            print(f"\n{'='*80}")
            print(f"{BOLD}📊 SUMMARY COMPARISON TABLE{RESET}")
            print(f"{'='*80}")
            print(f"{'Model':<40} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Clusters':<12}")
            print(f"{'─'*40} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")
            
            for model_name, metrics in neural_results.items():
                clusters = len(all_neural_docs[model_name][doc_key].get("clusters", []))
                print(f"{model_name:<40} {metrics['precision']:<12.3f} {metrics['recall']:<12.3f} {metrics['f1']:<12.3f} {clusters:<12}")
            
            print(f"{'─'*40} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")
        else:
            print(f"\n{'='*80}")
            print(f"{BOLD}📊 SUMMARY COMPARISON TABLE{RESET}")
            print(f"{'='*80}")
            print(f"{'Model':<40} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Clusters':<12}")
            print(f"{'─'*40} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")
            print(f"{'─'*40} {'─'*12} {'─'*12} {'─'*12} {'─'*12}")

def cluster_diff(neural_doc, gold_doc, ctx):
    """Generate detailed cluster-by-cluster comparison."""
    def sort_key(cl):
        if not cl:
            return (0, 0)
        # Handle spans that might be lists or tuples
        starts = [s for s, _ in cl if isinstance((s, _), (list, tuple)) and len((s, _)) == 2]
        ends = [e for _, e in cl if isinstance((_, e), (list, tuple)) and len((_, e)) == 2]
        if not starts or not ends:
            return (0, 0)
        return (min(starts), max(ends))

    neural_cls = sorted(neural_doc.get("clusters", []), key=sort_key)
    gold_cls = sorted(gold_doc.get("clusters", []), key=sort_key)
    max_len = max(len(neural_cls), len(gold_cls))

    lines = []
    sep = "-" * 72
    
    # Get tokens for display
    neural_tokens = neural_doc.get("cased_words", neural_doc.get("tokens", []))
    gold_tokens = gold_doc.get("cased_words", gold_doc.get("tokens", []))
    
    for i in range(max_len):
        neural_cl = neural_cls[i] if i < len(neural_cls) else []
        gold_cl = gold_cls[i] if i < len(gold_cls) else []

        lines.append(f"[{i}]")
        
        # Build two aligned columns for neural / gold
        neural_rows = [f"[{s},{e}] {words(neural_tokens, [s, e])}"
                      for s, e in neural_cl if isinstance([s, e], (list, tuple)) and len([s, e]) == 2] or ["—"]
        gold_rows = [f"[{s},{e}] {words(gold_tokens, [s, e])}"
                    for s, e in gold_cl if isinstance([s, e], (list, tuple)) and len([s, e]) == 2] or ["—"]

        pad = max(len(x) for x in neural_rows) + 4
        for left, right in zip_longest(neural_rows, gold_rows, fillvalue=""):
            lines.append(f"    {left:<{pad}}{right}")
        lines.append(sep)
    
    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description="Compare neural model predictions with gold annotations")
    parser.add_argument("--neural", nargs="+", help="Neural model result file(s) or LLM prediction file(s)")
    parser.add_argument("--gold", nargs="+", help="Gold annotation file(s) - one per neural file (optional for LLM files)")
    parser.add_argument("--doc", help="Specific document ID to analyze")
    parser.add_argument("--full-doc", action="store_true", help="Show full document with colored clusters")
    parser.add_argument("--show-diff", action="store_true", help="Show key differences between predictions and gold")
    parser.add_argument("--correct-mistaken", action="store_true", help="Show correct vs mistaken predictions at cluster level")
    parser.add_argument("--compare-files", action="store_true", help="Compare multiple neural files")
    parser.add_argument("--demo", action="store_true", help="Demonstrate weighted similarity system")
    
    args = parser.parse_args()
    
    # Run demonstration if requested
    if args.demo:
        demonstrate_weighted_similarity()
        return
    
    # Validate that we have the required arguments for file comparison
    if not args.neural:
        print("❌ Error: --neural is required for file comparison")
        print("Use --demo to see the weighted similarity demonstration")
        return
    
    # Load neural/LLM data
    all_neural_docs = {}
    all_gold_docs = {}
    
    for i, neural_path in enumerate(args.neural):
        file_name = neural_path.split('/')[-1]
        print(f"Loading neural/LLM data: {neural_path}")
        
        try:
            neural_docs = load_data_smart(neural_path)
            all_neural_docs[file_name] = neural_docs
            
            # Check if this is an LLM file with built-in gold clusters
            if any("_gold" in key for key in neural_docs.keys()):
                print(f"  Detected LLM format with built-in gold clusters")
                # Extract gold clusters from the same file (but don't add to all_gold_docs yet)
                # We'll only use these if no external gold is provided
                built_in_gold_docs = {}
                for key, value in neural_docs.items():
                    if key.endswith("_gold"):
                        original_key = key.replace("_gold", "")
                        built_in_gold_docs[original_key] = value
                
                if built_in_gold_docs:
                    print(f"  Found {len(built_in_gold_docs)} built-in gold clusters (will use external gold if provided)")
            else:
                # Check if this is a CONLLU file (gold data)
                if any(key.isdigit() for key in neural_docs.keys()):
                    print(f"  Detected CONLLU format (gold data)")
                    all_gold_docs[file_name] = neural_docs
                    print(f"  Using CONLLU file as gold data with {len(neural_docs)} documents")
            
        except Exception as e:
            print(f"❌ Error loading {neural_path}: {e}")
            return
    
    # Load external gold data if provided
    if args.gold:
        if len(args.gold) != len(args.neural):
            print("❌ Error: Number of gold files must match number of neural files")
            print(f"  Neural files: {len(args.neural)}")
            print(f"  Gold files: {len(args.gold)}")
            return
        
        for i, gold_path in enumerate(args.gold):
            file_name = f"gold_{i+1}"
            print(f"Loading external gold data: {gold_path}")
            
            try:
                gold_docs = load_data_smart(gold_path)
                all_gold_docs[file_name] = gold_docs
            except Exception as e:
                print(f"❌ Error loading {gold_path}: {e}")
                return
    
    # If no external gold provided, use built-in gold from LLM files
    if not all_gold_docs:
        print("No external gold files provided, using built-in gold from LLM files...")
        for neural_name, neural_docs in all_neural_docs.items():
            if any("_gold" in key for key in neural_docs.keys()):
                # Extract built-in gold clusters
                gold_docs = {}
                for key, value in neural_docs.items():
                    if key.endswith("_gold"):
                        original_key = key.replace("_gold", "")
                        gold_docs[original_key] = value
                
                if gold_docs:
                    all_gold_docs[neural_name] = gold_docs
                    print(f"  Using built-in gold from {neural_name}")
    
    # If we still have no gold data, error out
    if not all_gold_docs:
        print("❌ Error: No gold data found. Either:")
        print("  1. Provide --gold files, or")
        print("  2. Use LLM files that contain both predicted_clusters and gold_clusters")
        return
    
    # If single file, show simple comparison
    if len(args.neural) == 1 and not args.compare_files:
        neural_docs = all_neural_docs[list(all_neural_docs.keys())[0]]
        gold_docs = all_gold_docs[list(all_gold_docs.keys())[0]]
        
        if args.doc:
            # Try to find the document in both files
            neural_doc_key = args.doc
            gold_doc_key = None
            
            # Check for exact match first
            if args.doc in neural_docs and args.doc in gold_docs:
                gold_doc_key = args.doc
            # If no exact match, try automatic mapping for single-document files
            elif len([k for k in neural_docs.keys() if not k.endswith('_gold')]) == 1 and len(gold_docs) == 1:
                # If both files have only one document, map them automatically
                neural_doc_key = [k for k in neural_docs.keys() if not k.endswith('_gold')][0]
                gold_doc_key = list(gold_docs.keys())[0]
                print(f"⚠️  Document key mismatch detected:")
                print(f"   LLM file has: {neural_doc_key}")
                print(f"   CONLLU file has: {gold_doc_key}")
                print(f"   Automatically mapping for comparison...")
            # If no exact match and CONLLU has only one document, try to map the requested document
            elif args.doc in neural_docs and len(gold_docs) == 1:
                neural_doc_key = args.doc
                gold_doc_key = list(gold_docs.keys())[0]
                print(f"⚠️  Document key mismatch detected:")
                print(f"   LLM file has: {neural_doc_key}")
                print(f"   CONLLU file has: {gold_doc_key}")
                print(f"   Automatically mapping for comparison...")
            else:
                print(f"❌ Document {args.doc} not found in both files")
                print(f"   Available in neural file: {list(neural_docs.keys())}")
                print(f"   Available in gold file: {list(gold_docs.keys())}")
                return
            
            if neural_doc_key in neural_docs and gold_doc_key in gold_docs:
                neural_doc = neural_docs[neural_doc_key]
                gold_doc = gold_docs[gold_doc_key]
                
                print(f"=== {neural_doc_key} (LLM) vs {gold_doc_key} (Gold) ===")
                neural_clusters = neural_doc.get("clusters", [])
                gold_clusters = gold_doc.get("clusters", [])
                
                print(f"Neural clusters: {len(neural_clusters)}")
                print(f"Gold clusters: {len(gold_clusters)}")
                
                if args.correct_mistaken:
                    display_prediction_analysis_word_level(neural_doc, gold_doc)
                
                if args.show_diff:
                    print(f"\nKey Differences:")
                    analysis = analyze_predictions_word_level(neural_doc, gold_doc)
                    if analysis['extra_clusters']:
                        print(f"  Extra clusters: {analysis['total_extra']}")
                    if analysis['missed_clusters']:
                        print(f"  Missed clusters: {analysis['total_missed']}")
                
                if args.full_doc:
                    display_full_document(neural_doc, gold_doc)
            else:
                print(f"❌ Could not find matching documents for comparison")
                return
        else:
            # Show all documents
            for doc_key in sorted(set(neural_docs.keys()) & set(gold_docs.keys())):
                neural_doc = neural_docs[doc_key]
                gold_doc = gold_docs[doc_key]
                show_neural_data_vs_gold(neural_doc, gold_doc, doc_key)
    else:
        # Multiple file comparison
        compare_multiple_files_with_corresponding_gold(
            all_neural_docs, all_gold_docs, 
            doc_id=args.doc, 
            show_diff=args.show_diff, 
            show_correct_mistaken=args.correct_mistaken, 
            show_full_doc=args.full_doc
        )

if __name__ == "__main__":
    main()
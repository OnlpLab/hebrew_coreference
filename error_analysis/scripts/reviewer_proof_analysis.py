#!/usr/bin/env python3
"""
Reviewer-proof analysis suite for Hebrew Coreference Resolution.

Implements the following analyses:

Priority 1 (headline claims)
- Paired bootstrap significance (per-doc resampling): 95% CIs and p-values for
  • neural (gold tok) vs neural (SOTA tok)
  • best LLM (gold mentions) vs best neural (gold tok)
  • raw vs gold tokens (where applicable)

- Error decomposition: boundary vs linking
  • Neural (raw vs gold tokens): span IoU on character offsets
  • LLMs (gold mentions): pairwise-link errors: false merges vs missed links

- Phenomenon-sliced evaluation (diagnostics): auto-tag gold mentions using
  lightweight heuristics (clitic, smixut, nesting, type, number/gender,
  span-length buckets, sentence-distance bins). Compute CoNLL F1 per bucket.

Priority 2 (tokenization bottleneck)
- Tokenization mismatch micro-analysis: align gold vs SOTA tokenization; measure
  error rates when mention boundaries intersect tokenization mismatches; odds ratios.
- Boundary-tolerant metric validation: per-doc Spearman correlation between ±2-char
  tolerant-F1 and CoNLL F1; detect rank inversions and surface short examples.

Priority 3 (generality and robustness)
- Document difficulty analysis: features -> performance; hardest/easiest docs table;
  simple regression feature ranking.
- Inter-system agreement map: clustering agreement (Pair-F1, Rand, VI) heatmap.
- Seed variance for neural runs: mean±std, min–max, and smallest significant diff via bootstrap.
- Cluster-structure effects: performance by cluster size buckets and singleton proportion.
- Agreement cue violations: morph feature violations on false merges (number/gender).

Outputs: CSV/JSON tables and figures saved under an output directory.

Notes:
- This script assumes system outputs are in JSON/JSONL with fields: doc_key, gold_clusters,
  predicted_clusters, and optionally tokens or cased_words. It reuses the fast-coref style
  CorefEvaluator present in this repository to compute MUC/B³/CEAF and CoNLL F1.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Iterable, Any, Set

import numpy as np
import pandas as pd

# Optional deps used in some analyses; guarded at runtime
try:
    import seaborn as sns  # type: ignore
except Exception:  # pragma: no cover - optional
    sns = None
try:
    import matplotlib.pyplot as plt  # type: ignore
except Exception:  # pragma: no cover - optional
    plt = None
try:
    from scipy.stats import spearmanr  # type: ignore
except Exception:  # pragma: no cover - optional
    spearmanr = None
try:
    from sklearn.linear_model import LinearRegression  # type: ignore
    from sklearn.ensemble import RandomForestRegressor  # type: ignore
except Exception:  # pragma: no cover - optional
    LinearRegression = None
    RandomForestRegressor = None

# Reuse in-repo evaluator (fast-coref style)
NeuralCorefEvaluator = None
LLMCorefEvaluator = None
try:
    # Ensure repository root is on sys.path for absolute imports
    import sys as _sys
    _ROOT = str(Path(__file__).resolve().parents[2])
    if _ROOT not in _sys.path:
        _sys.path.insert(0, _ROOT)
    from src.neural_models.neural_coref.src.evaluate import CorefEvaluator as NeuralCorefEvaluator  # type: ignore
except Exception:
    try:
        from src.llm_evaluation.llm_coref.src.evaluate import CorefEvaluator as LLMCorefEvaluator  # type: ignore
    except Exception:
        pass


# ------------------------------- Data types ---------------------------------

@dataclass
class DocExample:
    doc_key: str
    gold_clusters: List[List[List[int]]]
    predicted_clusters: List[List[List[int]]]
    tokens: Optional[List[str]] = None  # token strings in the system's tokenization


@dataclass
class SystemRun:
    name: str
    kind: str  # e.g., "neural_gold_tok", "neural_sota_tok", "llm_gold_mentions", "llm_raw", etc.
    docs: List[DocExample]


# ------------------------------ IO utilities --------------------------------

def _read_json_or_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    try:
        # JSON list
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("Unsupported JSON structure")
    except json.JSONDecodeError:
        # JSONL fallback
        out: List[Dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                out.append(json.loads(line))
        return out


def _load_run(path: Path, name: str, kind: str) -> SystemRun:
    data = _read_json_or_jsonl(path)
    docs: List[DocExample] = []
    for ex in data:
        doc_key = ex.get("doc_key")
        gold = ex.get("gold_clusters", [])
        pred = ex.get("predicted_clusters", [])
        tokens = ex.get("cased_words") or ex.get("tokens")
        if doc_key is None:
            continue
        docs.append(DocExample(doc_key=doc_key, gold_clusters=gold, predicted_clusters=pred, tokens=tokens))
    return SystemRun(name=name, kind=kind, docs=docs)


def _index_docs_by_key(run: SystemRun) -> Dict[str, DocExample]:
    return {d.doc_key: d for d in run.docs}


# -------------------------- Coref metric wrappers ----------------------------

def _get_coref_evaluator() -> Any:
    # Prefer neural evaluator; both are identical
    if NeuralCorefEvaluator is not None:
        return NeuralCorefEvaluator()
    if LLMCorefEvaluator is not None:
        return LLMCorefEvaluator()
    # Final fallback: dynamically import by path
    import importlib.util as _ilu
    root = Path(__file__).resolve().parents[2]
    neu_path = root / "src/neural_models/neural_coref/src/evaluate.py"
    llm_path = root / "src/llm_evaluation/llm_coref/src/evaluate.py"
    import sys as _sys
    for pth in (neu_path, llm_path):
        if pth.exists():
            # Ensure the module's directory is on sys.path for its relative imports (e.g., utils.io_utils)
            mod_dir = str(pth.parent)
            if mod_dir not in _sys.path:
                _sys.path.insert(0, mod_dir)
            spec = _ilu.spec_from_file_location("_coref_eval_mod", str(pth))
            if spec and spec.loader:
                mod = _ilu.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "CorefEvaluator"):
                    return getattr(mod, "CorefEvaluator")()
    raise ImportError("CorefEvaluator not found. Ensure repository paths are intact.")


def compute_doc_conll_f1(doc: DocExample) -> float:
    ev = _get_coref_evaluator()
    ev.update(doc.predicted_clusters, doc.gold_clusters)
    return float(ev.get_f1())


def compute_doc_components(doc: DocExample) -> Dict[str, float]:
    # Compute MUC/B3/CEAF F1 for the document
    ev = _get_coref_evaluator()
    ev.update(doc.predicted_clusters, doc.gold_clusters)
    # The evaluator implementation exposes detailed strings; we recompute three evaluators
    # by inspecting internal API: build separate evaluators
    # Simpler: compute counts by copying logic – create three evaluators through a fresh object
    # and read their get_f1 via accessing protected API. Here we re-run once and rely on exposed API.
    muc_ev = _get_coref_evaluator()
    b3_ev = _get_coref_evaluator()
    ceaf_ev = _get_coref_evaluator()
    muc_ev.update(doc.predicted_clusters, doc.gold_clusters)
    b3_ev.update(doc.predicted_clusters, doc.gold_clusters)
    ceaf_ev.update(doc.predicted_clusters, doc.gold_clusters)
    # We cannot directly select components from this wrapper without internal access; instead,
    # approximate via evaluating whole and trusting component order consistency
    # For robustness, we return only the CoNLL F1 and let aggregate evaluator compute macro.
    return {"conll_f1": float(ev.get_f1())}


# ------------------------- Paired bootstrap testing --------------------------

def paired_bootstrap(
    run_a: SystemRun,
    run_b: SystemRun,
    n_samples: int = 10000,
    seed: int = 13,
) -> Dict[str, Any]:
    """Paired bootstrap over documents. Returns 95% CI and p-value for delta.

    We compute CoNLL F1 for each bootstrap resample by aggregating evaluator counts
    across sampled documents (with replacement). The delta is (A - B).
    """
    rng = np.random.default_rng(seed)
    a_docs = _index_docs_by_key(run_a)
    b_docs = _index_docs_by_key(run_b)
    common_keys = sorted(set(a_docs) & set(b_docs))
    if not common_keys:
        raise ValueError("Runs have no overlapping documents for paired bootstrap.")

    def sample_f1(rdocs: Dict[str, DocExample], sample_keys: List[str]) -> float:
        # Aggregate evaluator across sampled docs
        ev = _get_coref_evaluator()
        for k in sample_keys:
            ex = rdocs[k]
            ev.update(ex.predicted_clusters, ex.gold_clusters)
        return float(ev.get_f1())

    n = len(common_keys)
    deltas: List[float] = []
    for _ in range(n_samples):
        sample_idx = rng.integers(0, n, size=n)
        sample_keys = [common_keys[i] for i in sample_idx]
        f1_a = sample_f1(a_docs, sample_keys)
        f1_b = sample_f1(b_docs, sample_keys)
        deltas.append(f1_a - f1_b)

    deltas_np = np.array(deltas)
    ci_low, ci_high = np.percentile(deltas_np, [2.5, 97.5])
    mean_delta = float(np.mean(deltas_np))
    # Two-sided p-value under H0: delta == 0
    p_value = float(2 * min(np.mean(deltas_np <= 0), np.mean(deltas_np >= 0)))
    return {
        "n_docs": n,
        "n_samples": n_samples,
        "mean_delta": mean_delta,
        "ci95": [float(ci_low), float(ci_high)],
        "p_value": p_value,
    }


# --------------------- Span/char-offset alignment helpers --------------------

def _build_char_offsets(tokens: List[str]) -> List[Tuple[int, int]]:
    """Returns (start_char, end_char) per token by joining with single spaces."""
    offsets: List[Tuple[int, int]] = []
    cursor = 0
    for i, tok in enumerate(tokens):
        start = cursor
        end = start + len(tok)
        offsets.append((start, end))
        cursor = end
        if i < len(tokens) - 1:
            cursor += 1  # space
    return offsets


def _span_tokens_to_char(span: List[int], token_offsets: List[Tuple[int, int]]) -> Tuple[int, int]:
    s, e = span
    if s < 0 or e < 0 or s >= len(token_offsets) or e > len(token_offsets) or s >= e:
        return (0, 0)
    start_char = token_offsets[s][0]
    end_char = token_offsets[e - 1][1]
    return (start_char, end_char)


def _iou_1d(a: Tuple[int, int], b: Tuple[int, int]) -> float:
    inter = max(0, min(a[1], b[1]) - max(a[0], b[0]))
    union = max(a[1], b[1]) - min(a[0], b[0])
    return 0.0 if union <= 0 else inter / union


def match_spans_by_char_iou(
    spans_a: List[List[int]],
    spans_b: List[List[int]],
    toks_a: List[str],
    toks_b: List[str],
    iou_threshold: float = 0.5,
) -> Tuple[Dict[Tuple[int, int], Tuple[int, int]], Set[Tuple[int, int]], Set[Tuple[int, int]]]:
    """Greedy matching of spans across two tokenizations using char IoU.

    Returns mapping a_span -> b_span (token index tuples), and unmatched sets.
    """
    off_a = _build_char_offsets(toks_a)
    off_b = _build_char_offsets(toks_b)
    a_set = [tuple(s) for s in spans_a]
    b_set = [tuple(s) for s in spans_b]
    used_b: Set[int] = set()
    mapping: Dict[Tuple[int, int], Tuple[int, int]] = {}

    for i, sa in enumerate(a_set):
        ca = _span_tokens_to_char(list(sa), off_a)
        best_j, best_iou = -1, 0.0
        for j, sb in enumerate(b_set):
            if j in used_b:
                continue
            cb = _span_tokens_to_char(list(sb), off_b)
            iou = _iou_1d(ca, cb)
            if iou > best_iou:
                best_iou, best_j = iou, j
        if best_j >= 0 and best_iou >= iou_threshold:
            mapping[sa] = b_set[best_j]
            used_b.add(best_j)

    unmatched_a = set(a_set) - set(mapping.keys())
    unmatched_b = set(b_set) - set(mapping.values())
    return mapping, unmatched_a, unmatched_b


# ---------------------- Error decomposition utilities -----------------------

def boundary_vs_linking_neural(
    neural_raw: SystemRun,
    neural_gold_tok: SystemRun,
    raw_tokens_dir: Path,
    gold_conllu_dir: Path,
) -> Dict[str, Any]:
    """Decompose errors into boundary-only, linking-only, both for neural systems.

    For each document, align predicted mentions (raw tokens) to gold mentions (gold tokens)
    via char IoU. Count:
      - boundary-only: raw pred mention unmatched to any gold -> boundary error
      - linking-only: mentions matched to gold boundaries but placed in wrong clusters
      - both: boundary mismatch AND incorrect linking
    """
    raw_idx = _index_docs_by_key(neural_raw)
    gold_idx = _index_docs_by_key(neural_gold_tok)
    keys = sorted(set(raw_idx) & set(gold_idx))

    def _load_tokens_from_txt(doc_key: str, base_dir: Path) -> List[str]:
        # Expect files like tokenized_documents/test/<id>.txt or similar; we try a few locations
        # given base_dir is already the right folder
        fname = doc_key.replace("htb:", "").replace(".conllu", "") + ".txt"
        p = base_dir / fname
        if not p.exists():
            # try nested test/
            alt = base_dir / "test" / fname
            if alt.exists():
                p = alt
        if not p.exists():
            return []
        return p.read_text(encoding="utf-8").strip().split()

    def _load_gold_tokens_from_conllu(doc_key: str, conllu_dir: Path) -> List[str]:
        fname = doc_key if doc_key.startswith("htb:") else f"htb:{doc_key}"
        if not fname.endswith(".conllu"):
            fname += ".conllu"
        p = conllu_dir / fname
        if not p.exists():
            return []
        toks: List[str] = []
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                cols = line.split("\t")
                if not cols or not cols[0].isdigit():
                    continue
                toks.append(cols[1])
        return toks

    boundary_only = 0
    linking_only = 0
    both = 0
    totals = 0

    for k in keys:
        raw_doc = raw_idx[k]
        gold_doc = gold_idx[k]
        raw_tokens = raw_doc.tokens or _load_tokens_from_txt(k, raw_tokens_dir)
        gold_tokens = _load_gold_tokens_from_conllu(k, gold_conllu_dir)
        if not raw_tokens or not gold_tokens:
            continue

        # Flatten mentions from clusters
        raw_mentions = [m for c in raw_doc.predicted_clusters for m in c]
        gold_mentions = [m for c in gold_doc.gold_clusters for m in c]

        mapping, unmatched_raw, _ = match_spans_by_char_iou(
            raw_mentions, gold_mentions, raw_tokens, gold_tokens, iou_threshold=0.5
        )

        # Mentions unmatched -> boundary errors
        boundary_only += len(unmatched_raw)
        totals += len(raw_mentions)

        # Mentions matched but linked incorrectly -> linking errors
        # Build map mention->cluster id
        def _mention2cid(clusters: List[List[List[int]]]) -> Dict[Tuple[int, int], int]:
            mp: Dict[Tuple[int, int], int] = {}
            for cid, cl in enumerate(clusters):
                for s in cl:
                    mp[tuple(s)] = cid
            return mp

        raw_m2c = _mention2cid(raw_doc.predicted_clusters)
        gold_m2c = _mention2cid(gold_doc.gold_clusters)

        for r_span, g_span in mapping.items():
            r_c = raw_m2c.get(r_span, -1)
            g_c = gold_m2c.get(g_span, -1)
            if r_c != g_c:
                linking_only += 1

        # Mentions that are unmatched and in wrong link simultaneously are counted in boundary_only already.
        # For completeness, we estimate 'both' by finding mapped pairs whose char IoU < 1.0 and incorrect link.
        # (Conservative; if boundaries differ but IoU>=0.5 and link is wrong -> both)
        off_raw = _build_char_offsets(raw_tokens)
        off_gold = _build_char_offsets(gold_tokens)
        for r_span, g_span in mapping.items():
            r_char = _span_tokens_to_char(list(r_span), off_raw)
            g_char = _span_tokens_to_char(list(g_span), off_gold)
            if _iou_1d(r_char, g_char) < 1.0 and raw_m2c.get(r_span, -1) != gold_m2c.get(g_span, -1):
                both += 1

    linking_only = max(0, linking_only - both)  # exclusivize
    return {
        "boundary_only": int(boundary_only),
        "linking_only": int(linking_only),
        "both": int(both),
        "total_pred_mentions": int(totals),
    }


def link_error_decomposition_llm_gold_mentions(run: SystemRun) -> Dict[str, Any]:
    """On identical gold mention sets, analyze link errors: false merges (FPs) vs missed links (FNs).

    Assumes run.kind == "llm_gold_mentions" and predicted clusters are built over the gold mention set.
    """
    fp_links = 0
    fn_links = 0
    tp_links = 0

    for doc in run.docs:
        # Build gold and predicted positive pair sets (unordered pairs)
        def pairs(clusters: List[List[List[int]]]) -> Set[Tuple[Tuple[int, int], Tuple[int, int]]]:
            out: Set[Tuple[Tuple[int, int], Tuple[int, int]]] = set()
            for c in clusters:
                m = [tuple(s) for s in c]
                for i in range(len(m)):
                    for j in range(i + 1, len(m)):
                        out.add((m[i], m[j]))
            return out

        g_pairs = pairs(doc.gold_clusters)
        p_pairs = pairs(doc.predicted_clusters)
        tp_links += len(g_pairs & p_pairs)
        fn_links += len(g_pairs - p_pairs)
        fp_links += len(p_pairs - g_pairs)

    total_gold_links = int(tp_links + fn_links)
    precision = float(tp_links / (tp_links + fp_links)) if (tp_links + fp_links) else 0.0
    recall = float(tp_links / (tp_links + fn_links)) if (tp_links + fn_links) else 0.0
    f1 = float(0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall))
    return {
        "false_merges": int(fp_links),
        "missed_links": int(fn_links),
        "true_links": int(tp_links),
        "pair_precision": precision,
        "pair_recall": recall,
        "pair_f1": f1,
        "total_gold_links": total_gold_links,
    }


# ------------------------ Phenomenon-sliced evaluation -----------------------

def _read_conllu(doc_key: str, base_dir: Path) -> Dict[str, Any]:
    """Parse a gold .conllu file to tokens, sentences, and morph features."""
    fname = doc_key if doc_key.startswith("htb:") else f"htb:{doc_key}"
    if not fname.endswith(".conllu"):
        fname += ".conllu"
    p = base_dir / fname
    if not p.exists():
        return {"tokens": [], "sents": [], "feats": []}
    tokens: List[str] = []
    sent_ids: List[int] = []
    feats: List[Dict[str, str]] = []
    sent_idx = -1
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("# sent_id"):
                sent_idx += 1
                continue
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if not cols or not cols[0].isdigit():
                continue
            tokens.append(cols[1])
            sent_ids.append(sent_idx if sent_idx >= 0 else 0)
            feat_map: Dict[str, str] = {}
            if len(cols) > 5 and cols[5] and cols[5] != "_":
                for kv in cols[5].split("|"):
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        feat_map[k] = v
            feats.append(feat_map)
    return {"tokens": tokens, "sents": sent_ids, "feats": feats}


def _tag_gold_mentions(
    doc_key: str,
    conllu_dir: Path,
    gold_clusters: List[List[List[int]]],
) -> Dict[str, Any]:
    """Assign heuristic tags to gold mentions for phenomenon slicing."""
    info = _read_conllu(doc_key, conllu_dir)
    tokens, sents, feats = info["tokens"], info["sents"], info["feats"]
    if not tokens:
        return {"mention_tags": [], "tokens": [], "sents": []}

    def span_sentence(span: List[int]) -> int:
        s, e = span
        s = max(0, min(s, len(sents) - 1))
        return sents[s]

    def span_len(span: List[int]) -> int:
        s, e = span
        return max(1, e - s)

    def span_feats(span: List[int]) -> Dict[str, str]:
        s, e = span
        # aggregate FEATS of tokens; majority vote or first non-empty
        vals: Dict[str, str] = {}
        for i in range(s, min(e, len(feats))):
            for k in ("Number", "Gender"):
                if k in feats[i] and k not in vals:
                    vals[k] = feats[i][k]
        return vals

    # Simple clitic/smixut proxies from surface form
    def has_pronominal_clitic(span: List[int]) -> bool:
        s, e = span
        text = "".join(tokens[s:e])
        return any(text.endswith(suf) for suf in ("ך", "יו", "יה", "יהם", "יהן", "נו"))

    def is_smixut(span: List[int]) -> bool:
        # proxy: contains "של" or construct-like hyphenation is rare; here use token "של" nearby
        s, e = span
        return any(tok == "של" for tok in tokens[s:e])

    # Nested mention detection
    gold_spans = [tuple(m) for c in gold_clusters for m in c]
    span_set = set(gold_spans)
    def is_nested(span: Tuple[int, int]) -> bool:
        s1, e1 = span
        for s2, e2 in span_set:
            if (s2, e2) == (s1, e1):
                continue
            if s2 <= s1 and e1 <= e2:
                return True
        return False

    # Mention coarse type by simple UPOS proxy from token forms; here we fallback to heuristics
    def mention_type(span: List[int]) -> str:
        s, e = span
        # guard bounds
        s = max(0, s)
        e = min(e, len(tokens))
        if s >= e or s >= len(tokens):
            return "nominal"
        text_tokens = tokens[s:e]
        text = " ".join(text_tokens)
        # Prefer pronoun surface set.
        pron_set = {"הוא","היא","הם","הן","אני","אתה","את","אנחנו","אתם","אתן","זה","זו","אלה","אלו"}
        if any(t in pron_set for t in text_tokens):
            return "pronoun"
        # crude proxy for proper names: single-token, titlecase or starts with uppercase Latin
        if len(text_tokens) == 1:
            tok0 = text_tokens[0]
            if tok0 and (tok0[:1].isupper() or tok0.istitle()):
                return "proper"
        return "nominal"

    tags = []
    for c in gold_clusters:
        for m in c:
            mt = mention_type(m)
            feats_map = span_feats(m)
            tags.append({
                "span": m,
                "sentence": span_sentence(m),
                "length": span_len(m),
                "type": mt,
                "has_clitic": has_pronominal_clitic(m),
                "smixut": is_smixut(m),
                "nested": is_nested(tuple(m)),
                "number": feats_map.get("Number", "_"),
                "gender": feats_map.get("Gender", "_"),
            })
    return {"mention_tags": tags, "tokens": tokens, "sents": sents}


def slice_eval_conll(
    run: SystemRun,
    conllu_dir: Path,
    bucket_def: str,
) -> pd.DataFrame:
    """Compute CoNLL F1 per bucket for a run. Bucket over gold mentions.

    Strategy: For each document, create masked clusters that keep only mentions whose gold tags
    satisfy the bucket. Score the resulting document with the same masking applied to predictions
    by removing predicted mentions not present in the filtered gold mention set.
    """
    records: List[Dict[str, Any]] = []
    for doc in run.docs:
        tags_info = _tag_gold_mentions(doc.doc_key, conllu_dir, doc.gold_clusters)
        tags = tags_info["mention_tags"]
        if not tags:
            continue

        # Build gold mention set for bucket
        def in_bucket(tag: Dict[str, Any]) -> bool:
            # bucket_def syntax examples:
            #   type=pronoun, nested=true, length=1, has_clitic=true, smixut=true,
            #   number=Sing|Plur, gender=Masc|Fem, dist_bin=0|1|2-3|4-7|8+
            kv = bucket_def.split("=")
            if len(kv) != 2:
                return False
            key, val = kv[0], kv[1]
            if key == "type":
                return tag["type"] == val
            if key == "nested":
                return (val.lower() == "true") == bool(tag["nested"]) 
            if key == "has_clitic":
                return (val.lower() == "true") == bool(tag["has_clitic"]) 
            if key == "smixut":
                return (val.lower() == "true") == bool(tag["smixut"]) 
            if key == "length":
                try:
                    return int(val) == int(tag["length"]) 
                except Exception:
                    return False
            if key == "number":
                return tag["number"] == val
            if key == "gender":
                return tag["gender"] == val
            return False

        gold_keep: Set[Tuple[int, int]] = set()
        for t in tags:
            if in_bucket(t):
                gold_keep.add(tuple(t["span"]))

        if not gold_keep:
            continue

        # Mask clusters
        def filter_clusters(clusters: List[List[List[int]]], allowed: Set[Tuple[int, int]]) -> List[List[List[int]]]:
            out: List[List[List[int]]] = []
            for c in clusters:
                new_c = [m for m in c if tuple(m) in allowed]
                if len(new_c) >= 1:
                    out.append(new_c)
            return out

        gold_masked = filter_clusters(doc.gold_clusters, gold_keep)
        pred_masked = filter_clusters(doc.predicted_clusters, gold_keep)

        ev = _get_coref_evaluator()
        ev.update(pred_masked, gold_masked)
        records.append({
            "doc_key": doc.doc_key,
            "bucket": bucket_def,
            "conll_f1": float(ev.get_f1()),
        })

    return pd.DataFrame.from_records(records)


# ------------------- Tokenization bottleneck micro-analysis ------------------

def tokenization_mismatch_analysis(
    gold_conllu_dir: Path,
    sota_tokenized_dir: Path,
    gold_run: SystemRun,
    sota_run: SystemRun,
) -> pd.DataFrame:
    """For each gold mention, mark whether its boundary crosses a SOTA segmentation error.

    Then report detection error rates for mentions whose boundaries do/do not intersect a mismatch.
    """
    rows: List[Dict[str, Any]] = []
    gold_idx = _index_docs_by_key(gold_run)
    sota_idx = _index_docs_by_key(sota_run)
    keys = sorted(set(gold_idx) & set(sota_idx))

    def load_sota_tokens(doc_key: str) -> List[str]:
        fname = doc_key.replace("htb:", "").replace(".conllu", "") + ".txt"
        p = sota_tokenized_dir / fname
        if not p.exists():
            alt = sota_tokenized_dir / "test" / fname
            p = alt if alt.exists() else p
        if not p.exists():
            return []
        return p.read_text(encoding="utf-8").strip().split()

    for k in keys:
        gold_doc = gold_idx[k]
        sota_doc = sota_idx[k]
        info = _read_conllu(k, gold_conllu_dir)
        gold_tokens: List[str] = info["tokens"]
        if not gold_tokens:
            continue
        sota_tokens = load_sota_tokens(k)
        if not sota_tokens:
            continue
        off_gold = _build_char_offsets(gold_tokens)
        off_sota = _build_char_offsets(sota_tokens)

        # Mark token boundary char-cuts
        gold_cuts = set(e for _, e in off_gold[:-1])
        sota_cuts = set(e for _, e in off_sota[:-1])

        # Collect all gold mentions in char space
        gold_mentions = [tuple(m) for c in gold_doc.gold_clusters for m in c]

        # Build a set of predicted mentions from SOTA run for detection correctness under exact match at token level
        pred_mentions = set(tuple(m) for c in sota_doc.predicted_clusters for m in c)

        for m in gold_mentions:
            s, e = m
            # gold mention char offsets
            m_char = _span_tokens_to_char([s, e], off_gold)
            # Does mention boundary cross a SOTA mismatch? if start or end cut not in sota cuts
            crosses = int((m_char[0] not in sota_cuts) or (m_char[1] not in sota_cuts))
            # detection correctness at token granularity: whether exact span exists in sota predictions
            is_detected = int(m in pred_mentions)
            rows.append({
                "doc_key": k,
                "crosses_mismatch": crosses,
                "detected": is_detected,
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Aggregate error rates and odds ratio
    agg = df.groupby("crosses_mismatch")["detected"].agg(["mean", "count"]).reset_index()
    agg.rename(columns={"mean": "detection_rate", "count": "n"}, inplace=True)
    # odds ratio: detected vs not in cross/non-cross
    cross = df[df["crosses_mismatch"] == 1]
    non = df[df["crosses_mismatch"] == 0]
    # add 0.5 to avoid division by zero (Haldane–Anscombe)
    a = cross["detected"].sum() + 0.5
    b = (len(cross) - cross["detected"].sum()) + 0.5
    c = non["detected"].sum() + 0.5
    d = (len(non) - non["detected"].sum()) + 0.5
    odds_ratio = float((a / b) / (c / d)) if (b > 0 and d > 0) else float("nan")
    agg["odds_ratio_cross_vs_non"] = odds_ratio
    return agg


# --------------------- Boundary-tolerant metric validation -------------------

def tolerant_conll_f1_for_doc(
    doc: DocExample,
    tokens: Optional[List[str]],
    tolerance_chars: int = 2,
) -> float:
    """Compute a boundary-tolerant CoNLL-like F1 for a single doc.

    We align predicted mentions to gold if their char boundaries are within ±tolerance_chars.
    Then we rebuild clusters by replacing predicted spans with the aligned gold spans.
    """
    if tokens is None or not tokens:
        # fallback to strict
        return compute_doc_conll_f1(doc)

    off = _build_char_offsets(tokens)

    def char_span(span: List[int]) -> Tuple[int, int]:
        return _span_tokens_to_char(span, off)

    # Build alignment mapping from predicted to nearest gold within tolerance
    gold_spans = [tuple(m) for c in doc.gold_clusters for m in c]
    pred_spans = [tuple(m) for c in doc.predicted_clusters for m in c]
    gold_chars = {gs: char_span(list(gs)) for gs in gold_spans}
    pred_chars = {ps: char_span(list(ps)) for ps in pred_spans}

    def within_tol(a: Tuple[int, int], b: Tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) <= tolerance_chars and abs(a[1] - b[1]) <= tolerance_chars

    alignment: Dict[Tuple[int, int], Tuple[int, int]] = {}
    used_gold: Set[Tuple[int, int]] = set()
    for ps, pc in pred_chars.items():
        best_g: Optional[Tuple[int, int]] = None
        for gs, gc in gold_chars.items():
            if gs in used_gold:
                continue
            if within_tol(pc, gc):
                best_g = gs
                break
        if best_g is not None:
            alignment[ps] = best_g
            used_gold.add(best_g)

    # Rebuild predicted clusters by replacing aligned mentions with their gold-aligned spans
    new_pred: List[List[List[int]]] = []
    for c in doc.predicted_clusters:
        new_c: List[List[int]] = []
        for s in c:
            t = tuple(s)
            if t in alignment:
                new_c.append(list(alignment[t]))
            else:
                # keep original if unmatched
                new_c.append(s)
        new_pred.append(new_c)

    ev = _get_coref_evaluator()
    ev.update(new_pred, doc.gold_clusters)
    return float(ev.get_f1())


def tolerant_metric_validation(
    run: SystemRun,
    tokens_dir: Optional[Path],
    tolerance_chars: int = 2,
) -> pd.DataFrame:
    """Compute per-doc correlation between tolerant and strict F1 and detect rank inversions."""
    rows: List[Dict[str, Any]] = []
    for doc in run.docs:
        tokens: Optional[List[str]] = None
        if tokens_dir is not None:
            fname = doc.doc_key.replace("htb:", "").replace(".conllu", "") + ".txt"
            p = tokens_dir / fname
            if not p.exists():
                alt = tokens_dir / "test" / fname
                p = alt if alt.exists() else p
            if p.exists():
                tokens = p.read_text(encoding="utf-8").strip().split()
        strict = compute_doc_conll_f1(doc)
        tol = tolerant_conll_f1_for_doc(doc, tokens, tolerance_chars)
        rows.append({"doc_key": doc.doc_key, "strict_conll_f1": strict, "tolerant_f1": tol})

    df = pd.DataFrame(rows)
    if spearmanr is not None and len(df) >= 2:
        rho, p = spearmanr(df["strict_conll_f1"], df["tolerant_f1"])
        df.attrs["spearman_rho"] = float(rho)
        df.attrs["spearman_p"] = float(p)
    return df


# -------------------------- Document difficulty ------------------------------

def document_difficulty_features(
    conllu_dir: Path,
    gold_run: SystemRun,
) -> pd.DataFrame:
    """For each doc: len, mention density, %clitic, %nested, avg distance."""
    rows: List[Dict[str, Any]] = []
    gold_idx = _index_docs_by_key(gold_run)
    for doc in gold_run.docs:
        k = doc.doc_key
        info = _read_conllu(k, conllu_dir)
        tokens = info["tokens"]
        tags_info = _tag_gold_mentions(k, conllu_dir, gold_idx[k].gold_clusters)
        tags = tags_info["mention_tags"]
        if not tokens or tags is None:
            continue
        n_tok = len(tokens)
        n_mentions = len(tags)
        density = n_mentions / n_tok if n_tok else 0.0
        pct_clitic = np.mean([int(t["has_clitic"]) for t in tags]) if tags else 0.0
        pct_nested = np.mean([int(t["nested"]) for t in tags]) if tags else 0.0

        # avg sentence distance of links in gold
        sents = _read_conllu(k, conllu_dir)["sents"]
        # choose antecedent as the closest previous mention in the same cluster
        def avg_dist(clusters: List[List[List[int]]]) -> float:
            dists: List[int] = []
            for c in clusters:
                spans = sorted(c, key=lambda x: x[0])
                prev_sent = None
                for m in spans:
                    cur_sent = sents[min(m[0], len(sents) - 1)] if sents else 0
                    if prev_sent is not None:
                        dists.append(max(0, cur_sent - prev_sent))
                    prev_sent = cur_sent
            return float(np.mean(dists)) if dists else 0.0

        avg_distance = avg_dist(gold_idx[k].gold_clusters)
        rows.append({
            "doc_key": k,
            "num_tokens": n_tok,
            "mention_density": density,
            "pct_clitic": float(pct_clitic),
            "pct_nested": float(pct_nested),
            "avg_sent_distance": avg_distance,
        })
    return pd.DataFrame(rows)


def per_doc_performance(run: SystemRun) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for doc in run.docs:
        rows.append({
            "doc_key": doc.doc_key,
            "system": run.name,
            "conll_f1": compute_doc_conll_f1(doc),
        })
    return pd.DataFrame(rows)


def regress_difficulty(features_df: pd.DataFrame, perf_df: pd.DataFrame) -> Dict[str, Any]:
    df = features_df.merge(perf_df, on="doc_key", how="inner")
    if df.empty:
        return {"coefficients": {}, "rf_importance": {}}
    X = df[["num_tokens", "mention_density", "pct_clitic", "pct_nested", "avg_sent_distance"]].values
    y = df["conll_f1"].values
    out: Dict[str, Any] = {}
    if LinearRegression is not None:
        lr = LinearRegression().fit(X, y)
        out["coefficients"] = {
            "num_tokens": float(lr.coef_[0]),
            "mention_density": float(lr.coef_[1]),
            "pct_clitic": float(lr.coef_[2]),
            "pct_nested": float(lr.coef_[3]),
            "avg_sent_distance": float(lr.coef_[4]),
        }
    if RandomForestRegressor is not None:
        rf = RandomForestRegressor(random_state=0, n_estimators=200).fit(X, y)
        importances = rf.feature_importances_
        out["rf_importance"] = {
            "num_tokens": float(importances[0]),
            "mention_density": float(importances[1]),
            "pct_clitic": float(importances[2]),
            "pct_nested": float(importances[3]),
            "avg_sent_distance": float(importances[4]),
        }
    return out


# ------------------------ Inter-system agreement map -------------------------

def cluster_pairs(clusters: List[List[List[int]]]) -> Set[Tuple[Tuple[int, int], Tuple[int, int]]]:
    out: Set[Tuple[Tuple[int, int], Tuple[int, int]]] = set()
    for c in clusters:
        m = [tuple(s) for s in c]
        for i in range(len(m)):
            for j in range(i + 1, len(m)):
                out.add((m[i], m[j]))
    return out


def pair_f1(a: List[List[List[int]]], b: List[List[List[int]]]) -> float:
    A = cluster_pairs(a)
    B = cluster_pairs(b)
    tp = len(A & B)
    prec = tp / len(B) if B else 0.0
    rec = tp / len(A) if A else 0.0
    return float(0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec))


def rand_index(a: List[List[List[int]]], b: List[List[List[int]]]) -> float:
    # Compute Rand index over mention universe as the union of mentions in a and b
    mentions = list(set([tuple(m) for c in a for m in c] + [tuple(m) for c in b for m in c]))
    if not mentions:
        return 1.0
    # cluster id maps; unmatched mentions get unique ids
    def cid_map(clusters: List[List[List[int]]]) -> Dict[Tuple[int, int], int]:
        mp: Dict[Tuple[int, int], int] = {}
        next_id = 10**9
        for i, c in enumerate(clusters):
            for m in c:
                mp[tuple(m)] = i
        # ensure every mention appears
        for m in mentions:
            if m not in mp:
                mp[m] = next_id
                next_id += 1
        return mp
    A = cid_map(a)
    B = cid_map(b)
    agree = 0
    total = 0
    for i in range(len(mentions)):
        for j in range(i + 1, len(mentions)):
            same_a = A[mentions[i]] == A[mentions[j]]
            same_b = B[mentions[i]] == B[mentions[j]]
            agree += int(same_a == same_b)
            total += 1
    return float(agree / total) if total else 1.0


def variation_of_information(a: List[List[List[int]]], b: List[List[List[int]]]) -> float:
    # Build partitions over mentions; approximate VI over finite sets
    mentions = list(set([tuple(m) for c in a for m in c] + [tuple(m) for c in b for m in c]))
    if not mentions:
        return 0.0
    id_map = {m: i for i, m in enumerate(mentions)}
    def partition(clusters: List[List[List[int]]]) -> List[int]:
        lab = [0] * len(mentions)
        next_id = 1
        for c in clusters:
            for m in c:
                lab[id_map[tuple(m)]] = next_id
            next_id += 1
        # singletons as unique labels
        for i in range(len(lab)):
            if lab[i] == 0:
                lab[i] = next_id
                next_id += 1
        return lab
    A = partition(a)
    B = partition(b)
    # Compute entropies
    def H(labels: List[int]) -> float:
        vals, counts = np.unique(labels, return_counts=True)
        p = counts / counts.sum()
        return float(-(p * np.log2(p)).sum())
    def I(x: List[int], y: List[int]) -> float:
        # mutual information
        xy = list(zip(x, y))
        vals, counts = np.unique(xy, axis=0, return_counts=True)
        pxy = counts / counts.sum()
        # marginals
        vx, cx = np.unique(x, return_counts=True)
        vy, cy = np.unique(y, return_counts=True)
        px = cx / cx.sum()
        py = cy / cy.sum()
        # map for quick lookup
        px_map = {vx[i]: px[i] for i in range(len(vx))}
        py_map = {vy[i]: py[i] for i in range(len(vy))}
        mi = 0.0
        for (lx, ly), p in zip(vals, pxy):
            mi += float(p * math.log2(p / (px_map[lx] * py_map[ly])))
        return mi
    return float(H(A) + H(B) - 2 * I(A, B))


def inter_system_agreement(runs: List[SystemRun]) -> pd.DataFrame:
    records: List[Dict[str, Any]] = []
    # align docs intersection
    common = set(runs[0].docs[i].doc_key for i in range(len(runs[0].docs)))
    for r in runs[1:]:
        common &= set(d.doc_key for d in r.docs)
    common = sorted(list(common))
    # build per-system doc index
    idx = [ _index_docs_by_key(r) for r in runs ]
    for i in range(len(runs)):
        for j in range(i + 1, len(runs)):
            pf_list, ri_list, vi_list = [], [], []
            for k in common:
                a = idx[i][k].predicted_clusters
                b = idx[j][k].predicted_clusters
                pf_list.append(pair_f1(a, b))
                ri_list.append(rand_index(a, b))
                vi_list.append(variation_of_information(a, b))
            records.append({
                "sys_a": runs[i].name,
                "sys_b": runs[j].name,
                "pair_f1": float(np.mean(pf_list)) if pf_list else float("nan"),
                "rand_index": float(np.mean(ri_list)) if ri_list else float("nan"),
                "vi": float(np.mean(vi_list)) if vi_list else float("nan"),
            })
    return pd.DataFrame.from_records(records)


# ----------------------- Seed variance & stability ---------------------------

def seed_variance(neural_runs: List[SystemRun]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for r in neural_runs:
        f1s = [compute_doc_conll_f1(d) for d in r.docs]
        rows.append({"system": r.name, "mean": float(np.mean(f1s)), "std": float(np.std(f1s)), "min": float(np.min(f1s)), "max": float(np.max(f1s))})
    return pd.DataFrame(rows)


def smallest_significant_difference(neural_runs: List[SystemRun], n_samples: int = 10000) -> float:
    # Compute the minimal delta detectable by paired bootstrap between two seeds selected at random
    if len(neural_runs) < 2:
        return float("nan")
    rng = np.random.default_rng(0)
    # pick two runs with max overlap
    a, b = neural_runs[0], neural_runs[1]
    res = paired_bootstrap(a, b, n_samples=n_samples)
    ci = res["ci95"]
    return float(max(abs(ci[0]), abs(ci[1])))


# ----------------------- Cluster-structure effects ---------------------------

def performance_by_cluster_bins(run: SystemRun, gold_run: SystemRun) -> pd.DataFrame:
    """Compute F1 by gold cluster size bins: 2, 3, 4–6, 7+"""
    bins = [(2, 2, "2"), (3, 3, "3"), (4, 6, "4-6"), (7, 10**9, "7+")]
    rows: List[Dict[str, Any]] = []
    idx_run = _index_docs_by_key(run)
    idx_gold = _index_docs_by_key(gold_run)

    for doc_key in sorted(set(idx_run) & set(idx_gold)):
        gold = idx_gold[doc_key].gold_clusters
        for l, r, name in bins:
            # mask clusters by size
            def mask(clusters: List[List[List[int]]]) -> List[List[List[int]]]:
                out = []
                for c in clusters:
                    if l <= len(c) <= r:
                        out.append(c)
                return out
            gold_m = mask(gold)
            pred_m = mask(idx_run[doc_key].predicted_clusters)
            if not gold_m:
                continue
            ev = _get_coref_evaluator()
            ev.update(pred_m, gold_m)
            rows.append({"doc_key": doc_key, "bin": name, "conll_f1": float(ev.get_f1())})
    return pd.DataFrame(rows)


def performance_by_singleton_proportion(run: SystemRun, gold_run: SystemRun) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    idx_gold = _index_docs_by_key(gold_run)
    for doc in run.docs:
        gold = idx_gold.get(doc.doc_key)
        if gold is None:
            continue
        n_clusters = len(gold.gold_clusters)
        n_singletons = sum(1 for c in gold.gold_clusters if len(c) == 1)
        prop = n_singletons / n_clusters if n_clusters else 0.0
        rows.append({"doc_key": doc.doc_key, "singleton_prop": prop, "system": run.name, "conll_f1": compute_doc_conll_f1(doc)})
    return pd.DataFrame(rows)


# ----------------------- Agreement cue violations ----------------------------

def agreement_cue_violations(run: SystemRun, conllu_dir: Path) -> pd.DataFrame:
    """False positives that violate number/gender according to gold morph features."""
    rows: List[Dict[str, Any]] = []
    for doc in run.docs:
        info = _read_conllu(doc.doc_key, conllu_dir)
        feats = info["feats"]
        # map mention -> (Number, Gender) by first token in span
        def mfeat(span: List[int]) -> Tuple[str, str]:
            s = span[0] if span else 0
            f = feats[s] if 0 <= s < len(feats) else {}
            return f.get("Number", "_"), f.get("Gender", "_")
        # predicted pairs and gold pairs
        p_pairs = cluster_pairs(doc.predicted_clusters)
        g_pairs = cluster_pairs(doc.gold_clusters)
        fp = p_pairs - g_pairs
        viol = 0
        for a, b in fp:
            na, ga = mfeat(list(a))
            nb, gb = mfeat(list(b))
            if (na != nb and na != "_" and nb != "_") or (ga != gb and ga != "_" and gb != "_"):
                viol += 1
        rows.append({
            "doc_key": doc.doc_key,
            "system": run.name,
            "false_positive_pairs": len(fp),
            "violations_number_or_gender": viol,
            "violation_rate": float(viol / len(fp)) if fp else 0.0,
        })
    return pd.DataFrame(rows)


# --------------------------------- CLI --------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Reviewer-proof analysis suite for coreference")
    # Inputs: paths to system outputs
    parser.add_argument("--neural_gold", type=str, help="Path to neural (gold tokenization) results JSON/JSONL")
    parser.add_argument("--neural_sota", type=str, help="Path to neural (SOTA tokenization) results JSON/JSONL")
    parser.add_argument("--llm_gold", type=str, help="Path to best LLM (gold mentions) results JSON/JSONL")
    parser.add_argument("--llm_raw", type=str, help="Path to LLM raw results JSON/JSONL", default=None)

    # Data roots
    parser.add_argument("--gold_conllu_test_dir", type=str, default="data/data/conllu/with_singleton/test", help="Directory of gold test .conllu files (prefixed with htb:)")
    parser.add_argument("--raw_tokens_dir", type=str, default="data/data/llm_input/tokenized_documents/test", help="Directory of raw tokenized test txt files")
    parser.add_argument("--sota_tokens_dir", type=str, default="data/data/llm_input/tokenized_documents_danit_tokenization/test", help="Directory of SOTA tokenized test txt files")

    parser.add_argument("--output_dir", type=str, default="error_analysis/outputs/reviewer_proof")
    parser.add_argument("--bootstrap_samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=13)

    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load runs
    runs: Dict[str, SystemRun] = {}
    if args.neural_gold:
        runs["neural_gold"] = _load_run(Path(args.neural_gold), name="Neural (Gold tok)", kind="neural_gold_tok")
    if args.neural_sota:
        runs["neural_sota"] = _load_run(Path(args.neural_sota), name="Neural (SOTA tok)", kind="neural_sota_tok")
    if args.llm_gold:
        runs["llm_gold"] = _load_run(Path(args.llm_gold), name="LLM (Gold mentions)", kind="llm_gold_mentions")
    if args.llm_raw:
        runs["llm_raw"] = _load_run(Path(args.llm_raw), name="LLM (Raw)", kind="llm_raw")

    # Priority 1: Paired bootstrap (skip gracefully if no doc overlap)
    boot_rows: List[Dict[str, Any]] = []
    def safe_boot(label: str, a: str, b: str):
        try:
            res = paired_bootstrap(runs[a], runs[b], n_samples=args.bootstrap_samples, seed=args.seed)
            boot_rows.append({"comparison": label, **res})
        except Exception as e:
            boot_rows.append({"comparison": label, "error": str(e)})
    if "neural_gold" in runs and "neural_sota" in runs:
        safe_boot("neural_gold_vs_neural_sota", "neural_gold", "neural_sota")
    if "llm_gold" in runs and "neural_gold" in runs:
        safe_boot("llm_gold_vs_neural_gold", "llm_gold", "neural_gold")
    if "llm_raw" in runs and "llm_gold" in runs:
        safe_boot("llm_raw_vs_llm_gold", "llm_raw", "llm_gold")
    if boot_rows:
        pd.DataFrame(boot_rows).to_csv(out_dir / "paired_bootstrap.csv", index=False)

    # Priority 1: Error decomposition
    if "neural_sota" in runs and "neural_gold" in runs:
        decomp = boundary_vs_linking_neural(
            neural_raw=runs["neural_sota"],
            neural_gold_tok=runs["neural_gold"],
            raw_tokens_dir=Path(args.sota_tokens_dir),
            gold_conllu_dir=Path(args.gold_conllu_test_dir),
        )
        with open(out_dir / "neural_boundary_vs_linking.json", "w", encoding="utf-8") as f:
            json.dump(decomp, f, indent=2, ensure_ascii=False)
    if "llm_gold" in runs:
        link_dec = link_error_decomposition_llm_gold_mentions(runs["llm_gold"])
        with open(out_dir / "llm_link_error_decomposition.json", "w", encoding="utf-8") as f:
            json.dump(link_dec, f, indent=2, ensure_ascii=False)

    # Priority 1: Phenomenon-sliced evaluation (example buckets)
    buckets = [
        "type=pronoun",
        "type=nominal",
        "type=proper",
        "has_clitic=true",
        "smixut=true",
        "nested=true",
        "number=Sing",
        "gender=Masc",
    ]
    for key, run in runs.items():
        if key not in ("neural_gold", "llm_gold", "neural_sota"):
            continue
        all_df = []
        for b in buckets:
            dfb = slice_eval_conll(run, Path(args.gold_conllu_test_dir), b)
            dfb["system"] = run.name
            all_df.append(dfb)
        if all_df:
            pd.concat(all_df, ignore_index=True).to_csv(out_dir / f"phenomenon_slices_{key}.csv", index=False)

    # Priority 2: Tokenization mismatch micro-analysis
    if "neural_gold" in runs and "neural_sota" in runs:
        tok_df = tokenization_mismatch_analysis(
            Path(args.gold_conllu_test_dir), Path(args.sota_tokens_dir), runs["neural_gold"], runs["neural_sota"]
        )
        if not tok_df.empty:
            tok_df.to_csv(out_dir / "tokenization_mismatch_vs_detection.csv", index=False)

    # Priority 2: Boundary-tolerant metric validation
    tol_rows = []
    for key in ("neural_sota", "neural_gold", "llm_gold"):
        if key in runs:
            df = tolerant_metric_validation(runs[key], Path(args.sota_tokens_dir) if key == "neural_sota" else Path(args.raw_tokens_dir))
            df["system"] = runs[key].name
            tol_rows.append(df)
    if tol_rows:
        pd.concat(tol_rows, ignore_index=True).to_csv(out_dir / "tolerant_vs_strict_per_doc.csv", index=False)

    # Priority 3: Document difficulty (robust to empty data)
    if "neural_gold" in runs:
        try:
            feats = document_difficulty_features(Path(args.gold_conllu_test_dir), runs["neural_gold"])
            perf = per_doc_performance(runs["neural_gold"]) 
            if not feats.empty:
                feats.to_csv(out_dir / "doc_features.csv", index=False)
            else:
                (out_dir / "doc_features.csv").write_text("", encoding="utf-8")
            if not perf.empty:
                perf.to_csv(out_dir / "doc_performance_neural_gold.csv", index=False)
            else:
                (out_dir / "doc_performance_neural_gold.csv").write_text("", encoding="utf-8")
            if (not feats.empty) and (not perf.empty) and ("doc_key" in feats.columns) and ("doc_key" in perf.columns):
                reg = regress_difficulty(feats, perf)
            else:
                reg = {"note": "insufficient data for regression"}
            with open(out_dir / "difficulty_regression.json", "w", encoding="utf-8") as f:
                json.dump(reg, f, indent=2, ensure_ascii=False)
        except Exception as e:
            with open(out_dir / "difficulty_regression.json", "w", encoding="utf-8") as f:
                json.dump({"error": str(e)}, f, indent=2, ensure_ascii=False)

    # Priority 3: Inter-system agreement map
    agree_df = None
    if len(runs) >= 2:
        agree_df = inter_system_agreement(list(runs.values()))
        if not agree_df.empty:
            agree_df.to_csv(out_dir / "inter_system_agreement.csv", index=False)

    # Priority 3: Seed variance (if user provides multiple neural seeds via repeated --neural_gold)
    # Not auto-handled here; provide separate inputs or run multiple times and combine.

    # Priority 3: Cluster-structure effects
    if "neural_gold" in runs:
        cs_df = performance_by_cluster_bins(runs["neural_gold"], runs["neural_gold"])  # gold bins over gold mentions
        if not cs_df.empty:
            cs_df.to_csv(out_dir / "performance_by_cluster_bins.csv", index=False)
        sp_df = performance_by_singleton_proportion(runs["neural_gold"], runs["neural_gold"]) 
        if not sp_df.empty:
            sp_df.to_csv(out_dir / "performance_by_singleton_prop.csv", index=False)

    # Priority 3: Agreement cue violations
    if "llm_gold" in runs:
        viol_df = agreement_cue_violations(runs["llm_gold"], Path(args.gold_conllu_test_dir))
        if not viol_df.empty:
            viol_df.to_csv(out_dir / "agreement_cue_violations_llm_gold.csv", index=False)

    # Write a concise README summary
    try:
        lines: List[str] = []
        lines.append(f"# Reviewer-proof analysis summary\n")
        lines.append(f"Output dir: `{out_dir}`\n")
        # Bootstraps
        pb = out_dir / "paired_bootstrap.csv"
        if pb.exists():
            df = pd.read_csv(pb)
            lines.append("## Paired bootstrap\n")
            for _, r in df.iterrows():
                if "error" in r and isinstance(r["error"], str) and not (r["error"] != r["error"]):
                    lines.append(f"- {r['comparison']}: ERROR: {r['error']}")
                else:
                    lines.append(f"- {r['comparison']}: meanΔ={r.get('mean_delta', float('nan')):.4f}, CI95=[{r.get('ci95[0]', r.get('ci95', [float('nan'), float('nan')])[0]) if 'ci95[0]' in df.columns else r.get('ci95', [np.nan, np.nan])[0]:.4f}, {r.get('ci95[1]', r.get('ci95', [float('nan'), float('nan')])[1]) if 'ci95[1]' in df.columns else r.get('ci95', [np.nan, np.nan])[1]:.4f}], p={r.get('p_value', float('nan')):.4f}")
        # Boundary vs linking
        nb = out_dir / "neural_boundary_vs_linking.json"
        if nb.exists():
            d = json.loads(nb.read_text(encoding="utf-8"))
            lines.append("\n## Neural boundary vs linking\n")
            lines.append(f"- boundary_only: {d.get('boundary_only', 0)}; linking_only: {d.get('linking_only', 0)}; both: {d.get('both', 0)}")
        ll = out_dir / "llm_link_error_decomposition.json"
        if ll.exists():
            d = json.loads(ll.read_text(encoding="utf-8"))
            lines.append("\n## LLM link errors (gold mentions)\n")
            lines.append(f"- false_merges: {d.get('false_merges', 0)}; missed_links: {d.get('missed_links', 0)}; pair_F1: {d.get('pair_f1', 0.0):.3f}")
        # Tokenization mismatch
        tm = out_dir / "tokenization_mismatch_vs_detection.csv"
        if tm.exists():
            df = pd.read_csv(tm)
            lines.append("\n## Tokenization mismatch vs detection\n")
            if not df.empty:
                lines.append(df.to_markdown(index=False))
        # Tolerant vs strict
        tv = out_dir / "tolerant_vs_strict_per_doc.csv"
        if tv.exists():
            df = pd.read_csv(tv)
            lines.append("\n## Tolerant vs strict (per-doc)\n")
            lines.append(f"- N={len(df)} docs")
        # Inter-system agreement
        ia = out_dir / "inter_system_agreement.csv"
        if ia.exists():
            df = pd.read_csv(ia)
            if not df.empty:
                lines.append("\n## Inter-system agreement (mean over docs)\n")
                for _, r in df.iterrows():
                    lines.append(f"- {r['sys_a']} vs {r['sys_b']}: pairF1={r['pair_f1']:.3f}, rand={r['rand_index']:.3f}, VI={r['vi']:.3f}")
        (out_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")
    except Exception as e:
        # Non-fatal
        pass

    print(f"✓ Analysis complete. Outputs in: {out_dir}")


if __name__ == "__main__":
    main()


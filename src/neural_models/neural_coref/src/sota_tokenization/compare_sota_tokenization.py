#!/usr/bin/env python3
"""
compare_clusters.py  —  cluster-by-cluster diff for Hebrew-coref JSON-lines files.

USAGE
-----
python compare_clusters.py \
    --orig  /path/to/original/test.hebrew.jsonlines \
    --new   /path/to/new_test.hebrew.jsonlines \
    [--doc  nw/3]            # only this doc_key
    [--context 6]            # # tokens around first span preview
    [--width 110]            # max line width
"""
import argparse, json, itertools, shutil, textwrap
from collections import namedtuple

Span   = namedtuple("Span",   ["s", "e"])
CLHDR  = "idx │ original cluster                              │ new cluster"
SEP    = "─"*len(CLHDR)

def load_docs(fp):
    out = {}
    with open(fp, encoding="utf-8") as fh:
        for ln in fh:
            d = json.loads(ln)
            out[d["doc_key"]] = d
    return out

def spans_of_cluster(cl):
    return [Span(s, e) for s, e in cl]

def cluster_key(cl):
    """(min_start, max_end) for ordering clusters."""
    starts  = [s for s, _ in cl]
    ends    = [e for _, e in cl]
    return (min(starts), max(ends))

def preview(tokens, span, ctx):
    """Return a short “… left >>>mid<<< right …” preview for one span."""
    s, e = span            # span is [start, end]
    left  = " ".join(tokens[max(0, s - ctx): s])
    mid = " ".join(tokens[s:e])  # no +1
    right = " ".join(tokens[e:e + ctx])
    return f"... {left} >>>{mid}<<< {right} ..."

def format_cluster(tokens, cl, ctx, width):
    if not cl:
        return "—"
    spans_txt = ", ".join(f"[{s},{e}]" for s, e in cl)
    # pick the span with the earliest start for preview
    first_span = min(cl, key=lambda x: x[0])
    sneak = preview(tokens, first_span, ctx)
    txt = f"{spans_txt}  {sneak}"
    return (txt[: width - 3] + "…") if len(txt) > width else txt

from itertools import zip_longest
try:
    from colorama import Fore, Style, init as color_init
    color_init()
    BOLD = Style.BRIGHT
    RESET = Style.RESET_ALL
    ORG  = Fore.CYAN + BOLD
    NEW  = Fore.MAGENTA + BOLD
except ImportError:   # colour is optional
    ORG = NEW = BOLD = RESET = ""

def words(tokens, span):
    s, e = span
    return " ".join(tokens[s:e])     # <— current (inclusive)

def cluster_diff(o_doc, n_doc, ctx):
    def sort_key(cl):
        starts = [s for s, _ in cl]
        ends   = [e for _, e in cl]
        return (min(starts), max(ends))

    o_cls = sorted(o_doc["clusters"], key=sort_key)
    n_cls = sorted(n_doc["clusters"], key=sort_key)
    max_len = max(len(o_cls), len(n_cls))

    lines = []
    sep = "-"*72
    for i in range(max_len):
        o = o_cls[i] if i < len(o_cls) else []
        n = n_cls[i] if i < len(n_cls) else []

        lines.append(f"[{i}]")
        # build two aligned columns (span → words) for orig / new
        o_rows = [f"{ORG}[{s},{e}]{RESET} {words(o_doc['cased_words'], (s,e))}"
                  for s,e in o] or ["—"]
        n_rows = [f"{NEW}[{s},{e}]{RESET} {words(n_doc['cased_words'], (s,e))}"
                  for s,e in n] or ["—"]

        pad = max(len(x) for x in o_rows) + 4
        for left, right in zip_longest(o_rows, n_rows, fillvalue=""):
            lines.append(f"    {left:<{pad}}{right}")
        lines.append(sep)
    return "\n".join(lines)
# ----------------------------------------------------------------

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--orig", required=True)
    p.add_argument("--new",  required=True)
    p.add_argument("--doc")
    p.add_argument("--context", type=int, default=6)
    p.add_argument("--width",   type=int, default=shutil.get_terminal_size().columns)
    args = p.parse_args()

    orig_docs = load_docs(args.orig)
    new_docs  = load_docs(args.new)

    keys = [args.doc] if args.doc else sorted(
        (set(orig_docs) & set(new_docs)),
        key=lambda k: len(orig_docs[k]["cased_words"])
    )
    if not keys:
        raise SystemExit("❌  No overlapping doc_keys found!")

    for k in keys:
        print(f"\n=== {k}  (len={len(orig_docs[k]['cased_words'])}) ===")
        print(cluster_diff(orig_docs[k], new_docs[k], args.context))


if __name__ == "__main__":
    main()

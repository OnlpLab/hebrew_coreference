#!/usr/bin/env python3
"""
fix_clusters.py  ―  clean-up and align the *new* segmentation file.

USAGE
-----
python fix_clusters.py \
    --orig  /path/to/original/test.hebrew.jsonlines \
    --new   /path/to/new_test.hebrew.jsonlines  \
    --out   /path/to/new_test.fixed.jsonlines   # default = *.fixed.jsonlines

A coloured diff is shown for every doubtful mention; press:

  ↵ / k    keep it as-is
  f        enter a replacement span as "start,end"
  d        delete this mention from the cluster
  q        abort the entire run

The script never touches the *orig* file; it rewrites *new* (to --out).
-----------------------------------------------------------------------------
Heuristics handled automatically
--------------------------------
✓ trailing punctuation inside the span (.,;:!?…)
✓ superfluous 'של' + pronoun after a *pronoun* base  (הוא → של הוא)
✓ extra/missing leading definite-article 'ה'
✓ clitic expansions  (בוקו ↔ בוק של הוא ; בברכו ↔ ברך של הוא)
✓ underscore tokens produced by some segmenters  (_הוא ↔ הוא)

Anything else is considered *dubious* and triggers the interactive prompt.
"""
import argparse, json, sys, shutil, textwrap
from pathlib import Path
from itertools import zip_longest
from collections import defaultdict, namedtuple

Span = namedtuple("Span", ["s", "e"])          # inclusive-exclusive
PUNCT = {".", ",", ";", ":", "!", "?", "…", "״", "׳", "”", "“", "־", "-", "–", "—"}
PRONOUNS = {"אני","את","אתה","הוא","היא","אנחנו","אתם","אתן","הם","הן"}

# ---------------------------------------------------------------------------#
#                    small helpers                                           #
# ---------------------------------------------------------------------------#
def load_jsonl(path):
    docs = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            docs[d["doc_key"]] = d
    return docs

def save_jsonl(path, docs):
    with open(path, "w", encoding="utf-8") as fh:
        for d in docs.values():
            fh.write(json.dumps(d, ensure_ascii=False)+"\n")

def strip_token(tok):
    """remove leading '_' and trailing punctuation"""
    tok = tok.lstrip("_")
    while tok and tok[-1] in PUNCT:
        tok = tok[:-1]
    return tok

def norm(tokens):
    """normalised form for fuzzy comparison"""
    out = [strip_token(t) for t in tokens]
    out = ["ה" if t=="ה" else t for t in out]    # normalise bare 'ה'
    return [t for t in out if t]                 # drop empties

def tokens(doc, span):
    s,e = span
    return doc["cased_words"][s:e]

def span_str(span):      # nice print
    return f"[{span[0]},{span[1]}]"

def print_context(doc, span, pad=6, width=120):
    """... left >>>mention<<< right ..."""
    s,e = span
    toks = doc["cased_words"]
    left  = " ".join(toks[max(0,s-pad):s])
    mid   = " ".join(toks[s:e])
    right = " ".join(toks[e:e+pad])
    msg = f"... {left} >>>{mid}<<< {right} ..."
    if len(msg) > width:
        return msg[:width-1]+"…"
    return msg

# ---------------------------------------------------------------------------#
#       heuristics: is_equivalent?  auto_fix()                               #
# ---------------------------------------------------------------------------#
# ---------------------------------------------------------------------------#
#  NEW helpers for softer matching                                           #
# ---------------------------------------------------------------------------#
HEB_PROCLITICS = "והבלכמש"          # ו-, ה-, ב-, ל-, כ-, מ-, ש-

def token_base(tok: str) -> str:
    """strip leading proclitic letters (but keep the stem)."""
    tok = strip_token(tok)          # remove '_' and trailing punct.
    while len(tok) > 1 and tok[0] in HEB_PROCLITICS:
        tok = tok[1:]
    return tok

def base_tokens(toks):
    """canonical token list:
         – drop stand-alone ו
         – strip proclitics + punctuation/underscores
         – keep order"""
    out = []
    for t in toks:
        t = strip_token(t)
        if t in {"", "ו"}:          # ignore bare conjunction
            continue
        out.append(token_base(t))
    return out
# ---------------------------------------------------------------------------#
#  IMPROVED equivalence test                                                 #
# ---------------------------------------------------------------------------#
def is_equivalent(orig_toks, new_toks):
    """Looser, Hebrew-aware equivalence.

       ▸ exact match after strong normalisation      (old rule)
       ▸ match after deleting stand-alone ו           (new)
       ▸ same first & last token and |Δ|≤1           (new)
       ▸ one-char edit apart (e.g. למחר / ל מחר)     (new)"""

    # 0. strong normalisation from the previous version
    o = norm(orig_toks)
    n = norm(new_toks)
    if o == n:
        return True

    # 1. ignore extra ו-tokens that are alone
    if [t for t in o if t != "ו"] == [t for t in n if t != "ו"]:
        return True

    # 2. compare *bases* (drop proclitics etc.)
    ob = base_tokens(orig_toks)
    nb = base_tokens(new_toks)
    if ob == nb:
        return True
    if (abs(len(ob) - len(nb)) <= 1
        and ob and nb
        and token_base(ob[0]) == token_base(nb[0])
        and token_base(ob[-1]) == token_base(nb[-1])):
        return True

    # 3. final safety-net: tiny char-edit distance
    def joined(xs): return "".join(base_tokens(xs))
    s1, s2 = joined(orig_toks), joined(new_toks)
    if abs(len(s1) - len(s2)) <= 1 and _levenshtein(s1, s2) <= 1:
        return True

    return False

# ---------------------------------------------------------------------------#
#   Interactive approval for each *auto-fix*                                 #
def approve_fix(doc, old_span, new_span, cluster):
    """Show before/after preview, ask, *then* re-print the cluster."""
    print("\n🔧 auto-fix candidate")
    print("OLD :", span_str(old_span), print_context(doc, old_span))
    print("NEW :", span_str(new_span), print_context(doc, new_span))
    while True:
        ans = input("accept [y] / [e]dit / [d]rop / [q]uit > ").strip().lower()
        if ans in {"y", "e", "d", "q"}:
            break
    if ans == "q":
        sys.exit("aborted.")

    if ans == "d":
        cluster.remove(old_span)              # will vanish
        res = None
    elif ans == "e":
        s, e = input("  enter corrected start,end > ").split(",")
        res = (int(s), int(e))
        old_span[:] = res
    else:                                     # ans == "y"
        res = new_span
        old_span[:] = res

    # ---- live cluster preview ----
    print("\n   🆕 cluster after your choice")
    spans = ", ".join(f"[{s},{e}]" for s, e in cluster)
    mots  = "; ".join(" ".join(doc['cased_words'][s:e]) for s, e in cluster)
    print("   ", spans)
    print("    ", mots, "\n")
    return res

# ---------------------------------------------------------------------------#
# tiny Levenshtein (length ≤ ~30 so O(N²) is fine)
def _levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1,      # deletion
                            curr[-1] + 1,     # insertion
                            prev[j - 1] + cost))  # sub
        prev = curr
    return prev[-1]

def auto_fix(orig_doc, orig_span, new_doc, new_span):
    """
    Return a *cleaner* span (tuple) or None.

    – If the NEW span ends with one or more tokens that strip to “”,
      AND the ORIGINAL span’s last token does **not** end with punctuation,
      those extra tokens are dropped.
    – All previous rules (של-pronoun, leading ה, …) stay intact.
    """
    def is_punct_only(tok):
        """True if token becomes empty after we strip punctuation & underscores"""
        return strip_token(tok) == ""


    s, e = new_span
    n_toks = new_doc["cased_words"]


    while e > s and is_punct_only(n_toks[e - 1]):
        e -= 1

    if (s, e) != new_span:
        return (s, e)                       # we shortened the span

    # 2. drop leading “של” before pure pronoun
    if e - s >= 2 and n_toks[s] == "של" and n_toks[s + 1] in PRONOUNS:
        return (s + 1, e)

    # 3. drop leading definite-article “ה” if rest identical
    if e - s >= 2 and n_toks[s] == "ה":
        return (s + 1, e)

    return None                             # nothing to fix


def align_spans(o_cls, n_cls, o_doc, n_doc):
    """
    Return list[(orig_span or None, new_span or None)], using:
      1) exact/relaxed token equivalence  (is_equivalent)
      2) maximal token-index overlap
      3) anything left  → unmatched
    """
    pairs      = []
    n_unused   = n_cls.copy()

    for o in o_cls:
        best   = None
        score  = -1
        for n in n_unused:
            if is_equivalent(tokens(o_doc, o), tokens(n_doc, n)):
                best, score = n, 999          # perfect!
                break

            # overlap score = size of intersection
            inter = max(0, min(o[1], n[1]) - max(o[0], n[0]))
            if inter > score:
                best, score = n, inter

        if best:
            pairs.append((o, best))
            n_unused.remove(best)
        else:
            pairs.append((o, None))

    # new mentions that never matched any original
    pairs.extend([(None, n) for n in n_unused])
    return pairs

# ---------------------------------------------------------------------------#
#                         main loop                                          #
# ---------------------------------------------------------------------------#
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", required=True)
    ap.add_argument("--new",  required=True)
    ap.add_argument("--out",  help="target file for the fixed NEW (default: *.fixed.jsonlines)")
    args = ap.parse_args()

    orig = load_jsonl(args.orig)
    new  = load_jsonl(args.new)

    out_file = args.out or str(Path(args.new).with_suffix(".fixed.jsonlines"))
    keys = sorted(set(orig) & set(new))
    if not keys:
        sys.exit("❌  No overlapping doc_keys between the two files.")

    for k in keys:
        o_doc = orig[k]
        n_doc = new[k]

        for cl_idx, (o_cl, n_cl) in enumerate(zip_longest(o_doc["clusters"], n_doc["clusters"], fillvalue=[])):
            # align by position, not by *identity* -- same assumption as compare_clusters.py
            for m_idx, (o_span, n_span) in enumerate(
                    align_spans(o_cl, n_cl, o_doc, n_doc)):

                if n_span is None:
                    # missing mention – ask user
                    print(f"\n{k}  cluster {cl_idx}  mention {m_idx}  🟥  missing in NEW")
                    print("ORIG :", span_str(o_span), print_context(o_doc, o_span))
                    choice = input("Fix options: [c]reate | s[k]ip | [q]uit > ").strip().lower()
                    if choice=="q": sys.exit("aborted.")
                    if choice=="c":
                        s,e = input("new span start,end > ").split(",")
                        n_cl.append([int(s),int(e)])
                    continue

                orig_ok = is_equivalent(tokens(o_doc, o_span), tokens(n_doc, n_span))
                if orig_ok:
                    continue                    # all good

                # try automatic repair
                fixed = auto_fix(o_doc, o_span, n_doc, n_span)
                if fixed and fixed != tuple(n_span):            # span *changed*
                    # keep the fix only if it still matches the original mention
                    if is_equivalent(tokens(o_doc, o_span),
                                     tokens(n_doc, fixed)):
                        # ask you first ─ approve / edit / drop
                        choice = approve_fix(n_doc, n_span, fixed, n_cl)
                        if choice is None:            # you chose “drop”
                            n_cl.remove(n_span)
                        else:
                            n_span[:] = choice        # accept / edited
                        continue                      # move on to next mention

                if fixed and is_equivalent(tokens(o_doc, o_span), tokens(n_doc, fixed)):
                    choice = approve_fix(n_doc, n_span, fixed, n_cl)
                    if choice is None:               # user chose "drop"
                        n_cl.remove(n_span)
                    else:
                        n_span[:] = choice           # accept / edited
                    continue

                # === interactive ===
                print("\n🟡 doubtful alignment — decide manually")
                print(f"{k}  cluster {cl_idx}  mention {m_idx}")
                print("ORIG :", span_str(o_span), print_context(o_doc, o_span))
                print("NEW  :", span_str(n_span), print_context(n_doc, n_span))
                while True:
                    choice = input("[k]eep / [f]ix / [d]elete / [q]uit > ").strip().lower()
                    if choice in {"k","f","d","q"}: break
                if choice=="q": sys.exit("aborted.")
                if choice=="d":
                    n_cl.remove(n_span)
                elif choice=="f":
                    s,e = input("enter corrected start,end > ").split(",")
                    n_span[:] = (int(s),int(e))
                # keep ↵ does nothing

    def canonical(span, doc_words):
        """Return span after dropping any RHS punctuation-only tokens."""
        s, e = span
        while e > s and strip_token(doc_words[e - 1]) == "":
            e -= 1
        return (s, e)

    for k, n_doc in new.items():
        words = n_doc["cased_words"]
        for cl in n_doc["clusters"]:
            # trim RHS punctuation
            trimmed = [canonical(tuple(span), words) for span in cl]

            # drop duplicates while preserving order
            seen = set()
            new_cl = []
            for s in trimmed:
                if s not in seen:
                    seen.add(s)
                    new_cl.append(list(s))
            cl[:] = new_cl

    # -------- write output --------
    save_jsonl(out_file, new)
    print(f"\n✅  Fixed file written to: {out_file}")

if __name__ == "__main__":
    main()
"""
Script to convert coreference clusters from a Hebrew dataset with a gold tokenization
to a new dataset aligned with a SOTA tokenization.  The original dataset is
stored in JSON‑lines format, where each line contains a document with keys
``cased_words``, ``sent_id``, ``part_id``, ``doc_key``, ``sentences``,
``speakers`` and ``clusters``.  The new tokenization is provided as plain
text files under a directory; every file corresponds to a document and
contains a space‑separated list of tokens.

The goal of this script is twofold:

1. Establish a mapping from the new tokenization files back to the
   corresponding documents in the original test set.  Because the new
   tokenizer assigns different identifiers (file names) to the documents,
   this mapping cannot rely on filename similarity alone.  Instead, the
   script compares the content of each new document (after normalising
   underscores) to the content of every original document and selects the
   best matching pair.

2. For each matched document pair, align the original tokens with the new
   tokens and adjust the coreference cluster indices accordingly.  The
   alignment uses a token‑level sequence matcher.  Whenever the number of
   tokens differs in a replacement block, the algorithm distributes the
   replacement span over the original tokens proportionally so that each
   original token maps to a contiguous span of new tokens.  This handles
   both cases where multiple original tokens are merged into a single new
   token (e.g. "ה" + "פועל" → "הפועל") and where a single original token
   is split into multiple new tokens (e.g. "הורי" → "הורה" "של" "הם").

The output of the script is a new JSON‑lines file containing documents with
the same format as the original test set but using the SOTA tokenization
for ``cased_words``, ``sentences`` and ``sent_id``.  The cluster indices
refer to positions in the new tokenization.

This script is intended to be run from the command line.  Typical usage::

    python answer.py \
      --original /Users/s0g0a87/studies/neural_hebrew_coref/data/lingmess/hebrew/test.hebrew.jsonlines \
      --tokenized /Users/s0g0a87/studies/coref-llms/data_coref/hebrew/tokenized_documents_danit_tokenization/test \
      --output /path/to/new_test.hebrew.jsonlines

Because the SOTA tokenized test set uses different file names and a
different tokenization scheme, this script reads all original documents
into memory and then processes each new file one by one.  If your data is
large, you may want to optimise the mapping stage or provide an explicit
mapping table.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Sequence, Tuple


def read_original_documents(path: str) -> List[Dict]:
    """Load the original test set.

    Each line in the given file is a JSON object representing a single
    document.  The function reads all lines, decodes the JSON and
    normalises the token lists by stripping underscores for matching.

    Parameters
    ----------
    path: str
        Path to the original JSON lines file.

    Returns
    -------
    List[Dict]
        A list of dictionaries containing the original document data along
        with additional helper fields used for matching.
    """
    docs = []
    with open(path, "r", encoding="utf‑8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to decode JSON on line {line_num}: {e}") from e
            # Create a normalised string without underscores for matching
            orig_tokens = doc["cased_words"]
            normalised = ''.join(tok.replace('_', '') for tok in orig_tokens)
            doc["_normalised"] = normalised
            docs.append(doc)
    return docs


def read_tokenized_documents(directory: str) -> Dict[str, List[str]]:
    """Read all tokenised documents from the given directory.

    The directory should contain one file per document.  Each file is
    expected to contain a single line of space‑separated tokens.  The
    function returns a dictionary mapping file names to lists of tokens.

    Parameters
    ----------
    directory: str
        Path to the directory containing the SOTA tokenised files.

    Returns
    -------
    Dict[str, List[str]]
        A mapping from the filename (without directory) to the list of
        tokens.  Tokens are kept as read; no underscores are stripped here
        because they may be meaningful in the new tokenization.
    """
    tokenized: Dict[str, List[str]] = {}
    for fname in sorted(os.listdir(directory)):
        fpath = os.path.join(directory, fname)
        if not os.path.isfile(fpath):
            continue
        with open(fpath, "r", encoding="utf‑8") as f:
            content = f.read().strip()
            # split on whitespace to obtain tokens
            # Keep the exact token strings; do not normalise underscores here.
            tokens = content.split()
            tokenized[fname] = tokens
    return tokenized


def match_documents(
    original_docs: List[Dict], tokenized_docs: Dict[str, List[str]]
) -> Dict[str, Dict]:
    """Match each tokenised document with its corresponding original document.

    The matching is performed by comparing the concatenated characters of
    the tokens (with underscores removed) of the original document to the
    concatenated characters of the new tokenisation (also with underscores
    removed).  A perfect match (identical strings) is preferred.  If no
    perfect match exists, the function falls back to selecting the document
    with the highest similarity ratio computed by :class:`SequenceMatcher`.

    Parameters
    ----------
    original_docs: List[Dict]
        List of original document objects read from the JSON lines file.

    tokenized_docs: Dict[str, List[str]]
        Mapping from tokenised file names to lists of tokens.

    Returns
    -------
    Dict[str, Dict]
        A mapping from tokenised file names to the matched original document.

    Notes
    -----
    This step assumes that each new document corresponds to exactly one
    original document.  If multiple tokenised files happen to match the
    same original document equally well, only the first match is returned.
    """
    matches: Dict[str, Dict] = {}
    used_original_keys = set()
    # Precompute normalised strings for tokenised docs
    tokenised_norm: Dict[str, str] = {
        fname: ''.join(tok.replace('_', '') for tok in tokens)
        for fname, tokens in tokenized_docs.items()
    }
    for fname, norm in tokenised_norm.items():
        best_score = 0.0
        best_doc: Optional[Dict] = None
        for doc in original_docs:
            if doc["doc_key"] in used_original_keys:
                continue
            doc_norm = doc["_normalised"]
            if norm == doc_norm:
                best_doc = doc
                best_score = 1.0
                break
            # Otherwise compute similarity ratio
            # Use SequenceMatcher on strings because the strings may be long.
            # Only compute ratio if lengths are comparable to avoid huge cost.
            # If ratio is high, keep candidate.
            # This is expensive but manageable for small datasets.
            sm = SequenceMatcher(None, norm, doc_norm)
            score = sm.ratio()
            if score > best_score:
                best_score = score
                best_doc = doc
        if best_doc is not None:
            print(score, best_doc["doc_key"])
            matches[fname] = best_doc
            used_original_keys.add(best_doc["doc_key"])
        else:
            raise ValueError(f"Could not find a matching original document for tokenised file {fname}")
    return matches


def compute_alignment(
    orig_tokens: Sequence[str], new_tokens: Sequence[str]
) -> Dict[int, Tuple[int, int]]:
    """Align original tokens with new tokens and build an index mapping.

    The alignment uses :class:`difflib.SequenceMatcher` at the token level.
    For each original token index *i*, the function returns a pair
    ``(new_start, new_end)`` indicating the range of new token indices that
    correspond to the original token.  Ranges are inclusive.  If an
    original token does not align to any new tokens (because it was
    completely deleted), the mapping value is ``(-1, -1)``.

    Parameters
    ----------
    orig_tokens: Sequence[str]
        List of tokens from the original document (cased_words).

    new_tokens: Sequence[str]
        List of tokens from the new tokenisation.

    Returns
    -------
    Dict[int, Tuple[int, int]]
        A dictionary mapping each original token index to a tuple
        ``(new_start, new_end)``.  Start and end are indices into
        ``new_tokens``.  A value of (-1, -1) indicates that the original
        token was deleted in the new tokenisation.  The function never
        produces decreasing ranges; if the computed end would be less than
        the start, the end is set equal to the start.
    """
    matcher = SequenceMatcher(a=list(orig_tokens), b=list(new_tokens))
    mapping: Dict[int, Tuple[int, int]] = {}
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for offset in range(i2 - i1):
                orig_index = i1 + offset
                new_index = j1 + offset
                mapping[orig_index] = (new_index, new_index)
        elif tag == 'replace':
            # A block in the original is replaced by another block in the new tokenisation.
            # We distribute the new span evenly over the original tokens.
            m = i2 - i1  # number of original tokens
            n = j2 - j1  # number of new tokens
            for k in range(m):
                orig_index = i1 + k
                if n == 0:
                    # Nothing in new; token deleted
                    mapping[orig_index] = (-1, -1)
                    continue
                # Compute the start and end of the slice in the new tokens
                start = j1 + int(round((k * n) / m))
                end = j1 + int(round(((k + 1) * n) / m)) - 1
                # Clamp the end to be at least the start and at most j2-1
                if end < start:
                    end = start
                if end >= j2:
                    end = j2 - 1
                mapping[orig_index] = (start, end)
        elif tag == 'delete':
            # Original tokens were deleted entirely (no corresponding new tokens).
            for orig_index in range(i1, i2):
                mapping[orig_index] = (-1, -1)
        elif tag == 'insert':
            # Tokens inserted in the new sequence; no original tokens map to them.
            # Nothing to do here.
            continue
        else:
            raise ValueError(f"Unhandled opcode tag: {tag}")
    return mapping


def update_clusters(
    clusters: List[List[List[int]]], mapping: Dict[int, Tuple[int, int]]
) -> List[List[List[int]]]:
    """Update coreference clusters according to the token alignment mapping.

    Parameters
    ----------
    clusters: List[List[List[int]]]
        The original cluster annotations.  Each cluster is a list of spans,
        where a span is a two‑element list ``[start, end]`` of inclusive
        token indices referring to the original tokenisation.

    mapping: Dict[int, Tuple[int, int]]
        Mapping from original token indices to ranges of new token indices.

    Returns
    -------
    List[List[List[int]]]
        A new list of clusters with spans updated to refer to the new
        tokenisation.  Spans mapping to deleted tokens are discarded.

    Notes
    -----
    If an original span maps partially to deleted tokens (i.e. some of its
    tokens were removed in the new tokenisation), only the portion that can
    be aligned is kept.  If the entire span is deleted, it will not
    appear in the output.  Adjacent or overlapping spans in the new
    tokenisation are not merged; the function preserves the structure of
    the original cluster list of lists.
    """
    new_clusters: List[List[List[int]]] = []
    for cluster in clusters:
        new_cluster: List[List[int]] = []
        for span in cluster:
            orig_start, orig_end = span
            # Determine the new start and end positions by consulting the mapping
            # Because a single original token may map to multiple new tokens,
            # we choose the minimal start and maximal end over the span.
            new_start: Optional[int] = None
            new_end: Optional[int] = None
            for orig_idx in range(orig_start, orig_end + 1):
                if orig_idx not in mapping:
                    continue
                s, e = mapping[orig_idx]
                if s == -1 and e == -1:
                    # This original token has no alignment in the new sequence.
                    continue
                if new_start is None or s < new_start:
                    new_start = s
                if new_end is None or e > new_end:
                    new_end = e
            if new_start is not None and new_end is not None:
                new_cluster.append([new_start, new_end])
        if new_cluster:
            new_clusters.append(new_cluster)
    return new_clusters


def map_new_tokens_to_original(mapping: Dict[int, Tuple[int, int]], new_len: int) -> List[Optional[int]]:
    """Create a reverse mapping from new token indices to an original token index.

    This helper is used to assign sentence IDs and speaker labels to new
    tokens.  For each new token index, the function finds which original
    token index (if any) generated it.  If multiple original tokens map to
    the same new token, the earliest original index is chosen.

    Parameters
    ----------
    mapping: Dict[int, Tuple[int, int]]
        Mapping from original token indices to ranges of new token indices.

    new_len: int
        The number of new tokens.

    Returns
    -------
    List[Optional[int]]
        A list of length ``new_len``.  Each element is either an integer
        giving the original token index that generated the new token or
        ``None`` if the new token was an insertion not corresponding to any
        original token.
    """
    reverse: List[Optional[int]] = [None] * new_len
    for orig_idx, (start, end) in mapping.items():
        if start == -1 or end == -1:
            continue
        for new_idx in range(start, end + 1):
            # If multiple original tokens map to the same new token, choose the earliest.
            if reverse[new_idx] is None or orig_idx < reverse[new_idx]:
                reverse[new_idx] = orig_idx
    return reverse


def rebuild_sentences(
    new_tokens: Sequence[str], orig_doc: Dict, reverse_map: List[Optional[int]]
) -> Tuple[List[List[str]], List[int]]:
    """Construct the new sentences and sentence IDs based on the reverse mapping.

    The original document contains a ``sent_id`` list indicating the
    sentence number for each original token.  Using the reverse mapping
    from new tokens to original indices, this function assigns a sentence
    ID to each new token.  New tokens that do not map to any original
    token (insertions) are assigned to the sentence of the nearest
    original token to the left; if no token to the left exists, the
    sentence of the nearest to the right is used.  Once sentence IDs are
    assigned, the function groups tokens into sentence lists.

    Parameters
    ----------
    new_tokens: Sequence[str]
        Tokens of the new tokenisation.

    orig_doc: Dict
        The original document dictionary containing the ``sent_id`` list.

    reverse_map: List[Optional[int]]
        For each new token index, the original token index that generated
        it or ``None`` if the token was inserted.

    Returns
    -------
    Tuple[List[List[str]], List[int]]
        A tuple ``(sentences, sent_ids)`` where ``sentences`` is a list of
        lists of tokens and ``sent_ids`` is the sentence ID for each new
        token.
    """
    orig_sent_ids: List[int] = orig_doc["sent_id"]
    new_sent_ids: List[int] = [0] * len(new_tokens)
    # Assign sentence IDs to new tokens based on reverse mapping
    for i, orig_idx in enumerate(reverse_map):
        if orig_idx is not None:
            new_sent_ids[i] = orig_sent_ids[orig_idx]
        else:
            # This token was inserted.  Look left and right for the closest
            # original token to copy the sentence ID from.
            left = i - 1
            right = i + 1
            assigned = False
            while left >= 0 or right < len(reverse_map):
                if left >= 0 and reverse_map[left] is not None:
                    new_sent_ids[i] = orig_sent_ids[reverse_map[left]]
                    assigned = True
                    break
                if right < len(reverse_map) and reverse_map[right] is not None:
                    new_sent_ids[i] = orig_sent_ids[reverse_map[right]]
                    assigned = True
                    break
                left -= 1
                right += 1
            if not assigned:
                # Fallback to zero if no context is available
                new_sent_ids[i] = 0
    # Group tokens by sentence ID
    sentences: List[List[str]] = []
    current_sent: List[str] = []
    current_id: int = new_sent_ids[0] if new_sent_ids else 0
    for token, sent_id in zip(new_tokens, new_sent_ids):
        if sent_id != current_id and current_sent:
            sentences.append(current_sent)
            current_sent = []
            current_id = sent_id
        current_sent.append(token)
    if current_sent:
        sentences.append(current_sent)
    return sentences, new_sent_ids


def rebuild_speakers(
    orig_doc: Dict, reverse_map: List[Optional[int]]
) -> List[List[str]]:
    """Construct the speakers list for the new tokenisation.

    The original document contains a nested ``speakers`` list with one
    sublist per sentence, and each sublist has one element per token.  The
    order of sentences in ``speakers`` corresponds to the order of
    sentences in ``sentences``.  Given the reverse mapping from new
    tokens to original token indices, this function assigns the speaker
    label from the corresponding original token to each new token.  For
    inserted tokens, the speaker from the nearest original token to the
    left is used (or to the right if none on the left).

    Parameters
    ----------
    orig_doc: Dict
        Original document with ``speakers`` field.

    reverse_map: List[Optional[int]]
        For each new token index, the original token index that generated
        it or ``None`` if the token was inserted.

    Returns
    -------
    List[List[str]]
        A nested list of speakers for the new tokenisation, grouped by
        sentence.
    """
    # Flatten the original speakers list to a single sequence for easier indexing
    flat_speakers: List[str] = []
    for sent_speakers in orig_doc["speakers"]:
        flat_speakers.extend(sent_speakers)
    new_speakers_flat: List[str] = []
    for i, orig_idx in enumerate(reverse_map):
        if orig_idx is not None:
            new_speakers_flat.append(flat_speakers[orig_idx])
        else:
            # Find nearest original token's speaker
            left = i - 1
            right = i + 1
            assigned = False
            while left >= 0 or right < len(reverse_map):
                if left >= 0 and reverse_map[left] is not None:
                    new_speakers_flat.append(flat_speakers[reverse_map[left]])
                    assigned = True
                    break
                if right < len(reverse_map) and reverse_map[right] is not None:
                    new_speakers_flat.append(flat_speakers[reverse_map[right]])
                    assigned = True
                    break
                left -= 1
                right += 1
            if not assigned:
                # Default speaker if no context; use "-" to indicate unknown
                new_speakers_flat.append("-")
    # Group the flat speaker list by sentence boundaries using the new
    # sentence IDs from rebuild_sentences.  To avoid recomputing sentence
    # boundaries, we reconstruct them again here.
    # Derive sentence IDs from reverse_map by repeating the logic in
    # rebuild_sentences but simplified for speaker grouping.
    orig_sent_ids: List[int] = orig_doc["sent_id"]
    new_sent_ids: List[int] = [0] * len(reverse_map)
    for i, orig_idx in enumerate(reverse_map):
        if orig_idx is not None:
            new_sent_ids[i] = orig_sent_ids[orig_idx]
        else:
            # same fallback as above
            left = i - 1
            right = i + 1
            assigned = False
            while left >= 0 or right < len(reverse_map):
                if left >= 0 and reverse_map[left] is not None:
                    new_sent_ids[i] = orig_sent_ids[reverse_map[left]]
                    assigned = True
                    break
                if right < len(reverse_map) and reverse_map[right] is not None:
                    new_sent_ids[i] = orig_sent_ids[reverse_map[right]]
                    assigned = True
                    break
                left -= 1
                right += 1
            if not assigned:
                new_sent_ids[i] = 0
    # Now group speakers by sentence ID
    grouped: List[List[str]] = []
    current_sent: List[str] = []
    current_id: Optional[int] = new_sent_ids[0] if new_sent_ids else None
    for spk, sid in zip(new_speakers_flat, new_sent_ids):
        if current_id is None:
            current_id = sid
        if sid != current_id and current_sent:
            grouped.append(current_sent)
            current_sent = []
            current_id = sid
        current_sent.append(spk)
    if current_sent:
        grouped.append(current_sent)
    return grouped


def process_documents(
    original_docs: List[Dict], tokenized_docs: Dict[str, List[str]], matches: Dict[str, Dict]
) -> List[Dict]:
    """Convert each tokenised document into the new format.

    Parameters
    ----------
    original_docs: List[Dict]
        The original documents parsed from the JSON lines file.

    tokenized_docs: Dict[str, List[str]]
        Mapping from tokenised filenames to lists of tokens.

    matches: Dict[str, Dict]
        Mapping from tokenised filenames to the matched original document
        dictionary as produced by :func:`match_documents`.

    Returns
    -------
    List[Dict]
        A list of new document dictionaries ready to be written to the
        output JSON lines file.
    """
    new_docs: List[Dict] = []
    for fname, new_tokens in tokenized_docs.items():
        orig_doc = matches[fname]
        orig_tokens = orig_doc["cased_words"]
        # Compute alignment mapping for this document
        mapping = compute_alignment(orig_tokens, new_tokens)
        # Update clusters
        new_clusters = update_clusters(orig_doc["clusters"], mapping)
        # Build reverse map from new tokens to original tokens
        reverse_map = map_new_tokens_to_original(mapping, len(new_tokens))
        # Rebuild sentences and sentence IDs
        sentences, new_sent_ids = rebuild_sentences(new_tokens, orig_doc, reverse_map)
        # Rebuild speakers
        new_speakers = rebuild_speakers(orig_doc, reverse_map)
        # Construct new document dictionary
        new_doc = {
            "cased_words": new_tokens,
            "sent_id": new_sent_ids,
            "part_id": orig_doc["part_id"],
            "doc_key": orig_doc["doc_key"],
            "sentences": sentences,
            "speakers": new_speakers,
            "clusters": new_clusters,
        }
        new_docs.append(new_doc)
    return new_docs


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Convert Hebrew coreference test set to SOTA tokenization")
    parser.add_argument(
        "--original",
        required=True,
        help="Path to the original test JSON lines file"
    )
    parser.add_argument(
        "--tokenized",
        required=True,
        help="Path to the directory containing SOTA tokenised documents"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the converted JSON lines file"
    )
    args = parser.parse_args(argv)

    # Read source data
    original_docs = read_original_documents(args.original)
    tokenized_docs = read_tokenized_documents(args.tokenized)
    # Match documents between the two corpora
    matches = match_documents(original_docs, tokenized_docs)
    # Process documents and convert clusters
    new_docs = process_documents(original_docs, tokenized_docs, matches)
    # Write output
    with open(args.output, "w", encoding="utf‑8") as out_f:
        for doc in new_docs:
            out_f.write(json.dumps(doc, ensure_ascii=False))
            out_f.write("\n")


if __name__ == "__main__":
    main()
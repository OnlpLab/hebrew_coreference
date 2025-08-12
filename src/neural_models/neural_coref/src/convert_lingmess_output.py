#!/usr/bin/env python3
"""
Convert lingmess-coref output format to evaluate.py expected format.

Lingmess-coref outputs:
- document_id
- span_clusters (predicted)

Original test data has:
- doc_key
- clusters (gold)

We need to convert to:
- doc_key
- predicted_clusters
- gold_clusters
"""

import json
import sys
import os


def load_jsonlines(file_path):
    """Load JSONLines file and return list of documents."""
    documents = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                doc = json.loads(line)
                documents[doc.get('doc_key', doc.get('document_id', ''))] = doc
    return documents


def convert_lingmess_output(predictions_file, gold_file, output_file):
    """Convert lingmess-coref output to evaluate.py format."""

    # Load predictions (lingmess-coref output)
    predictions = load_jsonlines(predictions_file)

    # Load gold data (original test file)
    gold_data = load_jsonlines(gold_file)

    # Convert format
    converted_docs = []

    for doc_id, pred_doc in predictions.items():
        # Find corresponding gold document
        gold_doc = gold_data.get(doc_id)
        if gold_doc is None:
            print(f"Warning: No gold data found for document {doc_id}")
            continue

        # Convert to evaluate.py format
        converted_doc = {
            "doc_key": doc_id,
            "predicted_clusters": pred_doc.get("clusters", []),
            "gold_clusters": gold_doc.get("clusters", [])
        }
        converted_docs.append(converted_doc)

    # Save converted format
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(converted_docs, f, ensure_ascii=False, indent=2)

    print(f"Converted {len(converted_docs)} documents to {output_file}")
    return converted_docs


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python convert_lingmess_output.py <predictions_file> <gold_file> <output_file>")
        print(
            "Example: python convert_lingmess_output.py test_output.json data/lingmess/hebrew/test.hebrew.jsonlines converted_output.json")
        sys.exit(1)

    predictions_file = sys.argv[1]
    gold_file = sys.argv[2]
    output_file = sys.argv[3]

    convert_lingmess_output(predictions_file, gold_file, output_file)
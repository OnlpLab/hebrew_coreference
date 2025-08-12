import argparse
from collections import defaultdict
import os
import json
import re
import random


def parse_base_docs(filepath):
    """Parse original .conllu files to extract necessary information"""
    sent_num = -1
    with open(filepath, 'r', encoding='utf-8') as file:
        doc_info = {
            "cased_words": [],
            "sent_id": [],
            "pos": [],
            "deprel": [],
            "head": []
        }
        for line in file:
            if line.startswith("#"):
                continue
            parts = line.strip().split("\t")
            if len(parts) == 10 and not "-" in parts[0]:  # To avoid range tokens in enhanced dependencies
                if parts[0] == "1":
                    sent_num += 1
                doc_info["cased_words"].append(parts[1])
                doc_info["sent_id"].append(sent_num)
                doc_info["pos"].append(parts[3])
                doc_info["deprel"].append(parts[7])
                doc_info["head"].append(int(parts[6]) if parts[6] != "0" else None)
        return doc_info


def parse_consolidated_file(filepath, use_local_indices=False, start_token=0):
    """Extract cluster information from consolidated files"""
    with open(filepath, 'r', encoding='utf-8') as file:
        data = file.read().split('\n')

    word_count = start_token
    corefs = defaultdict(list)
    corefs_open = defaultdict(list)
    sent_word_counts = defaultdict(int)

    for line in data:
        if line.startswith("#") or line == '':
            continue

        components = line.split('\t')
        word, sent_id_str, word_id_str = components[:3]
        sent_id = int(sent_id_str)
        annotation = components[4]
        parts = annotation.split('|')

        local_word_count = sent_word_counts[sent_id]

        for part in parts:
            if part.startswith('('):
                coref_id = part.strip("()")
                if use_local_indices:
                    corefs_open[coref_id].append((sent_id, local_word_count))
                else:
                    corefs_open[coref_id].append(word_count)

            if part.endswith(')'):
                coref_id = part.strip("()")
                start = corefs_open[coref_id].pop()
                coref_span = [start, word_count + 1]

                corefs[coref_id].append(coref_span)

        word_count += 1
        sent_word_counts[sent_id] += 1

    clusters = [corefs[key] for key in sorted(corefs.keys(), key=lambda x: int(x))]

    return clusters


def plot_stat(consolidated_files_path, base_files_path):
    files = get_coref_files(consolidated_files_path)
    conllus, conllus_by_hit_id = get_conllus_files(base_files_path)
    overall_mentions_with_singletons = 0
    overall_mentions_without_singletons = 0
    overall_clusters = 0
    for filename in files:
        if filename.endswith(".conllu"):
            doc_number = filename.split('_')[0]
            # Assuming there's a mapping to locate the matching base file
            base_filename = conllus_by_hit_id.get(int(doc_number))
            if base_filename:
                # Parse both files
                base_doc_info = parse_base_docs(os.path.join(base_files_path, base_filename))
                # We count clusters with singleton in order to get the number of mentions
                clusters_with_singleton = parse_consolidated_file(os.path.join(consolidated_files_path, filename))
                num_of_mentions = sum(len(cluster) for cluster in clusters_with_singleton)
                clusters = [c for c in clusters_with_singleton if len(c) > 1]
                num_of_non_singleton_mentions = sum(len(cluster) for cluster in clusters)
                num_of_clusters = len(clusters)
                overall_mentions_with_singletons += num_of_mentions
                overall_mentions_without_singletons += num_of_non_singleton_mentions
                overall_clusters += num_of_clusters
                print(
                    f"Doc {doc_number} has {num_of_mentions} mentions and {num_of_clusters} clusters and {num_of_non_singleton_mentions} non-singleton mentions")
    print(f"Overall mentions: {overall_mentions_with_singletons}")
    print(f"Overall mentions without singletons: {overall_mentions_without_singletons}")
    print(f"Overall clusters: {overall_clusters}")


def get_conllus_files(base_files_path):
    conllus = sorted([i for i in os.listdir(base_files_path)], key=lambda x: int(x.split("_")[0]))
    conllus_by_hit_id = {int(file_name.split("_")[0]) - 1: file_name for file_name in conllus}
    return conllus, conllus_by_hit_id


def get_coref_files(consolidated_files_path):
    files = os.listdir(consolidated_files_path)
    files.sort(key=lambda x: int(x.split("_")[0]))
    return files


def main():
    plot_stat("../final_coref_files/conllu/", "coref_docs_2_tag/base")


if __name__ == '__main__':
    main()

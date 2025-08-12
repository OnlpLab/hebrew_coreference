import argparse
from collections import defaultdict
import os
import json
import re
import random
from typing import List


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


def parse_consolidated_file(filepath, end_token_exclusive, to_keep_singleton, use_local_indices=False, start_token=0):
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
        word_id = int(word_id_str)
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
                if use_local_indices:
                    coref_span = [start[0], start[1], local_word_count + 1 if end_token_exclusive else local_word_count]
                else:
                    coref_span = [start, word_count + 1 if end_token_exclusive else word_count]

                corefs[coref_id].append(coref_span)

        word_count += 1
        sent_word_counts[sent_id] += 1

    if to_keep_singleton:
        clusters = [corefs[key] for key in sorted(corefs.keys(), key=lambda x: int(x))]
    else:
        clusters = [corefs[key] for key in sorted(corefs.keys(), key=lambda x: int(x)) if len(corefs[key]) > 1]

    return clusters


# def parse_consolidated_file(filepath, end_token_exclusive, to_keep_singleton):
#     """Extract cluster information from consolidated files"""
#     with open(filepath, 'r', encoding='utf-8') as file:
#         data = file.read().split('\n')
#
#     word_count = 0
#     corefs = defaultdict(list)
#     corefs_open = defaultdict(list)
#
#     for line in data:
#         if line.startswith("#"):
#             continue
#         if line == '':
#             continue
#         components = line.split('\t')
#         word, sent_id, word_id = components[:3]
#         annotation = components[4]
#         parts = annotation.split('|')
#         for part in parts:
#             if part.startswith('('):
#                 coref_id = part.strip("()")
#                 corefs_open[coref_id].append(word_count)
#             if part.endswith(')'):
#                 coref_id = part.strip("()")
#                 start = corefs_open[coref_id].pop()
#                 if end_token_exclusive:
#                     corefs[coref_id].append([start, word_count + 1])  # The End token is exclusive
#                 else:
#                     corefs[coref_id].append([start, word_count])  # The End token is exclusive
#
#         word_count += 1
#     if to_keep_singleton:
#         clusters = [corefs[key] for key in sorted(corefs.keys(), key=lambda x: int(x))]
#     else:
#         clusters = [corefs[key] for key in sorted(corefs.keys(), key=lambda x: int(x)) if len(corefs[key]) > 1]
#     return clusters
#

def get_sents_offsets(sentences_len):
    sentences_offsets = {}
    cur_count = 0
    for sent_id, length in sentences_len.items():
        sentences_offsets[sent_id] = cur_count
        cur_count += length
    return sentences_offsets


def fix_heads(base_doc_info):
    sentences_len = get_sentences_lengths(base_doc_info)
    sent_offset = get_sents_offsets(sentences_len)

    fixed_heads = []

    for head, sent in zip(base_doc_info["head"], base_doc_info['sent_id']):
        if head is None:
            fixed_heads.append(head)
        else:
            fixed_head = head + sent_offset[sent]
            fixed_heads.append(fixed_head)
    return fixed_heads


def get_sentences_lengths(base_doc_info):
    sents_len = {}
    for i in range(100):
        sent_len = base_doc_info['sent_id'].count(i)
        if sent_len == 0:
            break
        sents_len[i] = sent_len
    return sents_len


def get_sentences_seperated_representation(base_doc_info):
    sentences_dict = {}
    for word, id_ in zip(base_doc_info['cased_words'], base_doc_info['sent_id']):
        if id_ in sentences_dict:
            sentences_dict[id_].append(word)
        else:
            sentences_dict[id_] = [word]

    # Convert the dictionary into a list of lists
    sentences_list = list(sentences_dict.values())
    return sentences_list


def split_data(output, train_ratio=0.7, dev_ratio=0.1, test_ratio=0.2, seed=None):
    # Ensure the ratios sum to 1.0
    assert round(train_ratio + dev_ratio + test_ratio, 10) == 1.0, "Ratios must sum to 1.0"

    if seed is not None:
        random.seed(seed)
    # Shuffle the data
    random.shuffle(output)

    total_tokens = sum(len(json.loads(doc)["cased_words"]) for doc in output)

    # Calculate the number of tokens for each split
    train_tokens_threshold = total_tokens * train_ratio
    dev_tokens_threshold = total_tokens * dev_ratio

    train_data, dev_data, test_data = [], [], []
    train_tokens, dev_tokens, test_tokens = 0, 0, 0

    for doc in output:
        doc_data = json.loads(doc)
        num_tokens = len(doc_data["cased_words"])

        if train_tokens + num_tokens <= train_tokens_threshold:
            train_data.append(doc)
            train_tokens += num_tokens
        elif dev_tokens + num_tokens <= dev_tokens_threshold:
            dev_data.append(doc)
            dev_tokens += num_tokens
        else:
            test_data.append(doc)
            test_tokens += num_tokens

    return train_data, dev_data, test_data


def save_data(data, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as outfile:
        for line in data:
            outfile.write(line + "\n")


def consolidate_docs(consolidated_files_path, base_files_path, to_keep_singleton,
                     end_token_exclusive,
                     to_sep_sentences,
                     print_debug):
    output = []
    files = get_coref_files(consolidated_files_path)
    conllus, conllus_by_hit_id = get_conllus_files(base_files_path)

    for filename in files:
        if filename.endswith(".conllu"):
            doc_number = filename.split('_')[0]
            # Assuming there's a mapping to locate the matching base file
            base_filename = conllus_by_hit_id.get(int(doc_number))
            if base_filename:
                # Parse both files
                base_doc_info = parse_base_docs(os.path.join(base_files_path, base_filename))
                clusters = parse_consolidated_file(os.path.join(consolidated_files_path, filename),
                                                   end_token_exclusive,
                                                   to_keep_singleton)
                base_doc_info["part_id"] = 0  # Assuming constant part_id as not specified
                if to_sep_sentences:
                    base_doc_info["doc_key"] = "nw/" + re.search(r'\d+', filename).group()

                    base_doc_info['sentences'] = get_sentences_seperated_representation(base_doc_info)
                    base_doc_info["speakers"] = [['-' for _ in sublist] for sublist in base_doc_info['sentences']]

                else:
                    base_doc_info["document_id"] = "nw/" + re.search(r'\d+', filename).group()

                    base_doc_info["speaker"] = ["-"] * len(base_doc_info["cased_words"])
                base_doc_info["clusters"] = clusters
                base_doc_info["head"] = fix_heads(base_doc_info)
                output.append(json.dumps(base_doc_info, ensure_ascii=False))
    if print_debug:
        for doc in output:
            print(doc)
    return output


def get_conllus_files(base_files_path):
    conllus = sorted([i for i in os.listdir(base_files_path)], key=lambda x: int(x.split("_")[0]))
    conllus_by_hit_id = {int(file_name.split("_")[0]) - 1: file_name for file_name in conllus}
    return conllus, conllus_by_hit_id


def convert_to_indiscrim_format(base_files_path, consolidated_files_path):
    output = []
    files = get_coref_files(consolidated_files_path)
    conllus, conllus_by_hit_id = get_conllus_files(base_files_path)

    for filename in files:
        if not filename.endswith(".conllu"):
            continue
        doc_number = filename.split('_')[0]
        base_filename = conllus_by_hit_id.get(int(doc_number))
        if not base_filename:
            continue
        base_doc_info = parse_base_docs(os.path.join(base_files_path, base_filename))
        clusters = parse_consolidated_file(os.path.join(consolidated_files_path, filename),
                                           end_token_exclusive=False, to_keep_singleton=False,
                                           use_local_indices=True, start_token=1)

        sentences = []
        sentence_id = -1
        sentence_text = []
        sentence_toks = []
        tok_idx = 1

        for word, pos, deprel, head, sent_id in zip(
                base_doc_info["cased_words"],
                base_doc_info["pos"],
                base_doc_info["deprel"],
                base_doc_info["head"],
                base_doc_info["sent_id"]):
            sent_id += 1  # We start sentence from 1 and not from 0
            if sent_id != sentence_id:
                if sentence_id != -1:
                    sentence = {
                        "id": sentence_id,
                        "text": " ".join(sentence_text),
                        "speaker": None,
                        "tokens": sentence_toks
                    }
                    sentences.append(sentence)
                sentence_text = [word]
                tok_idx = 1
                sentence_toks = [{
                    "id": tok_idx,
                    "text": word,
                    "upos": pos,
                    "head": head,
                    "deprel": deprel,
                }]
                sentence_id = sent_id

            else:
                sentence_text.append(word)
                sentence_toks.append({
                    "id": tok_idx,
                    "text": word,
                    "upos": pos,
                    "head": head,
                    "deprel": deprel,
                })
            tok_idx += 1
        if sentence_text:
            sentence = {
                "id": sentence_id,
                "text": " ".join(sentence_text),
                "speaker": None,
                "tokens": sentence_toks
            }
            sentences.append(sentence)

        doc = {
            "id": "nw/" + re.search(r'\d+', filename).group(),
            "text": " ".join(base_doc_info["cased_words"]),
            "sentences": sentences,
            "coref_chains": clusters,
            "genre": "nw",
            "meta_data": {"comment": ""}
        }
        output.append(json.dumps(doc, ensure_ascii=False))
    return output


def get_coref_files(consolidated_files_path):
    files = os.listdir(consolidated_files_path)
    files.sort(key=lambda x: int(x.split("_")[0]))
    return files


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument("-con", "--consolidated_folder_path", type=str, default="../final_coref_files/conllu/",
                           help="The directory of the consolidated coreference files")
    argparser.add_argument("-base", "--base_folder_path", type=str, default="coref_docs_2_tag/base",
                           help="The name of the directory of the base conllu files with the POS tags and"
                                " dependency relation")
    argparser.add_argument("-o", "--output_path", type=str, default="coreference_docs.jsonl",
                           help="The output path for the jsonl file")
    argparser.add_argument("-s", "--keep_singletons", action='store_true',
                           help="If True the script would remove any cluster with only one mention")
    argparser.add_argument("-sent", "--separate_to_sentences", action='store_true',
                           help="add a key of word seperated by their sentences List[List[str]]")
    argparser.add_argument("-ete", "--end_token_exclusive", action='store_true',
                           help="Does in the clusters created the End token is exclusive")
    argparser.add_argument("-i", "--indiscrim", action='store_true',
                           help="This argument can't come with the arguments:\n "
                                "{keep_singletons,separate_to_sentences, end_token_exclusive }\n "
                                "Output the document in indiscrim format \n"
                                "See: https://github.com/ianporada/coref-data/  ")
    argparser.add_argument("-p", "--print_debug", action='store_true',
                           help="The output path for the jsonl file")  # it is just printing - might need to remove

    args = argparser.parse_args()

    consolidated_folder_path = args.consolidated_folder_path
    base_folder_path = args.base_folder_path
    output_path = args.output_path
    to_keep_singleton = args.keep_singletons
    to_sep_sentences = args.separate_to_sentences
    print_debug = args.print_debug
    end_token_exclusive = args.end_token_exclusive
    indiscrim_format = args.indiscrim
    if indiscrim_format and any([end_token_exclusive, to_sep_sentences, to_keep_singleton]):
        raise ValueError("The argument '--indiscrim' can't come with the arguments:\n "
                         "{keep_singletons,separate_to_sentences, end_token_exclusive }\n"
                         "You may run the program without the mentioned args")
    if indiscrim_format:
        formatted_docs = convert_to_indiscrim_format(base_folder_path, consolidated_folder_path)
    else:
        formatted_docs = consolidate_docs(consolidated_folder_path, base_folder_path,
                                          to_keep_singleton,
                                          end_token_exclusive,
                                          to_sep_sentences,
                                          print_debug)
    train_data, dev_data, test_data = split_data(formatted_docs, train_ratio=0.7, dev_ratio=0.15, test_ratio=0.15,
                                                 seed=42)

    # Output JSON lines (`.jsonl`) file

    save_data(train_data, os.path.join(output_path, 'train.hebrew.jsonlines'))
    save_data(dev_data, os.path.join(output_path, 'dev.hebrew.jsonlines'))
    save_data(test_data, os.path.join(output_path, 'test.hebrew.jsonlines'))


if __name__ == '__main__':
    """
    need run with
    For wl-coref:
    -con ../final_coref_files/conllu/ -base coref_docs_2_tag/base -o wl_coref_docs -ete
    For s2e-coref/linghmes:
    -con ../final_coref_files/conllu/ -base coref_docs_2_tag/base -sent -o coreference_docs_sent_sep_no_singleton 
    For indiscrim format:
    -o jsonl_output/indiscrim.jsonl -i
    """

    main()

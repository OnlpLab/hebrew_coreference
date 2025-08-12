import argparse
import json
import os

from conll_reader import ConllReader
from add_token_loc_utils import extract_nps_token_locations_to_consolidate_data


def read_consolidation_files(path):
    consolidation_by_hit_id = {}
    files = os.listdir(path)
    for file in files:
        file_full_path = os.path.join(path, file)
        with open(file_full_path) as f:
            hit_id = file.split(".")[0]
            consolidation_by_hit_id[hit_id] = json.load(f)
    return consolidation_by_hit_id


def parse_args():
    """
    -c coref_docs_2_tag/base
    -t ../../hebrew_coref/coref_annotation_data/Consolidation
    -m coref_docs_2_tag/tne_conll_final_mentions
    -o coref_docs_2_tag/conllu_out_annotation
    """

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-c", "--conllu_folder", type=str, help="path to conllu folder")
    arg_parser.add_argument("-t", "--tne_consolidate_folder", type=str, help="path to tne folder")
    arg_parser.add_argument("-m", "--final_mention_w_token_folder", type=str, help="path to tne folder")
    arg_parser.add_argument("-o", "--out_path", type=str, help="path to tne folder")
    arg_parser.add_argument("-nc", "--dont_use_cache", action='store_true', help="if used, the program would force "
                                                                                 "remaking all the  file i folder "
                                                                                 "even if they are already exists")
    args = arg_parser.parse_args()
    return args


def list_conllu_files(conllu_path):
    conll = ConllReader()
    files = os.listdir(conllu_path)
    conllu_by_hit_id = {}
    for file in files:
        file_full_path = os.path.join(conllu_path, file)
        hit_id = int(file.split("_")[0]) - 1
        conllu_by_hit_id[hit_id] = list(conll.read_conll(file_full_path, input_encoding="utf-8", merge_subtoken=False))
    return conllu_by_hit_id


def read_final_mention(final_mention_path):
    final_mention_by_hit_id = {}
    files = os.listdir(final_mention_path)
    for file in files:
        file_full_path = os.path.join(final_mention_path, file)
        with open(file_full_path) as f:
            hit_id = int(file.split("_")[0]) - 1
            tne_doc = json.load(f)[0]
            nps_w_token = tne_doc['nps']
            final_mention_by_hit_id[hit_id] = nps_w_token
    return final_mention_by_hit_id


def main():
    args = parse_args()
    consolidation_by_hit_id = read_consolidation_files(args.tne_consolidate_folder)

    conllu_files_by_hit_id = list_conllu_files(args.conllu_folder)
    final_mention_by_hit_id = read_final_mention(args.final_mention_w_token_folder)

    i=1

    for hit_id, consolidate_file_loc in consolidation_by_hit_id.items():
        if 'nps' not in consolidate_file_loc:
            # This script support only the new documents with annotated mentions
            # The old version is also deprecated and also already has support because the document nps are known
            continue
        i += 1
        hit_id = int(hit_id)
        cur_conllu = conllu_files_by_hit_id.get(hit_id)
        cur_final_mention = final_mention_by_hit_id.get(hit_id)
        nps_res = extract_nps_token_locations_to_consolidate_data(cur_final_mention, consolidate_file_loc, cur_conllu)
        consolidate_file_loc['nps'] = nps_res

        with open(os.path.join(args.out_path, f"{hit_id}.json"), mode='w', encoding='utf-8') as f:
            json.dump(consolidate_file_loc, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    main()

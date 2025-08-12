import argparse
import ast
import json
import sqlite3 as lite
import os
import shutil
from conll_reader import ConllReader
from add_token_loc_utils import extract_nps_token_locations


def parse_args():
    """
    -db_dir ../../data
    -db hebrew_v4.dat
    -c coref_docs_2_tag/base
    -t coref_docs_2_tag/tne_conll
    -o coref_docs_2_tag/tne_conll_final_mentions
    -nc
    """

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-db_dir", "--database_dir", type=str,
                            help="name of the directory that contains the databse")
    arg_parser.add_argument("-db", "--data_base", type=str,
                            help="name of the database to which the consolidation data will be stored")
    arg_parser.add_argument("-c", "--conllu_folder", type=str, help="path to conllu folder")
    arg_parser.add_argument("-t", "--tne_folder", type=str, help="path to tne folder")
    arg_parser.add_argument("-o", "--out_path", type=str, help="path to tne folder")
    arg_parser.add_argument("-nc", "--dont_use_cache", action='store_true', help="if used, the program would force "
                                                                                 "remaking all the  file i folder "
                                                                                 "even if they are already exists")
    args = arg_parser.parse_args()
    return args


def main():
    args = parse_args()
    db = os.path.join(args.database_dir, args.data_base)
    conllus = sorted([i for i in os.listdir(args.conllu_folder)], key=lambda x: int(x.split("_")[0]))
    conllus_by_hit_id = {int(file_name.split("_")[0]) - 1: file_name for file_name in conllus}
    tnes = sorted(os.listdir(args.tne_folder), key=lambda x: int(x.split("_")[0]))
    tne_by_hid_id = {int(file_name.split("_")[0]) - 1: file_name for file_name in tnes}
    with lite.connect(db) as con:
        cur = con.cursor()
        final_mentions_nps = get_final_mention_nps(cur)

    if not args.dont_use_cache:
        remove_cached_files_path(args, tne_by_hid_id)
    conll = ConllReader()
    for hit_id, tne_original_conllu_file in tne_by_hid_id.items():
        if hit_id not in final_mentions_nps:
            continue
        tne_doc = get_original_tne_doc(args, tne_original_conllu_file)
        res_nps_for_hit_id = get_final_mentions_for_hit_id(args, conll, conllus_by_hit_id,
                                                           final_mentions_nps.get(hit_id),
                                                           hit_id, tne_doc)
        tne_doc[0]['nps'] = res_nps_for_hit_id
        with open(os.path.join(args.out_path, tne_original_conllu_file), mode='w', encoding='utf-8') as f:
            json.dump(tne_doc, f, indent=4, ensure_ascii=False)
        print(hit_id)
        # print(res_nps_for_hit_id)

    '''
    conll = ConllReader()
    path = "/Users/s0g0a87/studies/tne_ui/hebrew_coref/create_agreement_files/coref_docs_2_tag/base/95_13_sents_htb_88.conllu"
    full_doc = list(conll.read_conll(path, input_encoding="utf-8", merge_subtoken=False))
    
    
    db_path = "/Users/s0g0a87/studies/tne_ui/data/hebrew_v3.dat"
    file_path = "/Users/s0g0a87/studies/tne_ui/hebrew_coref/create_agreement_files/coref_docs_2_tag/tne_conll/95_13_sents_htb_88.tne"
    hit_id = 94
    '''

    # TODO itertate through all the docs in debug - find an example for a mention we cant find
    # Try to resolve it using seraching a close mentions - maybe one in each other?
    # If manage to resolve all nps - create new documents under "tne_conll_final_mentions" -  can add there the documents before 59


def get_original_tne_doc(args, tne_original_conllu_file):
    tne_full_path = os.path.join(args.tne_folder, tne_original_conllu_file)
    with open(tne_full_path) as f:
        tne_doc = json.load(f)
    return tne_doc


def get_db_data(cur):
    original_data_query = "SELECT hit_id, text, nps FROM tne_original_data"
    original_data = cur.execute(original_data_query).fetchall()
    db_data = {t[0]: {"text": t[1], "original_nps": t[2]} for t in original_data}
    return db_data


def get_final_mention_nps(cur):
    nps_query = "SELECT hit_id, nps FROM final_mention_data"
    final_mentions_nps = cur.execute(nps_query).fetchall()
    final_mentions_nps = {t[0]: ast.literal_eval(t[1]) for t in final_mentions_nps}
    return final_mentions_nps


def get_final_mentions_for_hit_id(args, conll, conllus_by_hit_id, hit_id_final_mentions, hit_id, tne_doc):
    conllu_path = os.path.join(args.conllu_folder, conllus_by_hit_id.get(hit_id))
    spacy_docs = list(conll.read_conll(conllu_path, input_encoding="utf-8", merge_subtoken=False))
    original_np_by_idx = {(np['start_index'], np['end_index']): np for np in tne_doc[0]['nps']}
    res_nps_for_hit_id = extract_nps_token_locations(hit_id_final_mentions, original_np_by_idx, spacy_docs)
    return res_nps_for_hit_id


def remove_cached_files_path(args, tne_by_hid_id):
    cached_files = os.listdir(args.out_path)
    reversed_tne_by_id = {v: k for k, v in tne_by_hid_id.items()}
    for cache_file in cached_files:
        if cache_file in reversed_tne_by_id:
            tne_by_hid_id.pop(reversed_tne_by_id[cache_file])


def copy_original_conllu(args, tne_original_conllu_file):
    original_tne_file_full_path = os.path.join(args.tne_folder, tne_original_conllu_file)
    shutil.copy(original_tne_file_full_path, args.out_path)


if __name__ == '__main__':
    main()

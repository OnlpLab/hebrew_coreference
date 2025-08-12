import argparse
import ast
import dataclasses
import json
import sqlite3 as lite
import os
from collections import defaultdict

from conll_reader import ConllReader

conll = ConllReader()


@dataclasses.dataclass
class Mention:
    sent_num: int
    start: int
    end: int
    text: str


def verify_mention_in_only_one_cluster(cluster_with_mentions_boundary):
    seen = set([])
    for cluster in cluster_with_mentions_boundary:
        for member in cluster['members']:
            if member in seen:
                raise ValueError(f"The mention id {member} is in at least to clusters")
            seen.add(member)


def add_mentions_boundary(raw_annotation, nps):
    cluster_with_mentions_boundary = []
    for anno in raw_annotation:
        if anno['source'] == 'idiomatic':
            continue
        cluster = {k: v for k, v in anno.items() if k not in {'source', 'selected_preposition'}}
        mention_loc = []
        for member in cluster['members']:
            try:
                np = nps[int(member)]
            except Exception as e:
                print(hit_id)
                raise Exception(e)
            try:
                mention_loc.append(Mention(np['sent_num'], np['start_token'], np['end_token'] - 1, np['text']))
            except TypeError as e:
                print(np)
        cluster['boundary'] = mention_loc
        cluster_with_mentions_boundary.append(cluster)
    verify_mention_in_only_one_cluster(cluster_with_mentions_boundary)
    return cluster_with_mentions_boundary


def format_loc(sent_num, token_num):
    return f"{sent_num}:{token_num}"


def to_coref_format(param, cluster_id):
    if param == "start":
        return f"({cluster_id}"
    elif param == "end":
        return f"{cluster_id})"
    else:
        raise ValueError(f"param can be only {{start, end}} but is {param}")


def create_conll_doc(db_path, original_conllu, tne_format, out_path, hit_id):
    f_out_basename = tne_format.split('/')[-1].split('.')[0]
    with lite.connect(db_path) as con:
        cur = con.cursor()
        annotations = cur.execute(
            f"SELECT clusters, annotator_id FROM tne_coref_data WHERE hit_id={str(hit_id)}").fetchall()

    conllu_files = list(conll.read_conll(original_conllu, input_encoding="utf-8", merge_subtoken=False))
    nps = get_nps(tne_format)
    for annotation, annotator in annotations:
        print(annotator)
        raw_annotation = ast.literal_eval(annotation)
        clusters = add_mentions_boundary(raw_annotation, nps)
        clusters_dict = defaultdict(list)
        text = ""
        text += f"#begin document {str(hit_id)}\n"
        for cluster in clusters:
            cluster_id = cluster['id']
            for mention in cluster['boundary']:
                entry_start = format_loc(mention.sent_num, mention.start)

                if mention.start != mention.end:
                    clusters_dict[entry_start].append(to_coref_format('start', cluster_id))

                    entry_end = format_loc(mention.sent_num, mention.end)
                    clusters_dict[entry_end].append(to_coref_format('end', cluster_id))
                else:

                    clusters_dict[entry_start].append(f"({cluster_id})")

        for sent_num, sent in enumerate(conllu_files):
            # f.write(sent.sents[0]._.conll_meta_data)

            for token in sent:
                entry = format_loc(sent_num, token.i)

                if entry in clusters_dict:
                    token_prediction = "|".join(clusters_dict[entry])
                else:
                    token_prediction = "_"
                line = [token.text, str(sent_num), str(token.i), "_", token_prediction]
                out_line = "\t".join(line) + "\n"
                text += out_line
            text += "\n"
        text = text.strip()
        text += "\n#end document"

        f_outname_annotator = f"{f_out_basename}_{annotator}.conllu"
        with open(os.path.join(out_path, f_outname_annotator), mode='w') as f:
            f.write(text)


def get_nps(tne_format):
    with open(tne_format, encoding='utf-8') as f:
        nps_file = json.load(f)
    nps = nps_file[0]['nps']

    return nps


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--debug", action='store_true')
    arg_parser.add_argument("-db_dir", "--database_dir", type=str,
                            help="name of the directory that contains the databse")
    arg_parser.add_argument("-db", "--data_base", type=str,
                            help="name of the database to which the consolidation data will be stored")
    arg_parser.add_argument("-c", "--conllu_folder", type=str, help="path to conllu folder")
    arg_parser.add_argument("-t", "--tne_folder", type=str, help="path to tne folder")
    arg_parser.add_argument("-o", "--out_path", type=str, help="path to tne folder")
    args = arg_parser.parse_args()
    db = os.path.join(args.database_dir, args.data_base)
    # Used conllus_list only for debug could be only a set
    conllus_list = sorted([i.split(".")[0] for i in os.listdir(args.conllu_folder)], key=lambda x: int(x.split("_")[0]))
    conllus = set(conllus_list)
    tnes = sorted(os.listdir(args.tne_folder), key=lambda x: int(x.split("_")[0]))
    for tne in tnes:
        base_name = tne.split(".")[0]
        hit_id = int(tne.split("_")[0]) - 1
        if base_name not in conllus:
            print("Not good")
            continue
        tne_path = os.path.join(args.tne_folder, tne)
        conllu_path = os.path.join(args.conllu_folder, base_name + ".conllu")
        create_conll_doc(db_path=db,
                         original_conllu=conllu_path,
                         tne_format=tne_path,
                         out_path=args.out_path,
                         hit_id=hit_id)

# -db_dir
# ../../data
# -db
# hebrew_v4.dat
# -c
# coref_docs_2_tag/base
# -t
# coref_docs_2_tag/tne_conll_final_mentions
# -o
# coref_docs_2_tag/conllu_out_annotation

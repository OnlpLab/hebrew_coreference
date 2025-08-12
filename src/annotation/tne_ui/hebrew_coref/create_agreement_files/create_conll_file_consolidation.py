import argparse
import dataclasses
import json
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
        if 'idiomatic' in anno['source']:
            continue
        cluster = {k: v for k, v in anno.items() if k not in {'source', 'selected_preposition'}}
        mention_loc = []
        for member in cluster['members']:
            try:
                np = nps.get(int(member))
            except Exception as e:
                print(hit_id)
                raise Exception(e)
            try:
                mention_loc.append(Mention(np['sent_num'], np['start_token'], np['end_token'] - 1, np['text']))
            except TypeError as e:
                print(f"Error in {hit_id}")
                print(e)
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


def transform_filename(filename: str) -> str:
    original_filename = filename.split('/')[-1]
    relevant_name = original_filename.split('_sents_')[1]
    new_filename = relevant_name.replace("htb_", "htb:")
    return new_filename


def create_conll_doc(original_conllu, tne_format, out_path, hit_id, remove_singleton):
    f_out_basename = transform_filename(original_conllu)
    # f_out_basename = tne_format.split('/')[-1].split('.')[0]
    with open(tne_path) as f:
        annotation = json.load(f)

    conllu_files = list(conll.read_conll(original_conllu, input_encoding="utf-8", merge_subtoken=False))
    nps = annotation['nps']

    raw_annotation = annotation['clusters']
    if remove_singleton:
        raw_annotation = [cluster for cluster in raw_annotation if len(cluster['members']) > 1]
        raw_annotation.sort(key=lambda x: min(x['members']))
        for i, cluster in enumerate(raw_annotation):
            cluster['id'] = i
    id_to_np = {np['id']: np for np in nps}
    clusters = add_mentions_boundary(raw_annotation, id_to_np)
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
    f_outname_annotator = f"{f_out_basename}_Consolidation.conllu"
    with open(os.path.join(out_path, f_out_basename), mode='w') as f:
        f.write(text)


def get_nps(tne_format):
    with open(tne_format, encoding='utf-8') as f:
        nps_file = json.load(f)
    nps = nps_file[0]['nps']

    return nps


def transform(s):
    """
    This function assumes that the last part of the input string after _ is the primary component.
    And the strings will have .conllu extension
    """
    # Splitting the string by '/'
    parts = s.split('/')
    filename = parts[-1]

    filename = filename.replace('_sents_', ':').replace('.conllu', '').split('_htb_')
    filename = filename[::-1]
    filename = ":".join(filename)
    filename = filename + ".conllu"

    return filename


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--debug", action='store_true')
    arg_parser.add_argument("-c", "--conllu_folder", type=str, help="path to conllu folder")
    arg_parser.add_argument("-t", "--tne_folder", type=str, help="path to tne folder")
    arg_parser.add_argument("-o", "--out_path", type=str, help="path to tne folder")
    arg_parser.add_argument("-rs", "--remove_singleton", action='store_true',
                            help="Remove singleton clusters")
    args = arg_parser.parse_args()
    conllus = set([i.split(".")[0] for i in os.listdir(args.conllu_folder)])
    conllus_ids_to_name = {i.split("_")[0]: i for i in os.listdir(args.conllu_folder)}
    tnes = sorted(os.listdir(args.tne_folder), key=lambda x: int(x.split(".")[0]))
    for tne in tnes:
        hit_id = tne.split(".")[0]
        conllu_id = str(int(hit_id) + 1)
        if conllu_id not in conllus_ids_to_name:
            print("Not good")
            continue
        tne_path = os.path.join(args.tne_folder, tne)
        conllu_path = os.path.join(args.conllu_folder, conllus_ids_to_name[conllu_id])
        create_conll_doc(original_conllu=conllu_path,
                         tne_format=tne_path,
                         out_path=args.out_path,
                         hit_id=int(hit_id),
                         remove_singleton=args.remove_singleton)

# -db_dir sqlite_data -db hebrew_v4.dat -c corpus/coref_docs_2_tag/base -t corpus/coref_docs_2_tag/tne_conll -o corpus/coref_docs_2_tag/conllu_out_annotation

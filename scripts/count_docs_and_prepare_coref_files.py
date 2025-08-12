import argparse
from collections import defaultdict
from dataclasses import dataclass
import os
from pathlib import Path
from typing import List

from conllu import TokenList
from convert_tb2_to_ud import read_conllu, serialize_tl


@dataclass
class OutputFiles:
    name: str
    sentences: List[TokenList]


def sort_docs_by_order(input_directory):
    docs = defaultdict(list)
    for filename in os.listdir(input_directory):
        f = os.path.join(input_directory, filename)
        if not os.path.isfile(f) or Path(f).suffix != ".conllu":
            continue
        ud_data = read_conllu(f)
        for sent in ud_data:
            docs[sent.metadata["doc_id"]].append(sent)

    sorted_docs = sorted(docs.items(), key=lambda c: len(c[1]))
    sorted_docs_and_sents = [(sd[0], sorted(sd[1], key=lambda sent: sent.metadata["sent_id"] )) for sd in sorted_docs]
    return sorted_docs_and_sents


def dump_conllu_docs(output_directory, sorted_files):

    if not (os.path.exists(output_directory) and os.path.isdir(output_directory) ):
        os.mkdir(output_directory)
    for i, (n, f) in enumerate(sorted_files):
        out_ud = os.path.join(output_directory, str(i+1) + "_" + str(len(f)) + "_sents_" + n.replace(":", "_") + ".conllu")
        with open(out_ud, 'w') as fout:
            for tl in f:
                fout.write(serialize_tl(tl))


def parse_arguments():
    p = argparse.ArgumentParser(description='Read and output UD Doc files ')
    p.add_argument('input', help="input folder with all 3 files")
    p.add_argument('output', help="output folder for documents")
    return p.parse_args()


def main():
    args = parse_arguments()
    ud_data = sort_docs_by_order(args.input)
    dump_conllu_docs(args.output, ud_data)

if __name__ == '__main__':
    """
    Run with:
    ../corpus/new_htb_zeldes/htb2_format_with_underscore ../corpus/coref_docs_2_tag/base
    """
    main()

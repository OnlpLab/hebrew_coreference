# codisg=utf8
import argparse
from pathlib import Path

import requests
import re

import spacy_udpipe

from config import basic_features, basic_pos, entire_line_pos_conversion
from create_np_file_from_ud_scheme import read_conllx, get_noun_chunks
from np_chunker import Chunker, ConllReader
from legacy_pipeline.spmrl2ud import ConvertSPMRL2UD
import csv

from stanza_parser import StanzaParser

localhost_yap = "http://localhost:8000/yap/heb/joint"

def parse_text(text, to_print=False):
    sents_temp = re.split("([\.?!][\n ])", re.sub("\[\d+]", "", text).replace(u'\u200f', ''))
    sents = []
    for text, sep in zip(sents_temp[::2],sents_temp[1::2]):  # No need to end at -1 because that's the default
        final_text = text + " " + sep
        final_text = final_text.strip("\n ")
        pat = re.compile(r"([()\-,?;!])")
        final_text = pat.sub(" \\1 ", final_text).replace("  ", " ")
        if final_text != "":
            sents.append(final_text)
    if to_print:
        for s in sents:
            print(s)
    return sents

def get_raw_text(source):

    base_path = Path(__file__).parent.joinpath("raw_data")
    if source == "txt":
        with open(base_path.joinpath("ud_dev_only_sent_sample.txt"), encoding='utf-8') as f:
            sents = parse_text("\n".join(f.readlines()))
    elif source == "wiki":
        with open(base_path.joinpath("wikinews_raw"), encoding='utf-8') as f:
            sents = f.readlines()
            sents = parse_text("\n".join(sents))
    elif source == "story":
        with open(base_path.joinpath("story.txt"), encoding='utf-8') as f:
            sents = f.readlines()
            sents = parse_text("\n".join(sents))
    elif source=="simple":
        sents = [
            "הקהל איתר סוף סוף ערבי ויהודים חבטו בו עד זוב דם.",
        ]
    else:
        raise ValueError('Support source only of {"wiki", "txt", "simple", "story"}')

    return sents

def ud_np_chunks(ud_path, out_path):
    dummy_vocab = spacy_udpipe.load("he").vocab
    with open(ud_path, encoding='utf-8') as f:
        l = "".join(f.readlines())
        doc = read_conllx(l, dummy_vocab, merge_subtoken=False)
    with open(out_path, "w", encoding='utf-8') as f:
        for e in doc:
            for w, t in zip(e, get_noun_chunks(e, nested=False)):
                f.write(f"{w}\t{t}\n")
            f.write("\n")


def dump_ud(converter, ud_path):
    columns = ['ID', 'FORM', 'LEMMA', 'UPOS', 'XPOS', 'FEATS', 'HEAD', 'DEPREL', 'DEPS', 'MISC']
    out_csv = converter.segmented_sentence.to_csv(sep='\t', columns=columns, quoting=csv.QUOTE_NONE, index=False,
                                                  header=False)
    out_csv_with_sep = re.compile(r"(\n#.*\n#.*\n)").sub("\n\\1", out_csv)
    with open(ud_path, mode="w", newline="\n") as f:
        f.write(out_csv_with_sep)



def raw2yap2spmrl(sents, spmrl_path):
    output_str = ""
    for i, text in enumerate(sents):

        text = text.replace("\"", "〝")
        data = f'{{"text": "{text}  "}}'.encode("utf-8")  # input string ends with two space characters
        headers = {'content-type': 'application/json'}
        response = requests.get(url=localhost_yap, data=data, headers=headers)
        json_response = response.json()
        output_str += f'# sent_id = {i + 1}\n'
        output_str += f'# text = {text}\n'
        if i != 0:
            output_str += "\n"
        output_str += json_response['dep_tree'].replace("\r", "").replace("〝", "\"")
        output_str += "\n"
    with open(spmrl_path, mode='w') as f:
        f.write(output_str)


def yap_spmrl_ud_npchunck_pipeline():
    p = argparse.ArgumentParser(description='How to run')
    p.add_argument('source', help="source: wiki, txt, simple")
    args = p.parse_args()
    sents = get_raw_text(args.source)
    base_out_path = Path(__file__).parent.joinpath('full_outputs')
    spmrl_path = base_out_path.joinpath("data_spmrl.conll")
    raw2yap2spmrl(sents, spmrl_path)
    converter = ConvertSPMRL2UD(filepath=spmrl_path)
    converter.apply_conversions(feats=basic_features, simple_pos=basic_pos, complex_pos_conversions=entire_line_pos_conversion)
    ud_path = base_out_path.joinpath('ud_from_spmrl.conllu')
    dump_ud(converter, ud_path)
    ud_np_chunks(ud_path, base_out_path.joinpath( "full_pipe_line_txt.txt"))

def stanza_ud_npchunck_pipeline():
    p = argparse.ArgumentParser(description='How to run')
    p.add_argument('source', help="source: wiki, txt, simple")
    args = p.parse_args()
    sents = get_raw_text(args.source)
    base_out_path = Path(__file__).parent.joinpath('full_outputs', "19-2")
    ud_path = base_out_path.joinpath(f'{args.source}_ud_from_stanza.conllu')
    stanza_parser = StanzaParser()
    stanza_parser.parse_and_dump_sents(sents, ud_path)
    conll = ConllReader()
    docs = conll.read_conll(ud_path, input_encoding="utf-8", merge_subtoken=False)
    chunker = Chunker(take_longest=True, allow_nested=True, allow_loc_time_adv=True, possessive=True)
    final_out = base_out_path.joinpath(f"{args.source}_full_pipe_line_stanza.txt")
    # ud_np_chunks(ud_path, base_out_path.joinpath(f"{args.source}_full_pipe_line_stanza.txt"))
    type_output = "BIOSE"
    with open(final_out, mode="w", encoding="utf-8") as f:
        for doc in docs:
            for w, t in zip(doc, chunker.get_noun_chunks(doc, type_output)):
                # For the case of joined sub token strings are different than the original string
                # e.g. בבית -> ב ה בית 0 -> בהבית
                # instead of בבית
                if w._.original_text != "":
                    f.write(f"{w._.original_text} {t}\n")
                else:
                    f.write(f"{w} {t}\n")
            f.write("\n")


if __name__ == '__main__':
    stanza_ud_npchunck_pipeline()
    dataset = "test"
    # ud_np_chunks(rf"C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\corpus\he_htb-ud-{dataset}.conllu.txt",
    #              rf"C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\heb_ud_as_np\he_htb-ud-{dataset}.conllu_np.txt")




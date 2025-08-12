import argparse
import json
import re
from pathlib import Path

import pandas as pd

from ..np_chunker.chunker import Chunker
from ..np_chunker.conll_reader import ConllReader
from .parser import StanzaParser


def parse_arguments():
    p = argparse.ArgumentParser(description='Np chunker flow')
    p.add_argument('input', help="input file expect UD conll file or txt file")
    p.add_argument('output', help="output file chunked to NP")
    p.add_argument('type', help="Choose between {BIO, BIOSE, webbano} when choosing webbano, the file would dump"
                                "as  an output file in a Webanno tsv 3.2 **not 3.3!**  format see"
                                " https://inception-project.github.io/releases/22.2/docs/user-guide.html#sect_formats_webannotsv3 ")
    p.add_argument('output_format', help="format can be conll2003 format or a json format")
    p.add_argument('-ic', '--is_conll', dest='is_conll', action='store_true',
                   help="if passed the input file is a conll file, and the would parse the pre-tokenized data")
    p.add_argument('-2c', '--to_conll', dest='to_conll', action='store_true',
                   help="if passed the prase txt files of sentences and transform them in to conll file")
    p.add_argument('-nl', '--longest', dest='longest', action='store_false',
                   help="Not try to take the longest chunk (would not break in punctuation")
    p.add_argument('-nn', '--no_nested', dest='nested', action='store_false', help="Dont allow nested NP chunks")
    p.add_argument('-nms', '--no_merge_subtoken', dest='merge_subtoken', action='store_false',
                   help="Don't break words to its morphemes merge their subtokens (morphemes)."
                        "\ne.g. we get:  ב ה בית -> בבית"
                        "\nInstead of: ב ה בית -> ב_ _ה_ _בית")
    p.add_argument('-ntl', '--not_time_and_location', dest='time_and_location', action='store_false',
                   help="Tag time (אתמול, מחר etc.) and location (שם, כאן etc.) adverbs as NPs ")
    p.add_argument('-np', '--not_possessive', dest='possessive', action='store_false',
                   help="Do not connect use possessive term (של) in A chunk.")
    return p.parse_args()


class StanzaChunker:
    def __init__(self, is_conll: bool, chunker: Chunker=None ):
        self.is_conll = is_conll
        self.pre_tok = is_conll
        self.chunker = chunker
        self.conll_reader = ConllReader()
        self.parser = StanzaParser(pre_tokenized=self.pre_tok)

    def get_conll_file(self, input_file):
        docs = self.conll_reader.read_conll(input_file, input_encoding="utf-8", merge_subtoken=False)
        return docs

    def get_text_file(self, input_file):
        with open(input_file, encoding='utf-8') as f:
            text = "\n".join(f.readlines())
        docs = self.parse_text(text)
        return docs

    def parse_file(self, input_file):
        if "seg_only" in input_file:  # TODO refactor it to something less ugly
            sentences = self.parse_segmented_file(input_file)
        elif self.is_conll:
            sentences = []
            docs = self.get_conll_file(input_file)
            for doc in docs:
                tokens = [i.text for i in doc]
                sentences.append(tokens)
        else:
            sentences = self.get_text_file(input_file)
        return sentences

    def conll_dump(self, output_file, spacy_docs, type_output, ):
        with open(output_file, mode="w", encoding="utf-8") as f:
            for doc in spacy_docs:
                for w, t in zip(doc, self.chunker.get_noun_chunks(doc, type_output)):
                    if w._.original_text != "":
                        f.write(f"{w._.original_text} {t}\n")
                    else:
                        f.write(f"{w} {t}\n")
                f.write("\n")

    def json_dump(self, output_file, spacy_docs, type_output):
        with open(output_file, mode="w", encoding="utf-8") as f:
            for i, doc in enumerate(spacy_docs):
                sample = self.get_sample(doc, type_output, i)
                f.write(f"{json.dumps(sample)}\n")

    def get_sample(self, doc, type_output, sent_id):
        sample = {'tokens': [], 'labels': [], "sent_id": sent_id}
        for token, label in zip(doc, self.chunker.get_noun_chunks(doc, type_output)):
            token = token._.original_text if token._.original_text != "" else str(token)
            sample['tokens'].append(token)
            sample['labels'].append(label)
        return sample

    def run(self, input_file, output_file, type_output, output_format, dump_conll=False):
        sents = self.parse_file(input_file)
        docs = self.parser(sents)
        conll = self.parser.doc2conll(docs)
        if dump_conll:
            conll_fname = Path(output_file).stem + "_conll.conll"
            output_conll = Path(output_file).parent.joinpath(conll_fname)
            output_conll.write_text(conll.strip())
        spacy_docs = self.conll_reader.read_conll(conll.strip(), "utf-8", merge_subtoken=False)
        if output_format == "conll":
            self.conll_dump(output_file, spacy_docs, type_output)
        elif output_format == "json":
            self.json_dump(output_file, spacy_docs, type_output)
        else:
            raise ValueError(f"Not supporting this output format. Given {output_format}, but supports: json, conll")

    def parse_text(self, input_text, to_print=False):
        sents_temp = input_text.split("\n\n")
        sents = []
        for text in sents_temp:
            final_text = text.strip("").strip("\n")
            if final_text != "":
                sents.append(final_text)
        if to_print:
            for s in sents:
                print(s)
        return sents

    def parse_segmented_file(self, input_file):
        dt = pd.read_csv(input_file)
        sentences = []
        for i, g in dt.groupby("sent_id"):
            sentences.append(g["form"].to_list())
        return sentences


def stanza_ud_np_chunk_pipeline():
    print(Warning("Better to use the chunk runner flow, this one is old and not tested"))
    args = parse_arguments()
    if args.is_conll:
        chunker = Chunker(take_longest=args.longest, allow_nested=args.nested, allow_loc_time_adv=args.time_and_location,
                          possessive=args.possessive)
        pipe = StanzaChunker(chunker=chunker, is_conll=args.is_conll)
        pipe.run(args.input, args.output,args.type, args.output_format, dump_conll=True)
    else:
        pipe = StanzaChunker(is_conll=args.is_conll)
        sents = pipe.parse_file(args.input)
        with open(args.output, mode="w", encoding="utf-8") as f:
            for i, sent in enumerate(sents):
                # # sent_id = 1
                # # text = עשרות אנשים מגיעים מתאילנד לישראל כשהם נרשמים כמתנדבים, אך למעשה משמשים עובדים שכירים זולים.
                f.write(f"# sent_id = {i+1}\n")
                f.write(f"# text = {sent}\n")
                doc = pipe.parser.doc2conll(pipe.parser(sent))
                f.write(doc)




if __name__ == '__main__':
    import sys

    sys.path.append("../")
    sys.path.append(".")
    sys.path.append("../np_chunker")
    stanza_ud_np_chunk_pipeline()

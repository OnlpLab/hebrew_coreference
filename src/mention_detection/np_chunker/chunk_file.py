import argparse
import dataclasses
import json
import logging.config
import os
import re
from collections import defaultdict
from pathlib import Path
import glob

from tqdm import tqdm

from .chunker import Chunker
from .conll_reader import ConllReader
# from ..trankit_parser.trankit2spacy import Trankit2Spacy  # Temporarily disabled due to compatibility issues
from .webbano_utils import open_web_anno_tsv, AnnotatedSentence, Span, Annotation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s",
                    handlers=[logging.StreamHandler()])
logger = logging.getLogger(__file__)


def get_full_annotation(chunks, doc, start_idx=0):
    return [Annotation(label=label,
                       text=doc[start_tok:end_tok].text,
                       start=doc[start_tok:end_tok].start_char,
                       stop=doc[start_tok:end_tok].end_char,
                       id=i + start_idx) for i, (start_tok, end_tok, label) in
            enumerate(chunks)]


def parse_arguments():
    p = argparse.ArgumentParser(description='Np chunker flow')
    p.add_argument('input', help="input file expect UD conll file")
    p.add_argument('output', help="output file chunked to NP")
    p.add_argument('type', help="Choose between {BIO, BIOSE, webanno, json} when choosing webanno, the file would dump"
                                "as an output file in a Webanno tsv 3.* format see"
                                " https://inception-project.github.io/releases/22.2/docs/user-guide.html#sect_formats_webannotsv3 ")
    p.add_argument('-p', '--praser', dest='parser', nargs='?', const='spacy', default='spacy',
                   help="support {spacy, trankit} parser")
    p.add_argument('-l', '--longest', dest='longest', action='store_true',
                   help="Try to take the longest chunk (would not break in punctuation")
    p.add_argument('-n', '--nested', dest='nested', action='store_true', help="Allow nested NP chunks")
    p.add_argument('-ms', '--merge_subtoken', dest='merge_subtoken', action='store_true',
                   help="Don't break words to its morphemes merge their subtokens (morphemes)."
                        "\ne.g. we get:  ב ה בית -> בבית"
                        "\nInstead of: ב ה בית -> ב_ _ה_ _בית")
    p.add_argument('-ntl', '--not_time_and_location', dest='time_and_location', action='store_false',
                   help="Tag time (אתמול, מחר etc.) and location (שם, כאן etc.) adverbs as NPs ")
    p.add_argument('-np', '--no_possessive', dest='possessive', action='store_false',
                   help="Do not connect use possessive term (של) in A chunk.")
    p.add_argument('-iq', '--inner_quantitative', dest='inner_quantitative', action='store_true',
                   help="Do not add the inner mentions of a quantitative NP to the chunk.")
    p.add_argument('-ia', '--inner_acl', dest='inner_acl', action='store_true',
                   help="Do not add the inner mentions of the acl NP to the chunk.")
    p.add_argument('-t', '--tokenize', dest='tokenize', action='store_true',
                   help="tokenize the input - if True, expect a row file.")
    p.add_argument('-p50', '--pick50', dest='pick_50', action='store_true', help="pick 50 random sentences.")
    return p.parse_args()


class TneDocument:
    def __init__(self, title):
        self.title = title
        self.text = title + " "
        self.nps = []
        self.idx = ""
        self.cur_cursor = len(title) + 1
        self.title_start = 0
        self.title_end = len(title)

    def __str__(self):
        return self.text


class TneNP:
    def __init__(self, text, start_index, end_index, start_token, end_token, sent_num, idx):
        self.text = text
        self.start_index = start_index
        self.end_index = end_index
        self.start_token = start_token
        self.end_token = end_token
        self.sent_num = sent_num
        self.id = idx

@dataclasses.dataclass
class LlmNP:
    def __init__(self, text, start_token, end_token, sent_num, idx):
        self.text = text
        self.start_token = start_token
        self.end_token = end_token
        self.sent_num = sent_num
        self.id = idx

def dump_bio_conllu(args, chunker, docs):
    with open(args.output, mode="w", encoding="utf-8") as f:
        for doc in docs:
            for token, label in zip(doc, chunker.get_noun_chunks(doc, args.type)):
                # For the case of joined sub token strings are different than the original string
                # e.g. בבית -> ב ה בית 0 -> בהבית
                # instead of בבית
                if token._.original_text != "":
                    f.write(f"{token._.original_text} {label}\n")
                else:
                    f.write(f"{token} {label}\n")
            f.write("\n")


def dump_json(args, chunker, docs):
    with open(args.output, mode="w", encoding="utf-8") as f:
        for i, doc in enumerate(docs):
            sample = {'tokens': [], 'labels': [], "sent_id": i}
            for token, label in zip(doc, chunker.get_noun_chunks(doc, "BIOSE")):
                token = token._.original_text if token._.original_text != "" else str(token)
                sample['tokens'].append(token)
                sample['labels'].append(label)
            f.write(f"{json.dumps(sample)}\n")


def dump_webanno(args, chunker, docs):
    with open_web_anno_tsv(args.output, "w") as f1:
        for doc in docs:
            chunks = chunker.get_noun_chunks(doc, args.type)
            tokens = [Span(tok.text, tok.idx, tok.idx + len(tok.text), True, tok.i) for tok in doc]
            annotations = get_full_annotation(chunks, doc)
            sentence = AnnotatedSentence(doc.text, tokens, annotations)
            f1.write(sentence)


def run_chunker(args):
    if args.parser == 'trankit':
        docs = run_trankit(args)
    elif args.parser == 'stanza':
        docs = run_stanza(args)
    else:
        conll = ConllReader()
        docs = conll.read_conll(args.input, input_encoding="utf-8", merge_subtoken=args.merge_subtoken)
        if args.pick_50:
            docs = pick_50_random_sents(docs)
    return docs


def run_stanza(args):
    from stanza_parser import StanzaParser
    with open(Path(args.input).resolve(), encoding='utf-8') as f:
        sents = f.readlines()
    if args.pick_50:
        sents = pick_50_random_sents(sents)
    # TODO need to make it more intuitive,  stanza have a variable that say if the text is already pretokenized.
    #      When my flow ask if to tokenize. so, if the text is pretoknzied (True)- you dont need to tokenize (tok==Flase)
    is_input_pretokenize = not args.tokenize
    if is_input_pretokenize:
        sents = [s.split() for s in sents if s != ""]
    p = StanzaParser(pre_tokenized=is_input_pretokenize)
    parsed_docs = p(sents)
    conll_doc = p.doc2conll(parsed_docs)
    conll = ConllReader()
    docs = conll.read_conll(conll_doc, input_encoding="utf-8", merge_subtoken=args.merge_subtoken)
    return docs


def run_trankit(args):
    from trankit import Pipeline
    with open(Path(args.input).resolve(), encoding='utf-8') as f:
        sents = f.readlines()
    if args.pick_50:
        sents = pick_50_random_sents(sents)
    cur_fpath = os.path.abspath(os.path.dirname(__file__))
    p = Pipeline('hebrew', cache_dir=os.path.join(cur_fpath, "..", "trankit_parser", "trankit_cache"), gpu=False)
    t2s = Trankit2Spacy()
    if args.tokenize:
        sents = "".join([s for s in sents if s != ""])
    else:
        sents = [s.split() for s in sents if s != ""]
    parsed_sents = p(sents)
    docs = [t2s.transform(sent) for sent in parsed_sents['sentences']]
    return docs


def pick_50_random_sents(docs):
    import random
    random.seed(1)
    docs = list(docs)
    docs = [docs[i] for i in sorted(random.sample(range(len(docs)), 50))]
    return docs


def create_50_clean_sents():
    import random
    random.seed(1)

    inputs = r"corpus/UD_Hebrew-HTB/he_htb-ud-dev.conllu"
    outputs = r"np_chunk_output/50_clean_sentences.webaano"

    conll = ConllReader()
    docs = conll.read_conll(inputs, input_encoding="utf-8", merge_subtoken=False)
    logger.info(f"Input file: {Path(inputs).absolute()}")
    logger.info(f"Output file file: {Path(outputs).absolute()}")
    docs = list(docs)
    random_docs = [docs[i] for i in sorted(random.sample(range(len(docs)), 50))]

    with open_web_anno_tsv(outputs, "w") as f1:
        for doc in random_docs:
            tokens = [Span(tok.text, tok.idx, tok.idx + len(tok.text), True, tok.i) for tok in doc]
            sentence = AnnotatedSentence(doc.text, tokens, [])
            f1.write(sentence)


def build_tne_formatted_doc(docs_json):
    jsons = []
    for doc in docs_json:
        nps = [np.__dict__ for np in doc.nps]
        done_nps = {np.id: False for np in doc.nps}
        json_doc = {"nps": nps, 'done_nps': done_nps, 'pronouns': [],
                    "tx": {'raw_text': doc.text, 'title': {'start_index': doc.title_start, 'end_index': doc.title_end},
                           'subtitles': [],
                           'paragraphs': [{"start_index": doc.title_end + 1, "end_index": len(doc.text), "id": 1}], },
                    "source_file": "test_formatted.json", "url": "", "text_id": doc.idx

                    }
        jsons.append(json_doc)
    return jsons


def make_doc_files_inception():
    args = parse_arguments()
    chunker = Chunker(take_longest=args.longest, allow_nested=args.nested, allow_loc_time_adv=args.time_and_location,
                      possessive=args.possessive, allow_inner_quantitative=args.inner_quantitative,
                      allow_inner_acl=args.inner_acl)
    conll = ConllReader()
    docs = conll.read_conll(args.input, input_encoding="utf-8", merge_subtoken=args.merge_subtoken)
    docs_output = defaultdict(list)
    for doc in docs:
        chunks = chunker.get_noun_chunks(doc, args.type)
        tokens = [Span(tok.text, tok.idx, tok.idx + len(tok.text), True, tok.i) for tok in doc]
        annotations = get_full_annotation(chunks, doc)
        sentence = AnnotatedSentence(doc.text, tokens, annotations)
        docs_output[list(doc.sents)[0]._.doc_id].append(sentence)
    for doc_id, sentences in tqdm(docs_output.items(), desc="Writing docs"):
        with open_web_anno_tsv(f"{args.output}/doc_{doc_id.split(':')[1]}.webbano", "w") as f1:
            for sentence in sentences:
                f1.write(sentence)


def make_doc_files_tne():
    """
    Run with:
    HebNpChunker/make_tne_docs.py corpus/coref_docs_2_tag/base corpus/coref_docs_2_tag/tne tne -n -l
    """
    args = parse_arguments()
    chunker = Chunker(take_longest=args.longest,
                      allow_nested=args.nested,
                      allow_loc_time_adv=args.time_and_location,
                      possessive=args.possessive,
                      allow_inner_quantitative=args.inner_quantitative,
                      allow_inner_acl=args.inner_acl)
    conll = ConllReader()
    files = glob.glob(f"{args.input}/*.conllu")
    for i, file in enumerate(files):
        docs = conll.read_conll(file, input_encoding="utf-8", merge_subtoken=args.merge_subtoken)
        format_json = get_tne_json(chunker, docs, idx=i)
        with open(args.output + "/" + Path(file).name.replace("conllu", "tne"), mode="w", encoding="utf-8") as f:
            json.dump(format_json, f, ensure_ascii=False, indent=4)

def make_paper_mentions_by_danit_for_llm():
    """
    Run with:
    HebNpChunker/make_paper_mentions_by_danit_for_llm.py corpus/coreference_final_split/parsed_danit corpus/coreference_final_split/mentions_by_parsed tne -n -l
    """

    @dataclasses.dataclass
    class Mention:
        sent_num: int
        start: int
        end: int
        text: str
        id: int

    def to_coref_format(param, cluster_id):
        if param == "start":
            return f"({cluster_id}"
        elif param == "end":
            return f"{cluster_id})"
        else:
            raise ValueError(f"param can be only {{start, end}} but is {param}")

    def format_loc(sent_num, token_num):
        return f"{sent_num}:{token_num}"

    args = parse_arguments()
    chunker = Chunker(take_longest=args.longest,
                      allow_nested=args.nested,
                      allow_loc_time_adv=args.time_and_location,
                      possessive=args.possessive,
                      allow_inner_quantitative=args.inner_quantitative,
                      allow_inner_acl=args.inner_acl)
    conll = ConllReader()
    for dataset in [ "dev", "test"]:
        files = glob.glob(f"{args.input}/{dataset}/htb:*")
        for i, file in enumerate(files):
            docs = list(conll.read_conll(file, input_encoding="utf-8", merge_subtoken=args.merge_subtoken))
            nps = get_nps_for_llm(chunker, docs)
            mentions = []
            for np in nps:
                mentions.append(Mention(np['sent_num'], np['start_token'], np['end_token'] - 1, np['text'], np['id']))

            clusters_dict = defaultdict(list)
            text = ""
            text += f"#begin document {str(Path(file).name)}\n"

            for mention in mentions:
                entry_start = format_loc(mention.sent_num, mention.start)

                if mention.start != mention.end:
                    clusters_dict[entry_start].append(to_coref_format('start', mention.id))

                    entry_end = format_loc(mention.sent_num, mention.end)
                    clusters_dict[entry_end].append(to_coref_format('end', mention.id))
                else:

                    clusters_dict[entry_start].append(f"({mention.id})")

            for sent_num, sent in enumerate(docs):
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

            os.makedirs(os.path.join(args.output,dataset), exist_ok=True)
            with open(os.path.join(args.output,dataset,f"{Path(file).name}.conllu"), mode="w", encoding="utf-8") as f:
                f.write(text)


def make_paper_mentions_by_gold_parse_for_llm():
    """
    Run with:
    HebNpChunker/make_paper_mentions_by_gold_parse_for_llm.py corpus/coref_docs_2_tag/base corpus/coreference_final_split/mentions_by_gold_parse tne -n -l
    """

    @dataclasses.dataclass
    class Mention:
        sent_num: int
        start: int
        end: int
        text: str
        id: int

    def to_coref_format(param, cluster_id):
        if param == "start":
            return f"({cluster_id}"
        elif param == "end":
            return f"{cluster_id})"
        else:
            raise ValueError(f"param can be only {{start, end}} but is {param}")

    def format_loc(sent_num, token_num):
        return f"{sent_num}:{token_num}"

    args = parse_arguments()
    chunker = Chunker(take_longest=args.longest,
                      allow_nested=args.nested,
                      allow_loc_time_adv=args.time_and_location,
                      possessive=args.possessive,
                      allow_inner_quantitative=args.inner_quantitative,
                      allow_inner_acl=args.inner_acl)
    conll = ConllReader()
    for dataset in [ "dev", "test"]:
        source_files = glob.glob(f"corpus/coreference_final_split/parsed_danit/{dataset}/htb:*")
        htb_numbers = set()
        for file in source_files:
            match = re.search(r'htb[:_](\d+(?:_\d+)?)', os.path.basename(file))
            if match:
                htb_numbers.add(match.group(1))  # Store only the number part

        # Filter files based on extracted htb numbers
        all_files = glob.glob(f"{args.input}/*")
        files = [f for f in all_files if any(f"htb_{num}." in os.path.basename(f) for num in htb_numbers)]
        for i, file in enumerate(files):
            docs = list(conll.read_conll(file, input_encoding="utf-8", merge_subtoken=args.merge_subtoken))
            nps = get_nps_for_llm(chunker, docs)
            mentions = []
            for np in nps:
                mentions.append(Mention(np['sent_num'], np['start_token'], np['end_token'] - 1, np['text'], np['id']))

            clusters_dict = defaultdict(list)
            text = ""
            text += f"#begin document {str(Path(file).name)}\n"

            for mention in mentions:
                entry_start = format_loc(mention.sent_num, mention.start)

                if mention.start != mention.end:
                    clusters_dict[entry_start].append(to_coref_format('start', mention.id))

                    entry_end = format_loc(mention.sent_num, mention.end)
                    clusters_dict[entry_end].append(to_coref_format('end', mention.id))
                else:

                    clusters_dict[entry_start].append(f"({mention.id})")

            for sent_num, sent in enumerate(docs):
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

            os.makedirs(os.path.join(args.output,dataset), exist_ok=True)
            pattern = r'htb_\d+(?:_\d+)?'
            file_name = re.search(pattern, Path(file).name).group().strip("htb_")
            with open(os.path.join(args.output,dataset,f"htb:{file_name}"), mode="w", encoding="utf-8") as f:
                f.write(text)




def chunker_main():
    args = parse_arguments()
    chunker = Chunker(take_longest=args.longest, allow_nested=args.nested, allow_loc_time_adv=args.time_and_location,
                      possessive=args.possessive, allow_inner_quantitative=args.inner_quantitative,
                      allow_inner_acl=args.inner_acl)
    docs = run_chunker(args)
    logger.info(f"Input file: {Path(args.input).absolute()}")
    logger.info(f"Output file file: {Path(args.output).absolute()}")
    logger.info(f"Tagging scheme: {args.type}")
    logger.info(f"Tag longest chunk (greedy mode): {args.longest}")
    logger.info(f"Tag nested chunk: {args.nested}")
    logger.info(f"Merge sub tokens: {args.merge_subtoken}")
    logger.info(f"Allow possessive: {args.possessive}")
    logger.info(f"Add inner quantitative: {args.inner_quantitative}")
    logger.info(f"Add inner acl: {args.inner_acl}")
    if args.type == "webanno":
        dump_webanno(args, chunker, docs)
    elif args.type == "json":
        dump_json(args, chunker, docs)
    elif args.type == "tne":
        dump_tne(args, chunker, docs)
    else:
        dump_bio_conllu(args, chunker, docs)


def dump_tne(args, chunker, docs):
    format_json = get_tne_json(chunker, docs)
    with open(args.output, mode="w", encoding="utf-8") as f:
        json.dump(format_json, f, ensure_ascii=False, indent=4)


def get_tne_json(chunker, docs, idx=None):
    cur_doc_id = None
    current_document = None
    docs_json = []
    number_of_nps = 0
    for doc_idx, doc in enumerate(docs):
        doc_id = get_doc_id(doc)
        if doc_id != cur_doc_id:
            if current_document:
                docs_json.append(current_document)
            current_document = TneDocument(doc_id)
            cur_doc_id = doc_id
            number_of_nps = 0
        chunks = chunker.get_noun_chunks(doc, "flat")
        chunks.sort(key=lambda annotation: annotation[1])
        annotations = [TneNP(text=doc[start:end].text,
                             start_index=doc[start].idx + current_document.cur_cursor,
                             end_index=doc[start].idx + len(doc[start:end].text) + current_document.cur_cursor,
                             start_token=start,
                             end_token=end,
                             sent_num=doc_idx,
                             idx=i + number_of_nps)
                       for i, (start, end, _) in enumerate(chunks)]
        number_of_nps += len(chunks)
        current_document.nps.extend(annotations)
        current_document.text += doc.text
        current_document.cur_cursor += len(doc.text)
    docs_json.append(current_document)
    format_json = build_tne_formatted_doc(docs_json)
    return format_json

def get_nps_for_llm(chunker, docs):
    number_of_nps = 0
    nps = []
    for doc_idx, doc in enumerate(docs):
        chunks = chunker.get_noun_chunks(doc, "flat")
        chunks.sort(key=lambda annotation: annotation[1])
        annotations = [ LlmNP(text=doc[start:end].text,
                              start_token=start,
                              end_token=end,
                              sent_num=doc_idx,
                              idx=i + number_of_nps)
                        for i, (start, end, _) in enumerate(chunks)]
        number_of_nps += len(chunks)
        nps.extend(annotations)
    return [np.__dict__ for np in nps]




def get_doc_id(doc):
    try:
        doc_id = list(doc.sents)[0]._.doc_id
    except Exception:
        raise ValueError(f"Seem that for the sentence: {doc} there is no doc_id. please check your file.")
    return doc_id


if __name__ == '__main__':
    # chunker_main()
    import sys

    sys.path.append(".")
    sys.path.append(".")
    create_50_clean_sents()

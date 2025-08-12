from pathlib import Path

from typing import Dict, Union
import re

import spacy_udpipe
from spacy.tokens import Doc, Token, Span
from spacy.training.converters.conllu_to_docs import get_entities
from spacy.training.iob_utils import spans_from_biluo_tags


class ConllReader:
    ner_tag_pattern: str = "^((?:name|NE)=)?([BILU])-([A-Z_]+)|O$"
    ner_map: Dict[str, str] = None
    try:
        vocab = spacy_udpipe.load("he").vocab
    except AssertionError as e:
        spacy_udpipe.download("he")
        vocab = spacy_udpipe.load("he").vocab

    def __init__(self):
        self.MAX_PATH_SIZE = 1024
        self.set_conllu_tokens_attribues()
        self.set_merged_tokens_attributes()

    def set_merged_tokens_attributes(self):
        if not Token.has_extension("original_text"):
            Token.set_extension("original_text", default="")
        if not Token.has_extension("merged_orth"):
            Token.set_extension("merged_orth", default="")
        if not Token.has_extension("merged_lemma"):
            Token.set_extension("merged_lemma", default="")
        if not Token.has_extension("merged_morph"):
            Token.set_extension("merged_morph", default="")
        if not Token.has_extension("merged_spaceafter"):
            Token.set_extension("merged_spaceafter", default="")
    def set_conllu_tokens_attribues(self):
        if not Token.has_extension("conll_misc_field"):
            Token.set_extension("conll_misc_field", default="_")
        if not Token.has_extension("conll_deps_graphs_field"):
            Token.set_extension("conll_deps_graphs_field", default="_")
        if not Span.has_extension("conll_metadata"):
            Span.set_extension("conll_metadata", default=None)
        if not Span.has_extension("doc_id"):
            Span.set_extension("doc_id", default=None)
        if not Span.has_extension("sent_id"):
            Span.set_extension("sent_id", default=None)
        if not Span.has_extension("text"):
            Span.set_extension("text", default=None)



    def merge_conllu_subtokens(self, lines, doc: Doc):
        # identify and process all subtoken spans to prepare attrs for merging
        subtok_spans = []
        span_original_text = []
        for line in lines:
            parts = line.split("\t")
            id_, word, lemma, pos, tag, morph, head, dep, _1, misc = parts
            if "-" in id_:
                span_original_text.append(word)
                subtok_start, subtok_end = id_.split("-")
                subtok_span = doc[int(subtok_start) - 1: int(subtok_end)]
                subtok_spans.append(subtok_span)
                # create merged tag, morph, and lemma values
                tags = []
                morphs = {}
                lemmas = []
                for token in subtok_span:
                    tags.append(token.tag_)
                    lemmas.append(token.lemma_)
                    if token._.merged_morph:
                        for feature in token._.merged_morph.split("|"):
                            field, values = feature.split("=", 1)
                            if field not in morphs:
                                morphs[field] = set()
                            for value in values.split(","):
                                morphs[field].add(value)
                # create merged features for each morph field
                for field, values in morphs.items():
                    morphs[field] = field + "=" + ",".join(sorted(values))
                # set the same attrs on all subtok tokens so that whatever head the
                # retokenizer chooses, the final attrs are available on that token
                for token in subtok_span:
                    token._.original_text = word
                    token._.merged_orth = token.orth_
                    token._.merged_lemma = " ".join(lemmas)
                    token.tag_ = "_".join(tags)
                    token._.merged_morph = "|".join(sorted(morphs.values()))
                    token._.merged_spaceafter = (True if subtok_span[-1].whitespace_ else False)
        with doc.retokenize() as retokenizer:
            for span in subtok_spans:
                retokenizer.merge(span)
        return doc


    def read_conll(self, inputs: Union[Path, str], input_encoding, merge_subtoken):
        """ Yield examples, one for each sentence """

        if (type(inputs) == str and len(inputs) < self.MAX_PATH_SIZE) and Path(inputs).exists():
            text = Path(inputs).resolve().read_text(encoding=input_encoding).strip()
        elif self.is_valid_path(inputs):
            raise NotADirectoryError(f"the path: {inputs} is not valid!")
        else:
            text = inputs
        for chunk in text.split("\n\n"):
            if chunk == "":
                continue
            doc = self.single_conll(chunk, merge_subtoken)
            yield doc

    def single_conll(self, txt_chunk, merge_subtoken):
        lines = [l for l in txt_chunk.splitlines() if l and not l.startswith("#")]
        words, spaces, tags, poses, morphs, lemmas, miscs = [], [], [], [], [], [], []
        heads, deps, deps_graphs = [], [], []
        in_subtok = False
        for i in range(len(lines)):
            dep, deps_graph, head, id_, lemma, misc, morph, pos, tag, word = self.get_line_params(i, lines)
            if "." in id_:
                continue
            if "-" in id_:
                in_subtok = True
                subtok_start, subtok_end = id_.split("-")
                subtok_spaceafter = "SpaceAfter=No" not in misc
                continue
            if merge_subtoken and in_subtok:
                words.append(word.strip("_") if word != "__" else word)
            else:
                words.append(word)
            if in_subtok:
                if id_ == subtok_end:
                    spaces.append(subtok_spaceafter)
                else:
                    spaces.append(False)
            elif "SpaceAfter=No" in misc:
                spaces.append(False)
            else:
                spaces.append(True)
            if in_subtok and id_ == subtok_end:
                in_subtok = False

            id_ = int(id_) - 1
            lemmas.append(lemma)
            poses.append(pos)
            tags.append(pos if tag == "_" else tag)
            morphs.append(morph if morph != "_" else "")
            heads.append((int(head) - 1) if head not in ("0", "_") else id_)
            deps.append("ROOT" if dep == "root" else dep)
            deps_graphs.append(deps_graph)
            miscs.append(misc)
        try:
            doc = Doc(self.vocab, words=words, spaces=spaces, tags=tags, pos=poses, morphs=morphs, lemmas=lemmas, heads=heads,
                deps=deps)
        except Exception as e:
            print(e)
            print(words)
        # Set custom Token extensions
        for i in range(len(doc)):
            doc[i]._.conll_misc_field = miscs[i]
            doc[i]._.conll_deps_graphs_field = deps_graphs[i]
            doc[i]._.merged_orth = words[i]
            doc[i]._.merged_morph = morphs[i]
            doc[i]._.merged_lemma = lemmas[i]
            doc[i]._.merged_spaceafter = spaces[i]

        ents = get_entities(lines, self.ner_tag_pattern, self.ner_map)
        doc.ents = spans_from_biluo_tags(doc, ents)
        # The deprel relations ensure that this CoNLL chunk is one sentence
        # Deprel cannot therefore not be empty or each word is considered a separate sentence
        if len(list(doc.sents)) != 1:
            raise ValueError("Your data is in an unexpected format. Make sure that it follows the CoNLL-U format"
                             " requirements. See https://universaldependencies.org/format.html. Particularly make"
                             " sure that the DEPREL field is filled in.")
        # Save the metadata in a custom sentence Span attribute so that the formatter can use it
        metadata = "\n".join([l for l in txt_chunk.splitlines() if l.startswith("#")])
        # We really only expect one sentence
        for sent in doc.sents:
            sent._.conll_metadata = metadata if metadata else ""
            meta_lines = {l.strip("# ").split(" = ")[0]: l.strip("# ").split(" = ")[1]
                          for l in txt_chunk.splitlines() if l.startswith("#")}
            if 'doc_id' in meta_lines:
                sent._.doc_id = meta_lines['doc_id']
            if 'sent_id' in meta_lines:
                sent._.sent_id = meta_lines['sent_id']
            if 'text' in meta_lines:
                sent._.text = meta_lines['text']
        if merge_subtoken:
            doc = self.merge_conllu_subtokens(lines, doc)
        return doc

    def get_line_params(self, i, lines):
        line = lines[i]
        parts = line.split("\t")
        if any(not p for p in parts):
            raise ValueError("According to the CoNLL-U Format, fields cannot be empty. See"
                             " https://universaldependencies.org/format.html")
        id_, word, lemma, pos, tag, morph, head, dep, deps_graph, misc = parts
        if any(" " in f for f in (id_, pos, tag, morph, head, dep, deps_graph)):
            raise ValueError("According to the CoNLL-U Format, only FORM, LEMMA, and MISC fields can contain"
                             " spaces. See https://universaldependencies.org/format.html")
        return dep, deps_graph, head, id_, lemma, misc, morph, pos, tag, word

    def is_valid_path(self, path):
        pattern_unix = re.compile(r'^((\w)+)?(/[^/ ]*)+/?$')
        pattern_win = re.compile(r"^[A-Za-z]:(\\[^&><|\n\t?*:\\]+)+\\?$")
        match = pattern_win.match(path) or pattern_unix.match(path)
        return match


if __name__ == '__main__':
    path = r"C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\corpus\pathologic\mistakes_3.11"
    conll = ConllReader()
    res = list(conll.read_conll(path, input_encoding="utf-8", merge_subtoken=False))
    from spacy import displacy

    displacy.serve(res[2],host="localhost", port=5001, style="dep")


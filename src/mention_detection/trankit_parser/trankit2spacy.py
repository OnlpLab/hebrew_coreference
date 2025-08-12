from typing import Dict

import spacy_udpipe
from spacy.tokens import Doc, Token, Span
from dataclasses import dataclass, field
from typing import List

from trankit import Pipeline

from np_chunker import Chunker


@dataclass
class FlatSentence:
    words: List = field(default_factory=lambda: [])
    spaces: List = field(default_factory=lambda: [])
    tags: List = field(default_factory=lambda: [])
    poses: List = field(default_factory=lambda: [])
    morphs: List = field(default_factory=lambda: [])
    lemmas: List = field(default_factory=lambda: [])
    miscs: List = field(default_factory=lambda: [])
    heads: List = field(default_factory=lambda: [])
    deps: List = field(default_factory=lambda: [])
    deps_graphs: List = field(default_factory=lambda: [])


class Trankit2Spacy:
    ner_map: Dict[str, str] = None
    vocab = spacy_udpipe.load("he").vocab
    no_space_after = {"ב", "כ", "ל", "מ", "ה", "ו", "ש", "כש", "("}
    puncts = set(list(".,!?):-\""))

    def __init__(self):
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

    def enrich_sent(self, token: dict, flat_sentence: FlatSentence):

        id_ = int(token['id']) - 1
        flat_sentence.words.append(token['text'])
        flat_sentence.lemmas.append(token['lemma'])
        flat_sentence.poses.append(token['upos'])
        flat_sentence.tags.append(token['upos'] if token['xpos'] == "_" else token['xpos'])
        flat_sentence.morphs.append(token['feats'] if 'feats' in token else "")
        flat_sentence.heads.append((token['head'] - 1) if token['head'] != 0 else id_)  # TODO check
        flat_sentence.deps.append(self.get_deprel(token))
        flat_sentence.deps_graphs.append("_")
        flat_sentence.miscs.append("_")

    def get_deprel(self, token):
        if token['deprel'] == "det:def":
            return "det"
        elif token['deprel'] == "root":
            return "ROOT"
        else:
            return token['deprel']

    def transform(self, sentence, metadata=""):
        flat_sentence = FlatSentence()
        for i, token in enumerate(sentence['tokens']):
            # dep, deps_graph, head, id_, lemma, misc, morph, pos, tag, word = token
            if type(token['id']) == tuple:
                for i, inner_tok in enumerate(token['expanded']):
                    self.enrich_sent(inner_tok, flat_sentence)
                    if i < len(token["id"]) - 1:
                        flat_sentence.spaces.append(False)
                    else:
                        flat_sentence.spaces.append(True)
            else:
                self.enrich_sent(token, flat_sentence)
                if any([token["text"] in self.no_space_after,
                        i + 1 < len(sentence['tokens']) and sentence['tokens'][i + 1]['text'] in self.puncts,
                        token["text"].endswith("_")]):  # TODO might not be perfect
                    flat_sentence.spaces.append(False)
                else:
                    flat_sentence.spaces.append(True)

        try:
            doc = Doc(self.vocab, words=flat_sentence.words, spaces=flat_sentence.spaces, tags=flat_sentence.tags,
                      pos=flat_sentence.poses, morphs=flat_sentence.morphs, lemmas=flat_sentence.lemmas,
                      heads=flat_sentence.heads, deps=flat_sentence.deps)
        except Exception as e:
            print(e)
            print(flat_sentence.words)
            exit(1)
        # Set custom Token extensions
        for i in range(len(doc)):
            doc[i]._.conll_misc_field = flat_sentence.miscs[i]
            doc[i]._.conll_deps_graphs_field = flat_sentence.deps_graphs[i]
            doc[i]._.merged_orth = flat_sentence.words[i]
            doc[i]._.merged_morph = flat_sentence.morphs[i]
            doc[i]._.merged_lemma = flat_sentence.lemmas[i]
            doc[i]._.merged_spaceafter = flat_sentence.spaces[i]

        doc.ents = []  # TODO TBD if we include NER
        # The deprel relations ensure that this CoNLL chunk is one sentence
        # Deprel cannot therefore not be empty or each word is considered a separate sentence
        if len(list(doc.sents)) != 1:
            raise ValueError("Your data is in an unexpected format. Make sure that it follows the CoNLL-U format"
                             " requirements. See https://universaldependencies.org/format.html. Particularly make"
                             " sure that the DEPREL field is filled in.")
        # Save the metadata in a custom sentence Span attribute so that the formatter can use it
        # We really only expect one sentence
        for sent in doc.sents:
            sent._.conll_metadata = metadata
        return doc


if __name__ == '__main__':
    p = Pipeline('hebrew')
    # sent = p("תופעה זו התבררה אתמול ב וועדת ה עבודה ו ה רווחה של ה כנסת , ש דנה ב נושא העסקת עובדים זרים .".split(), is_sent=True)
    # sent = p("כל ה ישראלים ש עובדים ב דרום".split(), is_sent=True)
    sent = p("אדון שוקו הולך לבקר את חברו , אדון שוקו אחר.", is_sent=True)
    t2s = Trankit2Spacy()
    res = t2s.transform(sent)
    chunker = Chunker(take_longest=True, allow_nested=True, allow_loc_time_adv=True, possessive=True)

    print(list((t.text, c) for t,c in zip(res, chunker.get_noun_chunks(res, "BIOSE"))))

    from spacy import displacy

    options = {"collapse_punct": False}

    displacy.serve(res, options=options, host="localhost", port=5001, style="dep")

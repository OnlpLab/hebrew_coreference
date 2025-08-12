import stanza
from stanza.utils.conll import CoNLL
from tqdm import tqdm


class StanzaParser:

    def __init__(self, pre_tokenized: bool = False):
        self.pre_tokenized = pre_tokenized
        self.nlp = self.get_heb_model()

    def __call__(self, doc):
        return self.nlp(doc)


    def parse_and_dump_sents(self, sents, out_path):
        docs = [self.nlp(s) for s in sents]
        with open(out_path, 'w', encoding='utf-8') as outfile:
            for doc in tqdm(docs, desc="Stanza parsing"):
                outfile.write(self.doc2conll(doc))


    def doc2conll(self, doc):
        return CoNLL.doc2conll_text(doc)

    def get_heb_model(self):
        try:
            nlp = stanza.Pipeline('he', tokenize_pretokenized=self.pre_tokenized, tokenize_no_ssplit=True) # initialize English neural pipeline
        except Exception:
            print("Downloading model")
            stanza.download('he')
            nlp = stanza.Pipeline('he', tokenize_pretokenized=self.pre_tokenized, tokenize_no_ssplit=True)
        return nlp



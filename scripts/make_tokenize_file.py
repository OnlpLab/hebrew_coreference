import os
import stanza
from trankit import Pipeline


def extract_string(sent, text):
    for t in sent.tokens:
        if len(t.id) == 1:
            text += t.text
            text += " "
        else:
            for w in t.words:
                text += w.text
                text += " "
    return text

def extract_string_trankit(sent, text):
    for t in sent['tokens']:
        try:
            if type(t['id']) == int:
                text += t['text']
                text += " "
            else:
                for w in t['expanded']:
                    text += w['text']
                    text += " "
        except Exception:
            print(t)
            print(text)
    return text


def tokenize_sents_stanza(input_f, out_f, model):
    all_text = []
    with open(input_f, encoding='utf-8') as f:
        sentences = f.readlines()
    for s in sentences:
        tokenized = model(s)
        text = ""
        if len(tokenized.sentences) == 1:
            text = extract_string(tokenized.sentences[0], text)
        elif len(tokenized.sentences) > 1:
            for sent in tokenized.sentences:
                text = extract_string(sent, text)
        else:
            continue
        text = text.strip()
        print(text)
        text += "\n"
        all_text.append(text)
    with open(out_f, mode='w') as f:
        f.writelines(all_text)


def stanza_tokenize():
    heb = stanza.Pipeline("he", processors='tokenize', tokenize_pretokenized=False)
    tokenize_sents_stanza('../corpus/UD_row_sentence_only/he_htb-sent-dev.txt',
                   '../corpus/UD_row_stanza_seg_sentence/he_htb-sent-dev.txt', heb)
    tokenize_sents_stanza('../corpus/UD_row_sentence_only/he_htb-sent-test.txt',
                   '../corpus/UD_row_stanza_seg_sentence/he_htb-sent-test.txt', heb)


def tokenize_sents_trankit(input_f, out_f, model):
    all_text = []
    with open(input_f, encoding='utf-8') as f:
        sentences = f.readlines()
    for s in sentences:
        tokenized = model.tokenize(s)
        text = ""
        if len(tokenized["sentences"]) == 1:
            text = extract_string_trankit(tokenized["sentences"][0], text)
        elif len(tokenized["sentences"]) > 1:
            for sent in tokenized["sentences"]:
                text = extract_string_trankit(sent, text)
        else:
            continue
        text = text.strip()
        print(text)
        text += "\n"
        all_text.append(text)
    with open(out_f, mode='w') as f:
        f.writelines(all_text)



def trankit_tokenize():
    cur_fpath = os.path.abspath(os.path.dirname(__file__))
    p = Pipeline('hebrew', cache_dir=os.path.join(cur_fpath,"..", "trankit_parser", "cache", "trankit"), gpu=False)
    tokenize_sents_trankit('../corpus/UD_row_sentence_only/he_htb-sent-dev.txt',
                           '../corpus/UD_row_trankit_seg_sentence/he_htb-sent-dev.txt',
                           p)

    tokenize_sents_trankit('../corpus/UD_row_sentence_only/he_htb-sent-test.txt',
                           '../corpus/UD_row_trankit_seg_sentence/he_htb-sent-test.txt',
                           p)


if __name__ == '__main__':
    # stanza_tokenize()
    trankit_tokenize()
from spacy import displacy

from np_chunker import ConllReader


def serve_parse():
    conll = ConllReader()
    path = "/Users/s0g0a87/studies/HebNpChunker/corpus/UD_Hebrew-HTB/he_htb-ud-dev.conllu"
    res = list(conll.read_conll(path, input_encoding="utf-8", merge_subtoken=False))
    options = {"collapse_punct": False}
    displacy.serve(res, options=options, host="localhost", port=5001, style="dep")

def format_sent(num, sent):
    l1 = f"<p><b>משפט {num}</b></p>\n"
    l2 = f"<p>{sent}</p>\n"
    return l1, l2

def add_sentence_to_html(path, dev):
    with open(path, encoding="utf-8") as f:
        lines = f.readlines()
    conll = ConllReader()
    res = list(conll.read_conll(dev, input_encoding="utf-8", merge_subtoken=False))
    sentences = [s.text for s in res]
    to_insert = []
    line_to_insert = []
    for i, l in enumerate(lines):
        if l.startswith('<figure'):
            to_insert.append(i)
    for j, sent in enumerate(sentences):
        new_lines = format_sent(j+1, sent)
        line_to_insert.append(new_lines)

    added = 0
    for n, cur_new_lines in zip(to_insert, line_to_insert):
        new_n = n + 2*added
        lines[new_n:new_n] = cur_new_lines
        added+=1
    with open("new_with_sents.html",mode="w", encoding="utf-8") as fn:
        fn.writelines(lines)

if __name__ == '__main__':
    add_sentence_to_html("displaCy_all_dev.html", "/Users/s0g0a87/studies/HebNpChunker/corpus/UD_Hebrew-HTB/he_htb-ud-dev.conllu")
    serve_parse()

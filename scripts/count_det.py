from np_chunker import ConllReader
"""
Script for counting how many determiners there are in in a Conllu file
"""
conll = ConllReader()
det_pos_dict = {}

def add_det(docs,det_pos, det_tag):
    seen =set()
    for doc in docs:
        det_pos = det_pos.union(set([t.lemma_ for t in doc if t.pos_ == "DET"]))
        det_tag = det_tag.union(set([t.lemma_ for t in doc if t.dep_ == "det"]))
        for t in doc:
            if (t.pos == "DET" or t.dep_ == "det")  and t.lemma_ != t.text:
                if (t.text+t.lemma_) not in seen:
                    print(f"lemma: {t.lemma_}\ttext: {t.text}")
                    seen.add((t.text+t.lemma_))
        for p in set([t.lemma_ for t in doc if t.dep_ == "det"]):
            if p not in det_pos_dict:
                det_pos_dict[p] = doc.text
    return det_pos, det_tag


det_pos = set()
det_tag = set()
train = conll.read_conll("../corpus/UD_Hebrew-HTB/he_htb-ud-train.conllu", input_encoding="utf-8", merge_subtoken=False)
dev = conll.read_conll("../corpus/UD_Hebrew-HTB/he_htb-ud-dev.conllu", input_encoding="utf-8", merge_subtoken=False)
det_pos, det_tag = add_det(train, det_pos, det_tag)
det_pos, det_tag = add_det(dev, det_pos, det_tag)

print("det pos:\n ", det_pos)
print("det tag:\n", det_tag)
print("intersection:\n", det_tag.intersection(det_pos))
print("difference:\n", det_tag.symmetric_difference(det_pos))
print(f"total det {len(det_tag.union(det_pos))}")
print("union:\n", det_tag.union(det_pos))


for k, v in det_pos_dict.items():
    print(f"{k}: {v}")




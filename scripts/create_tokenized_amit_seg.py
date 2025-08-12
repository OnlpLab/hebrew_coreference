from pathlib import Path
from conllu import parse
from tqdm import tqdm

datasets = [ "dev", "test"]

problematic_lemma = {"ל"}
problematic_pre_tok = "לה"
problematic_token = {"להם"}
for ds in datasets:
    input_path = f"../np_data/test_data/amit_seg/{ds}_conll.conll"
    output_path = f"../corpus/UD_row_amit_seg_sentence/he_htb-ud-{ds}.txt"
    text = Path(input_path).resolve().read_text(encoding='utf-8').strip()
    docs = parse(text)
    with open(output_path, mode='w', encoding='utf-8') as f_out:
        for doc in tqdm(docs, desc=f"dataset {ds}"):
            tokens = []
            for i, tok in enumerate(doc):
                if type(tok['id']) == int:
                    if tok['lemma'] in problematic_lemma and len(tok['form']) > len(tok['lemma']): #fix bug in amit file ל ->לו להם להן
                        tokens.append(tok['lemma'])
                    elif tok['lemma'] == problematic_pre_tok and doc[i+1]['form'] in "_היא":
                        tokens.append("ל")
                    else:
                        tokens.append(tok['form'])
            toknized_sent = " ".join(tokens) + "\n"
            f_out.write(toknized_sent)



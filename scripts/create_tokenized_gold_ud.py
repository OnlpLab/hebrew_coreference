from pathlib import Path
from conllu import parse
from tqdm import tqdm

datasets = ["train", "dev", "test"]
for ds in datasets:
    input_path = f"../corpus/UD_Hebrew-HTB/he_htb-ud-{ds}.conllu"
    output_path = f"../corpus/UD_row_tokenized_sentence/he_htb-ud-{ds}.txt"
    text = Path(input_path).resolve().read_text(encoding='utf-8').strip()
    docs = parse(text)
    with open(output_path, mode='w', encoding='utf-8') as f_out:
        for doc in tqdm(docs, desc=f"dataset {ds}"):
            tokens = [i['form'] for i in doc if type(i['id']) == int ]
            toknized_sent = " ".join(tokens) + "\n"
            f_out.write(toknized_sent)



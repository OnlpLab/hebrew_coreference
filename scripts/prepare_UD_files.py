files_path = "../corpus/UD_Hebrew-HTB/he_htb-ud-{}.conllu"
out_path ="../corpus/UD_row_sentence_only/he_htb-sent-{}.txt"
for fn in ["train", "dev", "test"]:
    with open(files_path.format(fn), encoding="utf-8") as f_in:
        lines = [l.strip("# text =") for l in f_in.readlines() if l.startswith("# text =")]
    with open(out_path.format(fn), mode='w', encoding="utf-8") as f_out:
        f_out.writelines(lines)


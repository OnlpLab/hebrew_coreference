# FILE2CHECK = r"C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\crf\outputs\crf\bi_crf\test_predictions.txt"
FILE2CHECK = r"C:\Users\rafael\Desktop\studies\MSC\Theses\np_chunckers\heb_np_chuncker\input\train.txt"
with open(FILE2CHECK, encoding="utf-8") as f:
    lines = f.readlines()
res = []
cur_res = []
for l in lines:
    split_l = l.split(" ")
    if len(split_l) > 2 or len(split_l) == 0:
        raise ValueError("split() have to be in length of 1 or 2.")
    if len(split_l) == 2:
        cur_res.append(split_l[1].strip())
    if len(split_l) == 1:
        res.append(cur_res)
        cur_res = []
last_tag = "O"
for i, sent in enumerate(res):
    for tag in sent:
        if tag == "I-NP" and last_tag == "O":
            raise Exception(f"In sent number {i}\n Test Failed:\n{sent} ")
        last_tag = tag

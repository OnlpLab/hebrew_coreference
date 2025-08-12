import os

output = r"C:\Users\rafael\Desktop\studies\MSC\Theses\Bert NP result\input_no_sep"
base_input = r"C:\Users\rafael\Desktop\studies\MSC\Theses\Bert NP result\input_sep"

for fn in ["dev.txt", "train.txt", "test.txt"]:
    f_path = os.path.join(base_input, fn)
    o_path = os.path.join(output, fn)
    res = []
    with open(f_path, encoding="utf-8") as f:
        lines = f.readlines()
    for line in lines:
        res.append(line.replace("_", ""))
    with open(o_path, mode='w', encoding='utf-8')as f:
        f.writelines(res)

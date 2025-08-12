"Muc7 analysis"
import os
from typing import Dict, List, Any, Union
import spacy
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

def data_analysis_muc(rootdir=r"C:\Users\rafael\Desktop\studies\MSC\Theses\datasets\muc_7\data"):
    print(rootdir)
    num_of_docs: Dict[str, Union[Union[int, List[Any], float], Any]] = {"docs_num": 0, "sent_num": []}
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            filepath = subdir + os.sep + file
            name = set(file.split("."))
            if "keys" not in name:
                continue
            if "muc_7" in rootdir:
                if "co" in name:
                    with open(filepath) as f:
                        txt = "".join(f.readlines())
                else:
                    continue
            else:
                with open(filepath, encoding="ISO-8859-1", errors='ignore') as f:
                    txt = "".join(f.readlines())

            txt_l = txt.split("</DOC>")
            txt_l = [s + '</DOC>' for s in txt_l if s.strip().startswith("<DOC>")]
            num_of_docs["docs_num"] += len(txt_l)
            for t in txt_l:
                soup = BeautifulSoup(t, features="lxml")
                # try:
                num_of_docs["sent_num"].append(
                    len(soup.body.doc.find_all("p")))  # except Exception:  #     print(t)
    num_of_docs["avg_sent_num"] = sum(num_of_docs["sent_num"]) / num_of_docs['docs_num']
    num_of_docs["num of sent"] = sum(num_of_docs["sent_num"])
    for k, v in num_of_docs.items():
        print(f"{k}: {v}")

def data_analysis_wikicoref():
    rootdir = r"C:\Users\rafael\Desktop\studies\MSC\Theses\datasets\WikiCoref\Documents"
    nlp = spacy.load("en_core_web_sm")

    print(rootdir)
    num_of_docs: Dict[str, Union[Union[int, List[Any], float], Any]] = {"docs_num": 0, "sent_num": []}
    for subdir, dirs, files in os.walk(rootdir):
        num_of_docs["docs_num"] = len(files)
        for file in files:
            filepath = subdir + os.sep + file
            with open(filepath) as f:
                txt = "".join(f.readlines())
                sents = [i for i in nlp(txt).sents if len(i) > 5]
                num_of_docs["sent_num"].append(len(sents))
    num_of_docs["avg_sent_num"] = sum(num_of_docs["sent_num"]) / num_of_docs['docs_num']
    num_of_docs["num of sent"] = sum(num_of_docs["sent_num"])
    for k, v in num_of_docs.items():
        print(f"{k}: {v}")


def data_analysis_marmara_turkish():
    rootdir = r"C:\Users\rafael\Desktop\studies\MSC\Theses\datasets\turkish\marmara-turkish-coreference-corpus\gold"

    print(rootdir)
    sents = []
    for subdir, dirs, files in os.walk(rootdir):
        for file in files:
            filepath = subdir + os.sep + file
            tree = ET.parse(filepath)
            root = tree.getroot()
            mentions = list(root)[0]
            sents.append(len(list(mentions)))

    print(sents)
    print(sum(sents))






if __name__ == '__main__':
    # data_analysis_wikicoref()
    data_analysis_marmara_turkish()
    # data_analysis_muc()  # print(num_of_docs)


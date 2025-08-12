from collections import Counter

from split_long_conll_docs import  read_conllu_folder
folder_path = "../corpus/coref_docs_2_tag/tne_conll/"


def main():
    conllu_folder = '../corpus/new_htb_zeldes/htb2_format_with_underscore'
    conllu_docs = read_conllu_folder(conllu_folder)
    pronouns = []
    for idx, doc in conllu_docs.items():
        for sent in doc:
            for token in sent:
                try:
                    if token['upos'] == "PRON":
                        pronouns.append(token['form'])
                except AttributeError as e:
                    print(e)
    pronouns_num = Counter(pronouns)
    for i, (num, tok) in enumerate(pronouns_num.most_common()):
        print(f"{i+1}. {num} : {tok} ")


if __name__ == '__main__':
    main()

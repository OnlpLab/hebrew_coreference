import argparse
import copy
from pathlib import Path
from typing import List

import pandas as pd

from np_chunker import open_web_anno_tsv, AnnotatedSentence


def diff_sents(sent1: AnnotatedSentence, sent2: AnnotatedSentence):
    sent1_ann = set(sent1.annotations)
    sent2_ann = set(sent2.annotations)
    agreed_annotation = sent1_ann & sent2_ann
    not_in_1 = sent2_ann - sent1_ann
    not_in_2 = sent1_ann - sent2_ann
    not_in_1 = [a.text for a in not_in_1]
    not_in_2 = [a.text for a in not_in_2]
    agreed_annotation = [a.text for a in agreed_annotation]

    return agreed_annotation, not_in_1, not_in_2


def fix_annotations(sent):
    fixed_sentences = []
    for s in sent:
        fixed_tokens = []
        fixed_annotations = []
        for token in s.tokens:
            nt = copy.deepcopy(token)
            nt.text = token.text.replace(" ", "")
            fixed_tokens.append(nt)

        for annotation in s.annotations:
            na = copy.deepcopy(annotation)
            na.text = annotation.text.replace(" ", "")
            fixed_annotations.append(na)

        s.tokens = fixed_tokens
        s.annotations = fixed_annotations
        fixed_sentences.append(s)

    return fixed_sentences


def score_files(gold: List[AnnotatedSentence], preds: List[AnnotatedSentence], examples=10):
    all_correct = []
    all_gold_ann = []
    all_pred_ann = []

    # gold = fix_annotations(gold)
    # preds = fix_annotations(preds)
    for sent1, sent2 in zip(gold, preds):
        gold_set, pred_set = set([s.text.replace(" ", "") for  s in sent1.annotations]),\
                             set([s.text.replace(" ", "") for  s in sent2.annotations])
        correct = pred_set & gold_set
        print(f"sentence text: {sent1.text}")
        print(f"FP: {list(pred_set - gold_set)}")
        print(f"FN: {list(gold_set - pred_set)}")
        print("*" * 15)
        all_pred_ann.extend(pred_set)
        all_gold_ann.extend(gold_set)
        all_correct.extend(correct)

    prec = 100 * len(all_correct) / len(all_pred_ann)
    recall = 100 * len(all_correct) / len(all_gold_ann)

    if prec == 0 and recall == 0:
        f1 = 0
    else:
        f1 = 2 * prec * recall / (prec + recall)

    print('Number of gold mentions:', len(all_gold_ann))
    print(f"recall: {round(recall, 2)}")
    print(f"prec: {round(prec, 2)}")
    print(f"f1: {round(f1, 2)}")
    print('FP ex.:', list(set(all_pred_ann) - set(all_gold_ann))[:10])
    print('FN ex.:', list(set(all_gold_ann) - set(all_pred_ann))[:10])

    return prec, recall, f1


def diff_files(file1: List[AnnotatedSentence], file2: List[AnnotatedSentence], fn1: str, fn2: str):
    total_agreed = []
    total_not_in_1 = []
    total_not_in_2 = []
    all_f1_ann = []
    all_f2_ann = []
    summary = []
    for i, (sent1, sent2) in enumerate(zip(file1, file2)):
        all_f1_ann.extend(sent1.annotations)
        all_f2_ann.extend(sent2.annotations)

        agreed_annotation, not_in_1, not_in_2 = diff_sents(sent1, sent2)
        not_in_1 = [""] if len(not_in_1) == 0 else not_in_1
        not_in_2 = [""] if len(not_in_2) == 0 else not_in_2
        agreed_annotation = [""] if len(agreed_annotation) == 0 else agreed_annotation
        total_agreed.extend(agreed_annotation)
        total_not_in_1.extend(not_in_1)
        total_not_in_2.extend(not_in_2)
        print("In sentence:")
        print(sent1.text)
        print("agreed on:")
        print(agreed_annotation)
        print(f"was only in {fn1}:")
        print(not_in_2)
        print(f"was only in {fn2}:")
        print(not_in_1)
        print("*"*30)
        summary.append({"idx": i + 1,
                        "text": sent1.text,
                        "agreed": "\n".join(agreed_annotation),
                        f"only in {fn1} (not in {fn2})": "\n".join(not_in_2),
                        f"only in {fn2} (not in {fn1})": "\n".join(not_in_1)})

    print(f"total agreed: {len(total_agreed)}")
    print(f"total in file 1: {len(all_f1_ann)}")
    print(f"total in file 2: {len(all_f2_ann)}")

    print(f"total only in first: {len(total_not_in_2)}")
    outf = Path(__file__).parent.joinpath("diff_output",f"diff_{fn1}_{fn2}.xlsx")
    print(f"total only in second: {len(total_not_in_1)}")
    print(f"dump summary diff results to: {outf} ")
    pd.DataFrame(summary).to_excel(outf, index=False)
    print("Finish!")



def parse_arguments():
    p = argparse.ArgumentParser(description='diff np chunks')
    p.add_argument('first', help="First webaano tsv file path (gold if score action)")
    p.add_argument('second', help="Second webaano tsv file path (pred if score action)")
    p.add_argument('action', help="could be {diff, score} ")
    return p.parse_args()


def read_files(file1: str, file2: str):
    f1 = list(open_web_anno_tsv(file1))
    f2 = list(open_web_anno_tsv(file2))
    if len(f1) != len(f2):
        raise ValueError(f"files supplied  doesnt contain same number of sentences \n"
                         f"{file1} has {len(f1)}\n"
                         f"{file2} has {len(f2)}\n")
    return f1, f2


def main():
    args = parse_arguments()
    f1, f2 = read_files(args.first, args.second)
    if args.action == "diff":
        fn1 = "gold" #args.first.split("_")[-1].split(".")[0]
        fn2 = args.second.split("_")[-1].split(".")[0]
        diff_files(f1, f2, fn1, fn2)
    elif args.action == "score":
        score_files(f1, f2)


if __name__ == '__main__':
    main()

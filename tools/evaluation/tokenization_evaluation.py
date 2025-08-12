import argparse
import re
from collections import Counter



def eval_segmentation(test_sentences, gold_sentences):
    gold_counts, pred_counts, intersection_counts = 0, 0, 0

    for gold_sent, test_sent in zip(gold_sentences, test_sentences):
        gold_sent = [fix_suffix_sofiot(g) for g in gold_sent]
        test_sent = [fix_suffix_sofiot(t) for t in test_sent]
        gold_count, pred_count = Counter(gold_sent), Counter(test_sent)

        intersection_count = gold_count & pred_count
        gold_counts += sum(gold_count.values())
        pred_counts += sum(pred_count.values())
        intersection_counts += sum(intersection_count.values())

    return gold_counts, pred_counts, intersection_counts


def parse_arguments():
    p = argparse.ArgumentParser(description='diff np chunks')
    p.add_argument('first', help="First webaano tsv file path (gold if score action)")
    p.add_argument('second', help="Second webaano tsv file path (pred if score action)")
    return p.parse_args()

def fix_suffix_sofiot( text):
    text = re.sub(r'נ,', 'ן,',   text)
    text = re.sub(r'מ,', 'ם,',   text)
    text = re.sub(r'כ,', 'ך,',   text)
    text = re.sub(r'פ,', 'ף,',   text)
    text = re.sub(r'צ,', 'ץ,',   text)
    text = re.sub(r'נ\.', 'ן.',   text)
    text = re.sub(r'מ\.', 'ם.',   text)
    text = re.sub(r'כ\.', 'ך.',   text)
    text = re.sub(r'פ\.', 'ף.',   text)
    text = re.sub(r'צ\.', 'ץ.',   text)
    text = re.sub(r'נ ', 'ן ',   text)
    text = re.sub(r'מ ', 'ם ',   text)
    text = re.sub(r'כ ', 'ך ',   text)
    text = re.sub(r'פ ', 'ף ',   text)
    text = re.sub(r'צ ', 'ץ ',   text)
    text = re.sub(r'נ ', 'ן ',   text)
    text = re.sub(r'נ_', 'ן_',   text)
    text = re.sub(r'מ_', 'ם_',   text)
    text = re.sub(r'כ_', 'ך_',   text)
    text = re.sub(r'פ_', 'ף_',   text)
    text = re.sub(r'צ_', 'ץ_',   text)
    text = re.sub(r'נ_', 'ן_',   text)
    return text.strip("_")

def read_files(first, second):
    with open(first, encoding="utf-8") as f:
        f_lines = [l.split() for l in f.readlines()]

    with open(second, encoding="utf-8") as f:
        s_lines = [l.split() for l in f.readlines()]
    return f_lines, s_lines


def main():
    args = parse_arguments()
    f1, f2 = read_files(args.first, args.second)
    gold_counts, pred_counts, intersection_counts = eval_segmentation(f1, f2)
    precision = intersection_counts / pred_counts *100
    recall = intersection_counts / gold_counts * 100

    f1 = (2* precision * recall )/(precision + recall)
    print(f"precision: {precision:.4}")
    print(f"recall: {recall:.4}")
    print(f"f1: {f1:.4}")
if __name__ == '__main__':
    main()

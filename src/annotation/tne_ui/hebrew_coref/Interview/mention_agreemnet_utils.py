from collections import defaultdict
import os
import json
from dataclasses import dataclass
from typing import Dict, List
from coval.eval import evaluator


@dataclass(eq=True, frozen=True)
class Span:
    start_index: int
    end_index: int
    text: str


def process_annotations(annotations: Dict[str, Dict[int, List[Span]]], to_print=False) -> float:
    # get a list of all annotators' names
    annotators = list(annotations.keys())

    total_spans = 0
    agreement_spans = 0

    # iterate over all pairs of annotators
    for i in range(len(annotators)):
        for j in range(i + 1, len(annotators)):
            if j == "gold":
                j = i
                i = "gold"
            annotator1 = annotators[i]
            annotator2 = annotators[j]

            # iterate over all documents
            for doc_id, spans1 in annotations[annotator1].items():
                spans2 = annotations[annotator2].get(doc_id)

                if spans2 is not None:  # if both annotators annotated the same document
                    total_spans += max(len(spans1),
                                       len(spans2))  # consider the maximum number of spans identified by both

                    # calculate number of similar spans
                    agreement_spans += len(set(spans1) & set(spans2))
                    if to_print:
                        print(doc_id)
                        print("Disagreement")
                        print(f"Only in {annotators[i]}:")
                        only_in_i = set(spans1).difference(set(spans2))
                        for span in list(only_in_i):
                            print(span)
                        print(f"Only in {annotators[j]}:")
                        only_in_j = set(spans2).difference(set(spans1))
                        for span in list(only_in_j):
                            print(span)

                    # calculate agreement
    agreement = agreement_spans / total_spans  # it is the ratio of the spans that both annotators agreed upon to the total number of spans
    return agreement


def read_annotation_data(folder_path, specific_files=None, exclude=None):
    if exclude is None:
        exclude = {}
    annotations = {}

    for annotation_name in os.listdir(folder_path):
        if annotation_name in exclude:
            continue
        annotation_dir = os.path.join(folder_path, annotation_name)

        if os.path.isdir(annotation_dir):

            annotations[annotation_name] = {}

            for file_name in os.listdir(annotation_dir):
                hit_id = int(file_name.split(".")[0])
                if specific_files and hit_id not in specific_files:
                    continue
                file_path = os.path.join(annotation_dir, file_name)

                if file_name.endswith(".json"):
                    with open(file_path, 'r') as file:
                        data = json.load(file)

                        spans = data.get("clusters", [])

                        valid_spans = set([span["members"][0] for span in spans if
                                           span.get("source") == "mention" or span.get("source")[0] == "mention"])
                        nps = data.get("nps", [])

                        annotated_spans = [(Span(np["start_index"], np["end_index"], np['text'])) for np in nps if
                                           np['id'] in valid_spans]

                        annotations[annotation_name][hit_id] = annotated_spans

    return annotations

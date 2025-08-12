import os
from coval.conll import reader
from coval.eval import evaluator


def run_agreement(gold_file, sys_file, metrics, keep_singletons):
    metric_options = {"muc", "bcub", "ceafe", "lea"}
    doc_coref_infos = reader.get_coref_infos(gold_file, sys_file, keep_singletons=keep_singletons,
                                             NP_only=False,
                                             remove_nested=False,
                                             min_span=False)

    conll = 0
    conll_subparts_num = 0
    metrics_result = {}
    for name, metric in metrics:
        recall, precision, f1 = evaluator.evaluate_documents(doc_coref_infos,
                                                             metric,
                                                             beta=1)
        metrics_result[name] = {"recall": recall, "precision": precision, "f1": f1}
        if name in metric_options:
            conll += f1
            conll_subparts_num += 1

        print(name.ljust(10), 'Recall: %.2f' % (recall * 100),
              ' Precision: %.2f' % (precision * 100),
              ' F1: %.2f' % (f1 * 100))

    if conll_subparts_num == 4:
        conll_score = (conll / 4) * 100
        print('CoNLL score: %.2f' % conll_score)
        metrics_result['conll_score'] = conll_score
    return metrics_result


def run_2_annotators_agreement(gold_files, sys_files, keep_singletons=True):
    allmetrics = [('mentions', evaluator.mentions),
                  ('muc', evaluator.muc),
                  ('bcub', evaluator.b_cubed),
                  ('ceafe', evaluator.ceafe),
                  ('lea', evaluator.lea)]
    results = []
    for gold_file, sys_file in zip(gold_files, sys_files):
        res = run_agreement(gold_file, sys_file, allmetrics, keep_singletons)
        results.append(res)
    return results


def extract_name(file_name):
    parts = file_name.split('_')
    name = '_'.join(parts[-1:])
    name = name.replace('.conllu', '')
    return name


def calculate_average_scores(metrics_list, include_mentions):
    # initialize the dictionary to store the total scores and counts for each metric
    total_scores = {
        'mentions': {'recall': 0, 'precision': 0, 'f1': 0},
        'muc': {'recall': 0, 'precision': 0, 'f1': 0},
        'bcub': {'recall': 0, 'precision': 0, 'f1': 0},
        'ceafe': {'recall': 0, 'precision': 0, 'f1': 0},
        'lea': {'recall': 0, 'precision': 0, 'f1': 0},
    }
    counts = {
        'mentions': 0,
        'muc': 0,
        'bcub': 0,
        'ceafe': 0,
        'lea': 0,
    }
    if not include_mentions:
        total_scores.pop('mentions')
        counts.pop('mentions')
        for user_metrics in metrics_list:
            user_metrics.pop('mentions')
    # iterate over the list of dictionaries and add up the scores and counts for each
    for metrics_dict in metrics_list:
        for metric_name, metric_scores in metrics_dict.items():
            if metric_name != 'conll_score':
                for score_name, score_value in metric_scores.items():
                    total_scores[metric_name][score_name] += score_value
                counts[metric_name] += 1

    # calculate the average scores for each metric
    for metric_name, metric_scores in total_scores.items():

        for score_name, score_value in metric_scores.items():
            total_scores[metric_name][score_name] = score_value / counts[metric_name]

    return total_scores


def two_annotators_agreement(name1, name2, keep_singletons, include_mentions, file_by_annotator,
                             conllu_annotated_files_path):
    annotator_1 = {f.split("_")[0]: f for f in file_by_annotator[name1]}
    annotator_2 = {f.split("_")[0]: f for f in file_by_annotator[name2]}
    a1_f = []
    a2_f = []

    for key, a1_file in annotator_1.items():
        if key in annotator_2:
            a1_f.append(os.path.join(conllu_annotated_files_path, a1_file))
            a2_f.append(os.path.join(conllu_annotated_files_path, annotator_2[key]))
    agreement = run_2_annotators_agreement(a1_f, a2_f, keep_singletons)
    return calculate_average_scores(agreement, include_mentions=include_mentions)


def n_annotators_agreement(annotator_names, keep_singletons, include_mentions, file_by_annotator,
                           conllu_annotated_files_path):
    print(f"keep_singletons: {keep_singletons} ")
    print(f"include_mentions: {include_mentions} ")
    annotator_files = {}
    for name in annotator_names:
        annotator_files[name] = {f.split("_")[0]: f for f in file_by_annotator[name]}
    print(f"Check agreement for {len(annotator_files)} files")
    file_couples = []
    for i, name1 in enumerate(annotator_names):
        for j, name2 in enumerate(annotator_names[i + 1:], i + 1):

            a1_f = []
            a2_f = []

            for key, a1_file in annotator_files[name1].items():
                if key in annotator_files[name2]:
                    a1_f.append(os.path.join(conllu_annotated_files_path, a1_file))
                    a2_f.append(os.path.join(conllu_annotated_files_path, annotator_files[name2][key]))

            file_couples.append((a1_f, a2_f))
            print("name1: ", name1)
            print("name2: ", name2)
            print(f"Number of file coules: {len(a1_f)}")

    agreement_scores = []
    for a1_f, a2_f in file_couples:
        agreement_scores.append(
            calculate_average_scores(run_2_annotators_agreement(a1_f, a2_f, keep_singletons), include_mentions))

    # return calculate_average_scores(agreement_scores)
    return agreement_scores

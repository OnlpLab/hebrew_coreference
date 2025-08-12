import argparse
import json
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
print('[DEBUG] sys.path:', sys.path)

import jsonlines
import torch
from tqdm import tqdm

from coref import CorefModel
from coref.tokenizer_customization import *

def write_json(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def build_doc(doc: dict, model: CorefModel) -> dict:
    filter_func = TOKENIZER_FILTERS.get(model.config.bert_model,
                                        lambda _: True)
    token_map = TOKENIZER_MAPS.get(model.config.bert_model, {})

    word2subword = []
    subwords = []
    word_id = []
    for i, word in enumerate(doc["cased_words"]):
        tokenized_word = (token_map[word]
                          if word in token_map
                          else model.tokenizer.tokenize(word))
        tokenized_word = list(filter(filter_func, tokenized_word))
        word2subword.append((len(subwords), len(subwords) + len(tokenized_word)))
        subwords.extend(tokenized_word)
        word_id.extend([i] * len(tokenized_word))
    doc["word2subword"] = word2subword
    doc["subwords"] = subwords
    doc["word_id"] = word_id

    doc["head2span"] = []
    if "speaker" not in doc:
        doc["speaker"] = ["_" for _ in doc["cased_words"]]
    doc["word_clusters"] = []
    doc["span_clusters"] = []

    return doc


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("[START] wl-coref predict.py main entry point.")
        argparser = argparse.ArgumentParser()
        argparser.add_argument("experiment")
        argparser.add_argument("input_file")
        argparser.add_argument("output_file")
        argparser.add_argument("--config-file", default="config.toml")
        argparser.add_argument("--batch-size", type=int,
                               help="Adjust to override the config value if you're"
                                    " experiencing out-of-memory issues")
        argparser.add_argument("--weights",
                               help="Path to file with weights to load."
                                    " If not supplied, in the latest"
                                    " weights of the experiment will be loaded;"
                                    " if there aren't any, an error is raised.")
        argparser.add_argument("--output-dir", default=None, help="Directory to load best model weights for this run. If not given, uses --weights or latest in data_dir.")
        argparser.add_argument("--eval-compatible-output", default=None, help="Optional: path to write output compatible with src/evaluate.py.")
        argparser.add_argument("--data-dir", default=None, help="Override data_dir in config.toml for this run (where weights are loaded from).")
        argparser.add_argument("--conll-log-dir", default=None, help="Override conll_log_dir in config.toml for this run (where conll logs are saved).")
        args = argparser.parse_args()

        model = CorefModel(args.config_file, args.experiment, build_optimizers=False)
        if args.data_dir is not None:
            model.config.data_dir = args.data_dir
        if args.conll_log_dir is not None:
            model.config.conll_log_dir = args.conll_log_dir

        if args.batch_size:
            model.config.a_scoring_batch_size = args.batch_size

        # Determine weights path
        weights_path = args.weights
        if weights_path is None and args.output_dir is not None:
            weights_path = os.path.join(args.output_dir, "model_best.pt")
        # If still None, will fall back to default logic in load_weights
        model.load_weights(path=weights_path, map_location="cpu",
                           ignore={"bert_optimizer", "general_optimizer",
                                   "bert_scheduler", "general_scheduler"})
        model.training = False

        with jsonlines.open(args.input_file, mode="r") as input_data:
            docs = [build_doc(doc, model) for doc in input_data]

        with torch.no_grad():
            for doc in tqdm(docs, unit="docs"):
                result = model.run(doc)
                doc["span_clusters"] = result.span_clusters
                doc["word_clusters"] = result.word_clusters

                for key in ("word2subword", "subwords", "word_id", "head2span"):
                    del doc[key]

        with jsonlines.open(args.output_file, mode="w") as output_data:
            output_data.write_all(docs)

        if args.eval_compatible_output is not None:
            # Load original test data to get gold clusters
            gold_data = {}
            with jsonlines.open(args.input_file, mode="r") as input_data:
                for doc in input_data:
                    gold_data[doc.get("document_id", "")] = doc.get("span_clusters", [])
            
            eval_docs = []
            for doc in docs:
                doc_key = doc.get("document_id", "")
                eval_doc = {
                    "doc_key": doc_key,
                    "predicted_clusters": doc.get("span_clusters", []),
                    "gold_clusters": gold_data.get(doc_key, [])
                }
                eval_docs.append(eval_doc)
            write_json(eval_docs, args.eval_compatible_output)
        logger.info("[SUCCESS] wl-coref predict.py completed successfully.")
    except Exception as e:
        logger.error(f"[ERROR] Exception in wl-coref predict.py: {e}", exc_info=True)
        print(f"[ERROR] Exception in wl-coref predict.py: {e}", file=sys.stderr)
        raise

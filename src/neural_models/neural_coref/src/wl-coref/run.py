""" Runs experiments with CorefModel.

Try 'python run.py -h' for more details.
"""

import argparse
from contextlib import contextmanager
import datetime
import random
import sys
import time
import os
import shutil

import numpy as np  # type: ignore
import torch        # type: ignore
import logging

from coref import CorefModel


@contextmanager
def output_running_time():
    """ Prints the time elapsed in the context """
    start = int(time.time())
    try:
        yield
    finally:
        end = int(time.time())
        delta = datetime.timedelta(seconds=end - start)
        print(f"Total running time: {delta}")


def seed(value: int) -> None:
    """ Seed random number generators to get reproducible results """
    random.seed(value)
    np.random.seed(value)
    torch.manual_seed(value)
    torch.cuda.manual_seed_all(value)           # type: ignore
    torch.backends.cudnn.deterministic = True   # type: ignore
    torch.backends.cudnn.benchmark = False      # type: ignore


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
                        datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("[START] wl-coref main entry point.")
        argparser = argparse.ArgumentParser()
        argparser.add_argument("mode", choices=("train", "eval"))
        argparser.add_argument("experiment")
        argparser.add_argument("--config-file", default="config.toml")
        argparser.add_argument("--data-split", choices=("train", "dev", "test"),
                               default="test",
                               help="Data split to be used for evaluation."
                                    " Defaults to 'test'."
                                    " Ignored in 'train' mode.")
        argparser.add_argument("--batch-size", type=int,
                               help="Adjust to override the config value if you're"
                                    " experiencing out-of-memory issues")
        argparser.add_argument("--warm-start", action="store_true",
                               help="If set, the training will resume from the"
                                    " last checkpoint saved if any. Ignored in"
                                    " evaluation modes."
                                    " Incompatible with '--weights'.")
        argparser.add_argument("--weights",
                               help="Path to file with weights to load."
                                    " If not supplied, in 'eval' mode the latest"
                                    " weights of the experiment will be loaded;"
                                    " in 'train' mode no weights will be loaded.")
        argparser.add_argument("--word-level", action="store_true",
                               help="If set, output word-level conll-formatted"
                                    " files in evaluation modes. Ignored in"
                                    " 'train' mode.")
        argparser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
        argparser.add_argument("--output-dir", default=None, help="Directory to save/load best model weights for this run.")
        argparser.add_argument("--data-dir", default=None, help="Override data_dir in config.toml for this run (where weights are saved).")
        argparser.add_argument("--conll-log-dir", default=None, help="Override conll_log_dir in config.toml for this run (where conll logs are saved).")
        args = argparser.parse_args()

        if args.warm_start and args.weights is not None:
            logger.error("[ERROR] The following options are incompatible: '--warm_start' and '--weights'")
            print("The following options are incompatible: '--warm_start' and '--weights'", file=sys.stderr)
            sys.exit(1)

        seed(args.seed)
        model = CorefModel(args.config_file, args.experiment)
        if args.data_dir is not None:
            model.config.data_dir = args.data_dir
        if args.conll_log_dir is not None:
            model.config.conll_log_dir = args.conll_log_dir

        if args.batch_size:
            model.config.a_scoring_batch_size = args.batch_size

        if args.mode == "train":
            best_f1 = -1.0
            best_epoch = -1
            model.train()
            # After training, find latest weights and copy to output_dir/model_best.pt
            import glob
            section = args.experiment
            data_dir = model.config.data_dir
            print("globb pattern", os.path.join(data_dir, f"{section}_(e*_*.pt"))
            pattern = os.path.join(data_dir, f"{section}_(e*_*.pt")
            candidates = glob.glob(pattern)
            if not candidates:
                logger.error(f"[ERROR] No weights found in {data_dir} after training!")
                raise FileNotFoundError(f"No weights found in {data_dir} after training!")
            latest = max(candidates, key=os.path.getmtime)
            if args.output_dir is not None:
                os.makedirs(args.output_dir, exist_ok=True)
                best_path = os.path.join(args.output_dir, "model_best.pt")
                shutil.copy2(latest, best_path)
                logger.info(f"[INFO] Copied best weights to {best_path}")
            else:
                best_path = latest
            logger.info("[INFO] Loading best model for test evaluation...")
            model.load_weights(path=best_path, map_location="cpu",
                               ignore={"bert_optimizer", "general_optimizer",
                                       "bert_scheduler", "general_scheduler"})
            logger.info("[INFO] Evaluating on test set with best model...")
            model.evaluate(data_split="test", word_level_conll=args.word_level)
            logger.info("[SUCCESS] Test evaluation with best model complete.")
        else:
            model.load_weights(path=args.weights, map_location="cpu",
                               ignore={"bert_optimizer", "general_optimizer",
                                       "bert_scheduler", "general_scheduler"})
            model.evaluate(data_split=args.data_split,
                           word_level_conll=args.word_level)
        logger.info("[SUCCESS] wl-coref run.py completed successfully.")
    except Exception as e:
        logger.error(f"[ERROR] Exception in wl-coref run.py: {e}", exc_info=True)
        print(f"[ERROR] Exception in wl-coref run.py: {e}", file=sys.stderr)
        raise

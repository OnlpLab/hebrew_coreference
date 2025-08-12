import os
os.environ["WANDB_MODE"] = "offline"

import logging
import shutil
import pprint
import coref_dataset
import torch
from transformers import AutoConfig, AutoTokenizer

from consts import SUPPORTED_MODELS
from modeling_lingmess import LingMessCoref as coref_model_lingmess
from training import train
from eval import Evaluator
from util import set_seed
from cli import parse_args
from collate import LongformerCollator, DynamicBatchSampler, SegmentCollator
import wandb
# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt='%m/%d/%Y %H:%M:%S', level=logging.INFO)


def main():
    args = parse_args()

    # Always use lingmess logic
    if args.experiment_name is None:
        args.experiment_name = "lingmess_experiment"
    if args.output_dir is not None:
        if os.path.exists(args.output_dir):
            if args.overwrite_output_dir:
                shutil.rmtree(args.output_dir)
                logger.info(f'--overwrite_output_dir used. directory {args.output_dir} deleted!')
            else:
                raise ValueError(f"Output directory ({args.output_dir}) already exists. Use --overwrite_output_dir to overcome.")
        os.mkdir(args.output_dir)
    else:
        if args.do_train:
            raise ValueError(f"Output directory is required while do_train=True.")
        else:
            if args.output_file is None:
                raise ValueError(f"Output directory or output file is required.")

    # Setup CUDA, GPU & distributed training
    # Setup CUDA, MPS, GPU & distributed training
    if args.device.startswith("cuda") and torch.cuda.is_available():
        device = torch.device(args.device if args.device.startswith("cuda") else "cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")
    args.device = device
    print(f"Using device: {args.device}")
    if not (torch.cuda.is_available() or str(args.device).startswith("cuda") or str(args.device).startswith("mps")):
        raise RuntimeError(
            "CUDA or MPS is not available, or the device is not set correctly. Please run with --device cuda:0 or --device mps and ensure the appropriate hardware is available.")
    args.n_gpu = 1 if str(args.device).startswith("cuda") else 0
    set_seed(args)

    config = AutoConfig.from_pretrained(args.model_name_or_path, cache_dir=args.cache_dir)
    config.coref_head = {
        "max_span_length": args.max_span_length,
        "top_lambda": args.top_lambda,
        "ffnn_size": args.ffnn_size,
        "dropout_prob": args.dropout_prob,
        "max_segment_len": args.max_segment_len,
        "max_doc_len": 4096
    }

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, use_fast=True,
                                              add_prefix_space=True, cache_dir=args.cache_dir)
    # Always use lingmess-coref
    model, loading_info = coref_model_lingmess.from_pretrained(
        args.model_name_or_path, output_loading_info=True,
        config=config, cache_dir=args.cache_dir
    )

    if model.base_model_prefix not in SUPPORTED_MODELS:
        raise NotImplementedError(f'Model not supporting {args.model_type}, choose one of {SUPPORTED_MODELS}')
    args.base_model = model.base_model_prefix

    # Check model parameters before moving to device
    logger.info("Checking model parameters before device transfer...")
    nan_params_before = []
    for name, param in model.named_parameters():
        if torch.isnan(param).any():
            nan_params_before.append(name)
    
    if nan_params_before:
        logger.error(f"ERROR: Found {len(nan_params_before)} parameters with NaN before device transfer!")
        logger.error(f"First 10 NaN parameters: {nan_params_before[:10]}")
        raise RuntimeError("Model parameters contain NaN values before device transfer")
    else:
        logger.info("✓ All model parameters are valid before device transfer")

    model.to(args.device)
    
    # Check model parameters after moving to device
    logger.info("Checking model parameters after device transfer...")
    nan_params_after = []
    for name, param in model.named_parameters():
        if torch.isnan(param).any():
            nan_params_after.append(name)
    
    if nan_params_after:
        logger.error(f"ERROR: Found {len(nan_params_after)} parameters with NaN after device transfer!")
        logger.error(f"First 10 NaN parameters: {nan_params_after[:10]}")
        raise RuntimeError("Model parameters contain NaN values after device transfer")
    else:
        logger.info("✓ All model parameters are valid after device transfer")
    
    for key, val in loading_info.items():
        logger.info(f'{key}: {val}')

    t_params, h_params = [p / 1000000 for p in model.num_parameters()]
    logger.info(f'Parameters: {t_params + h_params:.1f}M, Transformer: {t_params:.1f}M, Head: {h_params:.1f}M')

    # load datasets
    dataset, dataset_files = coref_dataset.create(
        tokenizer=tokenizer,
        train_file=args.train_file, dev_file=args.dev_file, test_file=args.test_file,
        cache_dir=args.cache_dir
    )
    args.dataset_files = dataset_files
    print(args.base_model)
    if args.base_model == 'longformer':
        collator = LongformerCollator(tokenizer=tokenizer, device=args.device)
        max_doc_len = 4096
    else:
        collator = SegmentCollator(tokenizer=tokenizer, device=args.device, max_segment_len=args.max_segment_len)
        max_doc_len = None

    eval_dataloader = DynamicBatchSampler(
        dataset[args.eval_split],
        collator=collator,
        max_tokens=args.max_tokens_in_batch,
        max_segment_len=args.max_segment_len,
        max_doc_len=max_doc_len
    )
    evaluator = Evaluator(args=args, eval_dataloader=eval_dataloader)

    # Training
    if args.do_train:
        # Initialize wandb for training
        wandb.init(
            project="lingmess-coref",
            name=f"{args.model_name_or_path}_seed{args.seed}",
            config=vars(args),
            mode="offline"
        )
        
        train_sampler = DynamicBatchSampler(
            dataset['train'],
            collator=collator,
            max_tokens=args.max_tokens_in_batch,
            max_segment_len=args.max_segment_len,
            max_doc_len=max_doc_len
        )
        train_batches = coref_dataset.create_batches(sampler=train_sampler).shuffle(seed=args.seed)
        logger.info(train_batches)

        global_step, tr_loss = train(args, train_batches, model, tokenizer, evaluator)
        logger.info(f"global_step = {global_step}, average loss = {tr_loss}")
        
        # Finish wandb run only if we initialized it
        try:
            wandb.finish()
        except Exception as e:
            logger.warning(f"Warning: Could not finish wandb run: {e}")

    # Evaluation
    results = evaluator.evaluate(model)
    results_path = os.path.join(os.path.dirname(args.output_file), f"result_{args.eval_split}.json")
    with open(results_path, "w") as f:
        f.write(pprint.pformat(results))
    print(results)

    return results


if __name__ == "__main__":
    try:
        logger.info("[START] lingmess-coref main entry point.")
        main()
        logger.info("[SUCCESS] lingmess-coref run.py completed successfully.")
    except Exception as e:
        logger.error(f"[ERROR] Exception in lingmess-coref run.py: {e}", exc_info=True)
        raise

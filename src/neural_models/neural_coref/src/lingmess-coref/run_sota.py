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

def parse_args():
    """Parse command line arguments for SOTA evaluation."""
    import argparse
    parser = argparse.ArgumentParser()
    
    # Model arguments
    parser.add_argument('--model_name_or_path', type=str, required=True)
    parser.add_argument('--output_dir', type=str, default=None)
    parser.add_argument('--output_file', type=str, default=None)
    
    # Data arguments
    parser.add_argument('--train_file', type=str, default=None)
    parser.add_argument('--dev_file', type=str, default=None)
    parser.add_argument('--test_file', type=str, required=True)
    
    # Evaluation arguments
    parser.add_argument('--eval_split', type=str, default='test')
    parser.add_argument('--device', type=str, default='cpu')
    parser.add_argument('--seed', type=int, default=42)
    
    # Model configuration
    parser.add_argument('--max_span_length', type=int, default=30)
    parser.add_argument('--top_lambda', type=float, default=0.4)
    parser.add_argument('--ffnn_size', type=int, default=1000)
    parser.add_argument('--dropout_prob', type=float, default=0.3)
    parser.add_argument('--max_segment_len', type=int, default=512)
    parser.add_argument('--max_tokens_in_batch', type=int, default=4096)
    
    # Training arguments (not used for evaluation)
    parser.add_argument('--do_train', action='store_true', default=False)
    parser.add_argument('--overwrite_output_dir', action='store_true', default=False)
    parser.add_argument('--experiment_name', type=str, default=None)
    
    # Cache arguments
    parser.add_argument('--cache_dir', type=str, default='cache')
    
    return parser.parse_args()

def main():
    args = parse_args()

    # Always use lingmess logic
    if args.experiment_name is None:
        args.experiment_name = "lingmess_sota_experiment"
    
    # Handle output directory
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

    # Setup device
    if torch.cuda.is_available():
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

    # Load model configuration and tokenizer
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
    
    # Load the trained model
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

    # Load datasets using SOTA processing
    dataset, dataset_files = coref_dataset.create_sota(
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

    # Training (if requested)
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
        except:
            pass

    # Evaluation
    logger.info("Running evaluation...")
    results = evaluator.evaluate(model, tokenizer)
    
    # Save results
    if args.output_file:
        import json
        with open(args.output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Results saved to {args.output_file}")
    
    # Print results
    for metric, value in results.items():
        logger.info(f"{metric}: {value}")

if __name__ == '__main__':
    main() 
import json
import os
import logging
import torch
from tqdm import tqdm
from transformers import AdamW, get_linear_schedule_with_warmup
from util import save_all
import wandb

logger = logging.getLogger(__name__)


def train(args, train_batches, model, tokenizer, evaluator):
    """ Train the model """
    print(f"The device used is: {args.device}")
    device = torch.device(args.device)
    model.to(device)

    t_total = len(train_batches) * args.train_epochs

    # Prepare optimizer and schedule (linear warmup and decay)
    no_decay = ['bias', 'LayerNorm.weight']
    head_params = ['coref', 'mention', 'antecedent']

    model_decay = [p for n, p in model.named_parameters() if
                   not any(hp in n for hp in head_params) and not any(nd in n for nd in no_decay)]
    model_no_decay = [p for n, p in model.named_parameters() if
                      not any(hp in n for hp in head_params) and any(nd in n for nd in no_decay)]
    head_decay = [p for n, p in model.named_parameters() if
                  any(hp in n for hp in head_params) and not any(nd in n for nd in no_decay)]
    head_no_decay = [p for n, p in model.named_parameters() if
                     any(hp in n for hp in head_params) and any(nd in n for nd in no_decay)]

    head_learning_rate = args.head_learning_rate if args.head_learning_rate else args.learning_rate
    optimizer_grouped_parameters = [
        {'params': model_decay, 'lr': args.learning_rate, 'weight_decay': args.weight_decay},
        {'params': model_no_decay, 'lr': args.learning_rate, 'weight_decay': 0.0},
        {'params': head_decay, 'lr': head_learning_rate, 'weight_decay': args.weight_decay},
        {'params': head_no_decay, 'lr': head_learning_rate, 'weight_decay': 0.0}
    ]
    optimizer = AdamW(optimizer_grouped_parameters,
                      lr=args.learning_rate,
                      betas=(args.adam_beta1, args.adam_beta2),
                      eps=args.adam_epsilon)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=t_total * 0.1, num_training_steps=t_total)

    # using mixed precision
    scaler = torch.cuda.amp.GradScaler()
    logger.info("Mixed precision enabled for faster training")

    # Train!
    logger.info("***** Running training *****")
    logger.info("  Num Epochs = %d", args.train_epochs)
    logger.info("  Total optimization steps = %d", t_total)

    global_step, tr_loss, logging_loss = 0, 0.0, 0.0
    best_f1, best_global_step = -1, -1

    train_iterator = tqdm(range(int(args.train_epochs)), desc="Epoch")
    #Make sure out path exists before start training
    os.makedirs(args.output_dir, exist_ok=True)
    for _ in train_iterator:
        epoch_iterator = tqdm(train_batches, desc="Iteration")
        for step, batch in enumerate(epoch_iterator):
            batch['input_ids'] = torch.tensor(batch['input_ids'], device=device)
            batch['attention_mask'] = torch.tensor(batch['attention_mask'], device=device)
            batch['gold_clusters'] = torch.tensor(batch['gold_clusters'], device=device)
            if 'leftovers' in batch:
                batch['leftovers']['input_ids'] = torch.tensor(batch['leftovers']['input_ids'], device=device)
                batch['leftovers']['attention_mask'] = torch.tensor(batch['leftovers']['attention_mask'], device=device)

            model.zero_grad()
            model.train()

            with torch.cuda.amp.autocast():
                outputs = model(batch, gold_clusters=batch['gold_clusters'], return_all_outputs=False)

            loss = outputs[0]  # model outputs are always tuple in transformers (see doc)

            # Debug: Check what the model is outputting
            if global_step < 5:  # Only debug first few steps
                logger.info(f"Step {global_step}: outputs type: {type(outputs)}, length: {len(outputs)}")
                logger.info(f"Step {global_step}: loss type: {type(loss)}, value: {loss}")

            tr_loss += loss.item()
            if scaler is not None:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            scheduler.step()        # Update learning rate schedule
            if scaler is not None:
                scaler.step(optimizer)
                scaler.update()         # Updates the scale for next iteration
            else:
                optimizer.step()
            global_step += 1

            # Log metrics
            if global_step % args.logging_steps == 0:
                loss = (tr_loss - logging_loss) / args.logging_steps
                logger.info(f"\nloss step {global_step}: {loss}")
                try:
                    wandb.log({'loss': loss}, step=global_step)
                except Exception as e:
                    logger.warning(f"Warning: Could not log to wandb: {e}")
                logging_loss = tr_loss

            # Evaluation

            if global_step % args.eval_steps == 0:
                results = evaluator.evaluate(model, prefix=f'step_{global_step}')
                try:
                    wandb.log(results, step=global_step)
                except Exception as e:
                    logger.warning(f"Warning: Could not log evaluation results to wandb: {e}")

                f1 = results["f1"]
                if f1 > best_f1:
                    best_f1, best_global_step = f1, global_step
                    try:
                        wandb.run.summary["best_f1"] = best_f1
                    except Exception as e:
                        logger.warning(f"Warning: Could not update wandb summary: {e}")
                    # Save model
                    output_dir = os.path.join(args.output_dir, "model")
                    os.makedirs(output_dir, exist_ok=True)
                    model.save_pretrained(output_dir)
                    tokenizer.save_pretrained(output_dir)
                    logger.info(f"Saved best model to {output_dir}")
                logger.info(f"best f1 is {best_f1} on global step {best_global_step}")

    # Save best f1
    with open(os.path.join(args.output_dir, f"best_f1.json"), "w") as f:
        json.dump({"best_f1": best_f1, "best_global_step": best_global_step}, f)

    return global_step, tr_loss / global_step




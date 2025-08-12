## Word-Level Coreference Resolution

This is a repository with the code to reproduce the experiments described in the paper of the same name, which was accepted to EMNLP 2021. The paper is available [here](https://aclanthology.org/2021.emnlp-main.605/).

### Table of contents
1. [Preparation](#preparation)
2. [Training](#training)
3. [Evaluation](#evaluation)
5. [Prediction](#prediction)
6. [Citation](#citation)

### Preparation

The following instruction has been tested with Python 3.7 on an Ubuntu 20.04 machine.

You will need:
* **OntoNotes 5.0 corpus** (download [here](https://catalog.ldc.upenn.edu/LDC2013T19), registration needed)
* **Python 2.7** to run conll-2012 scripts
* **Java runtime** to run [Stanford Parser](https://nlp.stanford.edu/software/lex-parser.shtml)
* **Python 3.7+** to run the model
* **Perl** to run conll-2012 evaluation scripts
* **CUDA**-enabled machine (48 GB to train, 4 GB to evaluate)

1. Extract OntoNotes 5.0 arhive. In case it's in the repo's root directory:

        tar -xzvf ontonotes-release-5.0_LDC2013T19.tgz
2. Switch to Python 2.7 environment (where `python` would run 2.7 version). This is necessary for conll scripts to run correctly. To do it with with conda:

        conda create -y --name py27 python=2.7 && conda activate py27
3. Run the conll data preparation scripts (~30min):

        sh get_conll_data.sh ontonotes-release-5.0 data
4. Download conll scorers and Stanford Parser:

        sh get_third_party.sh
5. Prepare your environment. To do it with conda:

        conda create -y --name wl-coref python=3.7 openjdk perl
        conda activate wl-coref
        python -m pip install -r requirements.txt
6. Build the corpus in jsonlines format (~20 min):

        python convert_to_jsonlines.py data/conll-2012/ --out-dir data
        python convert_to_heads.py

You're all set!

### Training

If you have completed all the steps in the previous section, then just run:

    python run.py train roberta

Use `-h` flag for more parameters and `CUDA_VISIBLE_DEVICES` environment variable to limit the cuda devices visible to the script. Refer to `config.toml` to modify existing model configurations or create your own.

**Note:** By default, all model weights and logs are now saved under `../results/wlcoref` (see `data_dir` and `conll_log_dir` in `config.toml`). You can change these paths in the config if needed.

### Evaluation

Make sure that you have successfully completed all steps of the [Preparation](#preparation) section.

1. [Download](https://www.dropbox.com/s/vf7zadyksgj40zu/roberta_%28e20_2021.05.02_01.16%29_release.pt?dl=0) and save the pretrained model to the `data` directory.

        https://www.dropbox.com/s/vf7zadyksgj40zu/roberta_%28e20_2021.05.02_01.16%29_release.pt?dl=0

2. Generate the conll-formatted output:

        python run.py eval roberta --data-split test

3. Run the conll-2012 scripts to obtain the metrics:

        python calculate_conll.py roberta test 20

### Prediction

To predict coreference relations on an arbitrary text, you will need to prepare the data in the jsonlines format (one json-formatted document per line).
The following fields are requred:

        {
                "document_id": "tc_mydoc_001",
                "cased_words": ["Hi", "!", "Bye", "."],
                "sent_id": [0, 0, 1, 1]
        }

You can optionally provide the speaker data:

        {
                "speaker": ["Tom", "Tom", "#2", "#2"]
        }

`document_id` can be any string that starts with a two-letter genre identifier. The genres recognized are the following:
* bc: broadcast conversation
* bn: broadcast news
* mz: magazine genre (Sinorama magazine)
* nw: newswire genre
* pt: pivot text (The Bible)
* tc: telephone conversation (CallHome corpus)
* wb: web data

You can check [a sample input file](sample_input.jsonlines) for reference.

Then run:

        python predict.py roberta input.jsonlines output.jsonlines

This will utilize the latest weights available in the data directory for the chosen configuration. To load other weights, use the `--weights` argument.

## Unified Model Weight Management

Both `run.py` (training/evaluation) and `predict.py` now support a `--output-dir` argument:

- When training with `run.py`, after training, the latest weights are copied to `<output_dir>/model_best.pt`.
- When evaluating or predicting, if `--output-dir` is provided (and `--weights` is not), the model will be loaded from `<output_dir>/model_best.pt`.
- This ensures a standardized, plug-and-play workflow for running, saving, and reusing the best model across experiments.

### Example: Training and Evaluation

```bash
python run.py train hebrew_aleph --output-dir ../results/wlcoref/hebrew_aleph_seed42_model
# After training, the best model is at ../results/wlcoref/hebrew_aleph_seed42_model/model_best.pt
python run.py eval hebrew_aleph --output-dir ../results/wlcoref/hebrew_aleph_seed42_model --data-split test
```

### Example: Prediction

```bash
python predict.py hebrew_aleph input.jsonlines output.jsonlines --output-dir ../results/wlcoref/hebrew_aleph_seed42_model
```

- You can still use `--weights` to specify a custom weights file directly. If neither `--output-dir` nor `--weights` is given, the latest weights in the configured data_dir will be used.

## Output Directory Customization

Both `run.py` and `predict.py` now support `--data-dir` and `--conll-log-dir` arguments:

- `--data-dir` overrides the `data_dir` in `config.toml` for saving/loading model weights.
- `--conll-log-dir` overrides the `conll_log_dir` in `config.toml` for saving conll logs.
- This allows you to keep each experiment (e.g., each seed) in its own directory:

```bash
python run.py train hebrew_aleph --seed 42 \
  --data-dir ../results/wlcoref/hebrew_aleph_seed42 \
  --conll-log-dir ../results/wlcoref/hebrew_aleph_seed42/conll_logs \
  --output-dir ../results/wlcoref/hebrew_aleph_seed42
```

- The same applies to `predict.py` for loading weights and saving logs.

### Citation
    @inproceedings{dobrovolskii-2021-word,
    title = "Word-Level Coreference Resolution",
    author = "Dobrovolskii, Vladimir",
    booktitle = "Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing",
    month = nov,
    year = "2021",
    address = "Online and Punta Cana, Dominican Republic",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.emnlp-main.605",
    pages = "7670--7675"}

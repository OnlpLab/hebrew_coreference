# Project Structure

This document describes the clean, organized structure of the Hebrew Coreference Resolution System.

## Root Directory

```
hebrew-coref-system/
├── main.py                    # Main entry point
├── config.py                  # Configuration management
├── setup.py                   # Package setup
├── requirements.txt           # Dependencies
├── README.md                  # Main documentation
├── .gitignore                 # Git ignore rules
├── docs/                      # Documentation
├── src/                       # Source code
├── data/                      # Data files
├── outputs/                   # Output files
├── tools/                     # Utility tools
├── examples/                  # Example scripts
├── tests/                     # Test files
└── scripts/                   # Scripts
```

## Source Code (`src/`)

```
src/
├── mention_detection/         # Mention detection components
│   ├── np_chunker/           # NP chunking module
│   ├── trankit_parser/       # Trankit parser
│   └── stanza_parser/        # Stanza parser
├── annotation/               # Annotation components
│   └── tne_ui/              # Web annotation interface
├── neural_models/            # Neural model components
│   └── neural_coref/        # Neural coreference models
└── llm_evaluation/          # LLM evaluation components
    └── llm_coref/           # LLM evaluation scripts
```

## Data (`data/`)

```
data/
├── corpus/                   # Hebrew corpus data
│   ├── UD_Hebrew-HTB/       # Universal Dependencies Hebrew
│   ├── UD_row_tokenized_sentence/
│   ├── UD_row_amit_seg_sentence/
│   └── 50_gold_mentions/    # Gold standard mentions
├── sqlite_data/             # SQLite databases
├── raw_data/                # Raw data files
└── np_data/                 # NP processing data
```

## Outputs (`outputs/`)

```
outputs/
├── np_chunk_output/         # NP chunking results
│   └── version_5/           # Version-specific outputs
└── np_result_test/          # Test results
```

## Tools (`tools/`)

```
tools/
├── integrated_workflow.py    # Complete workflow script
├── dispaly_apps/            # Visualization tools
├── tree_visulization/       # Tree visualization
├── evaluation/              # Evaluation scripts
├── legacy_pipeline/         # Legacy pipeline components
└── crf/                     # CRF tools
```

## Examples (`examples/`)

```
examples/
├── demo_integration.py      # System demo
├── random/                  # Random examples
└── re_split_doc/           # Document splitting examples
```

## Tests (`tests/`)

```
tests/
└── test_chuncker.py        # Chunker tests
```

## Scripts (`scripts/`)

```
scripts/
├── chunker_runner.py        # Chunker runner
├── serve_chunker.py         # Chunker server
├── create_conll_file.py     # CONLL file creator
├── make_tne_docs.py         # TNE document creator
├── make_demo_docs.py        # Demo document creator
├── make_paper_mentions_by_gold_parse_for_llm.py
└── make_paper_mentions_by_danit_for_llm.py
```

## Documentation (`docs/`)

```
docs/
├── COMPLETE_INTEGRATION_SUMMARY.md
└── INTEGRATION_SUMMARY.md
```

## Component Details

### 1. Mention Detection (`src/mention_detection/`)

**Purpose**: Extract noun phrases and mentions from Hebrew text

**Components**:
- `np_chunker/`: Core NP chunking functionality
- `trankit_parser/`: Trankit-based parsing
- `stanza_parser/`: Stanza-based parsing

**Usage**:
```bash
python main.py mention-detect --input <file> --parser stanza
```

### 2. Annotation (`src/annotation/`)

**Purpose**: Web-based annotation interface for coreference

**Components**:
- `tne_ui/`: Complete web annotation system

**Features**:
- Coreference annotation
- NP-relation annotation
- Consolidation tools
- Training interfaces

**Usage**:
```bash
python main.py serve --db-dir data/tne_ui/data --db-name annotation_db
```

### 3. Neural Models (`src/neural_models/`)

**Purpose**: Neural coreference resolution models

**Components**:
- `neural_coref/`: Complete neural coreference system

**Models**:
- LingMess-Coref
- WL-Coref

**Features**:
- SOTA tokenization evaluation
- Multi-seed experiments
- Comprehensive evaluation

**Usage**:
```bash
python main.py train-neural --base-model onlplab/alephbert-base
```

### 4. LLM Evaluation (`src/llm_evaluation/`)

**Purpose**: Evaluate Large Language Models on coreference tasks

**Components**:
- `llm_coref/`: LLM evaluation system

**Models**:
- GPT-4
- GPT-3.5
- Claude

**Features**:
- Zero-shot evaluation
- Prompt engineering
- Comprehensive metrics

**Usage**:
```bash
python main.py evaluate-llm --model gpt-4 --eval-data data/example.jsonl
```

## Main Entry Point

The `main.py` file provides a clean interface to all components:

```bash
# Complete pipeline
python main.py run --input data/corpus/UD_Hebrew-HTB/he_htb-ud-dev.conllu

# Individual components
python main.py mention-detect --input <file> --parser stanza
python main.py annotate --input <np_results> --db-name annotation_db
python main.py train-neural --base-model onlplab/alephbert-base
python main.py evaluate-llm --model gpt-4 --eval-data data/example.jsonl

# Start annotation server
python main.py serve --db-dir data/tne_ui/data --db-name annotation_db

# Run demo
python main.py demo

# Show system information
python main.py info
```

## Configuration

The `config.py` file centralizes all configuration:

- **Component paths**: All directory paths
- **Model configurations**: Settings for neural and LLM models
- **Evaluation metrics**: MUC, B³, CEAF
- **Workflow steps**: Complete pipeline definition

## Benefits of This Structure

### 1. Clean Organization
- **Logical separation**: Each component has its own directory
- **Clear hierarchy**: Source, data, outputs, tools, examples, tests
- **Easy navigation**: Intuitive directory structure

### 2. Modular Design
- **Independent components**: Each component can be used separately
- **Clear interfaces**: Well-defined entry points
- **Easy maintenance**: Isolated components are easier to maintain

### 3. Professional Structure
- **Standard layout**: Follows Python project conventions
- **Proper packaging**: Includes setup.py for distribution
- **Documentation**: Comprehensive documentation structure

### 4. Scalable Architecture
- **Easy extension**: New components can be added easily
- **Clear dependencies**: Dependencies are well-defined
- **Flexible configuration**: Centralized configuration management

## File Naming Conventions

- **Directories**: lowercase_with_underscores
- **Python files**: lowercase_with_underscores.py
- **Configuration files**: config.py, setup.py
- **Documentation**: README.md, PROJECT_STRUCTURE.md
- **Scripts**: descriptive_names.py

## Best Practices

1. **Keep root clean**: Only essential files in root directory
2. **Logical grouping**: Related files in appropriate directories
3. **Clear naming**: Descriptive file and directory names
4. **Documentation**: Comprehensive documentation for each component
5. **Configuration**: Centralized configuration management
6. **Testing**: Proper test structure and organization 
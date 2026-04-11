# Hebrew Coreference Resolution System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive toolkit for Hebrew coreference resolution that integrates multiple components into a unified pipeline. This system provides mention detection, web-based annotation, neural coreference models, and LLM evaluation capabilities.

## 🚀 Features

### Core Components
- **Mention Detection**: Advanced NP chunking with multiple parser backends (Stanza, Trankit, Gold)
- **Web Annotation**: Interactive web interface for coreference and NP-relation annotation
- **Neural Models**: State-of-the-art neural coreference resolution (LingMess-Coref, WL-Coref)
- **LLM Evaluation**: Comprehensive evaluation of Large Language Models for coreference tasks

### Key Capabilities
- ✅ **Multi-Parser Support**: Stanza, Trankit, and Gold standard parsing
- ✅ **Interactive Annotation**: Web-based interface for manual annotation
- ✅ **Neural Training**: End-to-end neural model training and evaluation
- ✅ **LLM Integration**: Zero-shot and few-shot evaluation of LLMs
- ✅ **Comprehensive Evaluation**: MUC, B³, CEAF metrics
- ✅ **Production Ready**: Clean CLI interface and modular architecture
- ✅ **Extensible**: Easy to add new models and components

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [System Architecture](#system-architecture)
- [Usage](#usage)
- [Configuration](#configuration)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/shaked571/hebrew_coreference.git
cd hebrew_coreference

# Clone the data submodule
git submodule update --init --recursive

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### 1. Mention Detection
```bash
# Run NP chunking with Stanza parser
python src/mention_detection/stanza_parser/stanza_chunker.py

# Run NP chunking with Trankit parser
python src/mention_detection/trankit_parser/trankit2spacy.py
```

### 2. Neural Coreference
```bash
# Train LingMess-Coref model
cd src/neural_models/neural_coref/src/lingmess-coref
python training.py

# Evaluate model
python eval.py
```

### 3. LLM Evaluation
```bash
# Compare LLM outputs
cd error_analysis/llm_comparison
python compare_multi_system_outputs.py --approaches raw gold_tokenized sota_tokenized
```

### 4. Web Annotation
```bash
# Start annotation server
cd src/annotation/tne_ui
python annotationServer.py
```

## 🏗️ System Architecture

```
hebrew_coreference/
├── src/
│   ├── mention_detection/          # NP chunking and parsing
│   ├── neural_models/             # Neural coreference models
│   ├── llm_evaluation/            # LLM evaluation framework
│   └── annotation/                # Web-based annotation tools
├── error_analysis/                # Error analysis and comparison tools
├── statistics/                    # Statistical analysis tools
├── tests/                         # Test suite
├── data/                          # Data submodule (separate repo)
└── scripts/                       # Utility scripts
```

## 📖 Usage 

### Mention Detection
The system supports multiple parsing backends for robust mention detection:

- **Stanza**: Stanford's NLP toolkit with Hebrew support
- **Trankit**: Unified multilingual NLP toolkit
- **Gold**: Manual annotation for high-quality reference

### Neural Models
Two state-of-the-art neural architectures:

- **LingMess-Coref**: End-to-end neural coreference resolution
- **WL-Coref**: Span-based coreference with BERT encoding

### LLM Evaluation
Comprehensive evaluation framework for Large Language Models:

- **Raw Tokenization**: Direct LLM output evaluation
- **Gold Tokenization**: Aligned with reference tokenization
- **SOTA Tokenization**: State-of-the-art tokenization alignment

### Web Annotation
Interactive annotation interface for:

- Coreference annotation
- NP-relation annotation
- Mention boundary correction
- Quality control and validation

## ⚙️ Configuration

### Environment Variables
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export CUDA_VISIBLE_DEVICES=0  # For GPU training
```

### Model Configuration
Models can be configured through YAML files in their respective directories:
- `src/neural_models/neural_coref/src/lingmess-coref/config.yaml`
- `src/neural_models/neural_coref/src/wl-coref/config.toml`

## 📚 Examples

### Basic NP Chunking
```python
from src.mention_detection.np_chunker.chunker import NPChunker

chunker = NPChunker()
chunks = chunker.chunk_text("הטקסט בעברית עם שמות עצם")
print(chunks)
```

### Coreference Evaluation
```python
from src.neural_models.neural_coref.src.lingmess_coref.metrics import CorefEvaluator

evaluator = CorefEvaluator()
scores = evaluator.evaluate(predictions, gold)
print(f"MUC: {scores['muc']}, B³: {scores['b3']}, CEAF: {scores['ceaf']}")
```

### LLM Comparison
```python
from error_analysis.llm_comparison.compare_multi_system_outputs import MultiSystemComparisonRunner

runner = MultiSystemComparisonRunner()
results = runner.run_comprehensive_analysis()
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m pytest tests/

# Run specific test categories
python -m pytest tests/test_mention_detection.py
python -m pytest tests/test_neural_models.py
python -m pytest tests/test_llm_evaluation.py
```

## 📊 Error Analysis

The system includes comprehensive error analysis tools:

- **Cluster-level Analysis**: Detailed breakdown of correct/missed/extra clusters
- **Multi-system Comparison**: Compare different approaches side-by-side
- **Visualization**: Generate charts and graphs for analysis
- **Statistical Testing**: Significance testing for performance differences

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Hebrew NLP community for language resources
- Stanford NLP Group for Stanza
- Microsoft Research for Trankit
- Contributors to LingMess-Coref and WL-Coref

## 📞 Support

For questions and support:
- Open an issue on GitHub
- Check the documentation in each component directory
- Review the error analysis outputs for troubleshooting

---

**Note**: This system is designed specifically for Hebrew text and includes Hebrew-specific optimizations and linguistic features.

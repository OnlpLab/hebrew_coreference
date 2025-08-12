"""
Configuration file for Hebrew Coreference Resolution System.
Integrates four components: mention detection, annotation, neural models, and LLM models.
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
SRC_DIR = BASE_DIR / "src"
DATA_DIR = BASE_DIR / "data"
OUTPUTS_DIR = BASE_DIR / "outputs"
TOOLS_DIR = BASE_DIR / "tools"
EXAMPLES_DIR = BASE_DIR / "examples"
TESTS_DIR = BASE_DIR / "tests"
DOCS_DIR = BASE_DIR / "docs"

# Component paths
MENTION_DETECTION_DIR = SRC_DIR / "mention_detection"
ANNOTATION_DIR = SRC_DIR / "annotation"
NEURAL_MODELS_DIR = SRC_DIR / "neural_models"
LLM_EVALUATION_DIR = SRC_DIR / "llm_evaluation"

# TNE UI specific paths (now under annotation)
TNE_UI_DIR = ANNOTATION_DIR / "tne_ui"
TNE_DATA_DIR = TNE_UI_DIR / "data"
TNE_ANNOTATION_RESULTS_DIR = TNE_UI_DIR / "annotation_results"
TNE_STATIC_DIR = TNE_UI_DIR / "static"

# Neural Coref paths (now under neural_models)
NEURAL_COREF_DIR = NEURAL_MODELS_DIR / "neural_coref"
NEURAL_SRC_DIR = NEURAL_COREF_DIR / "src"
NEURAL_RESULTS_DIR = NEURAL_COREF_DIR / "results"
NEURAL_CACHE_DIR = NEURAL_COREF_DIR / "cache"
NEURAL_DATA_DIR = NEURAL_COREF_DIR / "data"

# LLM Coref paths (now under llm_evaluation)
LLM_COREF_DIR = LLM_EVALUATION_DIR / "llm_coref"
LLM_SRC_DIR = LLM_COREF_DIR / "src"
LLM_DATA_DIR = LLM_COREF_DIR / "data"
LLM_RESULTS_DIR = LLM_COREF_DIR / "results"
LLM_SCRIPTS_DIR = LLM_COREF_DIR / "scripts"
LLM_UTILS_DIR = LLM_COREF_DIR / "utils"

# Corpus paths (now under data)
CORPUS_DIR = DATA_DIR / "corpus"
UD_HEBREW_HTB_DIR = CORPUS_DIR / "UD_Hebrew-HTB"
UD_ROW_TOKENIZED_DIR = CORPUS_DIR / "UD_row_tokenized_sentence"
UD_ROW_AMIT_SEG_DIR = CORPUS_DIR / "UD_row_amit_seg_sentence"
GOLD_MENTIONS_DIR = CORPUS_DIR / "50_gold_mentions"

# Default files
DEFAULT_DEV_FILE = UD_HEBREW_HTB_DIR / "he_htb-ud-dev.conllu"
DEFAULT_TEST_FILE = UD_HEBREW_HTB_DIR / "he_htb-ud-test.conllu"
DEFAULT_TRAIN_FILE = UD_HEBREW_HTB_DIR / "he_htb-ud-train.conllu"

# Component configurations
COMPONENTS = {
    "mention_detector": {
        "name": "HebNpChunker",
        "description": "Hebrew NP chunking and mention detection",
        "parsers": ["stanza", "trankit", "gold"],
        "output_formats": ["webbano", "json", "conllu"]
    },
    "annotation_tool": {
        "name": "TNE UI",
        "description": "Web-based annotation interface for coreference",
        "features": ["coreference", "np_relations", "consolidation"],
        "port": 8080
    },
    "neural_models": {
        "name": "Neural Hebrew Coref",
        "description": "Neural coreference resolution models",
        "models": ["lingmess-coref", "wl-coref"],
        "features": ["SOTA tokenization", "multi-seed evaluation"]
    },
    "llm_models": {
        "name": "LLM Coref",
        "description": "Large Language Model coreference resolution",
        "models": ["gpt-4", "gpt-3.5-turbo", "claude"],
        "features": ["zero-shot", "few-shot", "prompt engineering"]
    }
}

# Parser configurations
PARSERS = {
    "stanza": {
        "name": "Stanza",
        "module": "src.mention_detection.stanza_parser.stanza_chunker",
        "class": "StanzaChunker",
        "description": "Stanford NLP's multilingual parser"
    },
    "trankit": {
        "name": "Trankit", 
        "module": "src.mention_detection.trankit_parser.trankit2spacy",
        "class": "TrankitParser",
        "description": "Trankit parser for multilingual NLP"
    },
    "gold": {
        "name": "Gold Standard",
        "module": "src.mention_detection.np_chunker.chunker",
        "class": "Chunker",
        "description": "Gold standard annotations"
    }
}

# Neural model configurations
NEURAL_MODELS = {
    "lingmess-coref": {
        "name": "LingMess Coref",
        "description": "Linguistically motivated coreference resolution",
        "script": "src/neural_models/neural_coref/src/lingmess-coref/run.py",
        "config": "src/neural_models/neural_coref/src/lingmess-coref/config.yaml"
    },
    "wl-coref": {
        "name": "WL-Coref",
        "description": "Word-level coreference resolution",
        "script": "src/neural_models/neural_coref/src/wl-coref/run.py",
        "config": "src/neural_models/neural_coref/src/wl-coref/config.yaml"
    }
}

# LLM model configurations
LLM_MODELS = {
    "gpt-4o-mini": {
        "name": "GPT-4o Mini",
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "gpt4o": {
        "name": "GPT-4o",
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "gpt4.1": {
        "name": "GPT-4.1",
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "gpt-3.5-turbo": {
        "name": "GPT-3.5 Turbo",
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "gemini-2.0-flash": {
        "name": "Gemini 2.0 Flash",
        "provider": "google",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "gemini-2.0-flash-lite": {
        "name": "Gemini 2.0 Flash Lite",
        "provider": "google",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "gemini-2.5-pro": {
        "name": "Gemini 2.5 Pro",
        "provider": "google",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "o1": {
        "name": "O1",
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.0
    },
    "o3": {
        "name": "O3",
        "provider": "openai",
        "max_tokens": 4000,
        "temperature": 0.0
    }
}

# TNE UI configurations
TNE_CONFIG = {
    "default_port": 8080,
    "default_host": "0.0.0.0",
    "debug_mode": True,
    "database_dir": str(TNE_DATA_DIR),
    "default_db_name": "annotation_db",
    "static_dir": str(TNE_STATIC_DIR),
    "annotation_results_dir": str(TNE_ANNOTATION_RESULTS_DIR)
}

# Neural coref configurations
NEURAL_CONFIG = {
    "base_models": ["onlplab/alephbert-base", "microsoft/mdeberta-v3-base"],
    "seeds": [42, 123, 2021, 31415, 27182],
    "evaluation_metrics": ["muc", "b3", "ceaf"],
    "sota_evaluation": True
}

# LLM coref configurations
LLM_CONFIG = {
    "prompt_templates": ["doc_template", "qa_template"],
    "evaluation_metrics": ["muc", "b3", "ceaf"],
    "batch_size": 1,
    "timeout": 60
}

# Output configurations
OUTPUT_CONFIG = {
    "np_output_dir": str(OUTPUTS_DIR / "np_chunk_output"),
    "version": "v6.0",
    "formats": ["webbano", "json", "conllu"],
    "default_format": "webbano"
}

# Evaluation configurations
EVALUATION_CONFIG = {
    "gold_standard_file": str(GOLD_MENTIONS_DIR / "50_clean_sentences_shaked.tsv"),
    "metrics": ["precision", "recall", "f1"],
    "output_format": "detailed"
}

# Web interface configurations
WEB_CONFIG = {
    "displacy_port": 8081,
    "chunker_port": 8082,
    "tne_port": 8080,
    "neural_port": 8083,
    "llm_port": 8084
}

def ensure_directories():
    """Ensure all necessary directories exist."""
    directories = [
        OUTPUTS_DIR,
        DATA_DIR,
        TNE_DATA_DIR,
        TNE_ANNOTATION_RESULTS_DIR,
        NEURAL_RESULTS_DIR,
        NEURAL_CACHE_DIR,
        NEURAL_DATA_DIR,
        LLM_RESULTS_DIR,
        LLM_DATA_DIR,
        TOOLS_DIR,
        EXAMPLES_DIR,
        TESTS_DIR,
        DOCS_DIR
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    return True

def get_component_config(component_name):
    """Get configuration for a specific component."""
    return COMPONENTS.get(component_name, {})

def get_parser_config(parser_name):
    """Get configuration for a specific parser."""
    return PARSERS.get(parser_name, PARSERS["stanza"])

def get_neural_model_config(model_name):
    """Get configuration for a specific neural model."""
    return NEURAL_MODELS.get(model_name, {})

def get_llm_model_config(model_name):
    """Get configuration for a specific LLM model."""
    return LLM_MODELS.get(model_name, {})

def get_tne_urls(hit_id=1, coref_ann_id=1):
    """Get TNE UI URLs for different annotation tasks."""
    base_url = f"http://localhost:{TNE_CONFIG['default_port']}"
    
    return {
        "coref": f"{base_url}/tne/tool/coref/{hit_id}",
        "links": f"{base_url}/tne/tool/links/{hit_id}/{coref_ann_id}",
        "consolidation": f"{base_url}/tne/tool/consolidation/{hit_id}/{coref_ann_id}",
        "training": f"{base_url}/static/coref_training.html",
        "instructions": f"{base_url}/static/intro_tne.html",
        "np_training": f"{base_url}/static/tne_training.html"
    }

def get_output_path(version=None, parser="stanza", format="webbano"):
    """Get output path for NP chunking results."""
    if version is None:
        version = OUTPUT_CONFIG["version"]
    
    filename = f"algo_output_{parser}_{format}_{version}.{format}"
    return OUTPUTS_DIR / "np_chunk_output" / version / filename

def get_neural_results_path(model_name, base_model, seed):
    """Get results path for neural model outputs."""
    return NEURAL_RESULTS_DIR / model_name / base_model.replace("/", "_") / f"seed_{seed}"

def get_llm_results_path(model_name, experiment_name):
    """Get results path for LLM model outputs."""
    return LLM_RESULTS_DIR / model_name / experiment_name

def validate_paths():
    """Validate that all required paths exist."""
    required_paths = [
        TNE_UI_DIR,
        NEURAL_COREF_DIR,
        LLM_COREF_DIR,
        CORPUS_DIR,
        UD_HEBREW_HTB_DIR,
        TNE_STATIC_DIR,
        NEURAL_SRC_DIR,
        LLM_SRC_DIR
    ]
    
    missing_paths = []
    for path in required_paths:
        if not path.exists():
            missing_paths.append(str(path))
    
    if missing_paths:
        print("Warning: The following required paths are missing:")
        for path in missing_paths:
            print(f"  - {path}")
        return False
    
    return True

def get_workflow_steps():
    """Get the complete workflow steps for Hebrew coreference resolution."""
    return [
        {
            "step": 1,
            "name": "Mention Detection",
            "component": "HebNpChunker",
            "description": "Extract noun phrases and mentions from Hebrew text",
            "output": "NP chunks and mention spans"
        },
        {
            "step": 2,
            "name": "Data Annotation",
            "component": "TNE UI",
            "description": "Annotate coreference clusters and NP relations",
            "output": "Annotated coreference data"
        },
        {
            "step": 3,
            "name": "Neural Model Training",
            "component": "Neural Coref",
            "description": "Train neural coreference resolution models",
            "output": "Trained neural models"
        },
        {
            "step": 4,
            "name": "LLM Evaluation",
            "component": "LLM Coref",
            "description": "Evaluate LLMs on coreference tasks",
            "output": "LLM coreference predictions"
        },
        {
            "step": 5,
            "name": "Evaluation & Comparison",
            "component": "Evaluation",
            "description": "Compare all approaches and generate reports",
            "output": "Comprehensive evaluation results"
        }
    ]

# Initialize directories on import
ensure_directories() 
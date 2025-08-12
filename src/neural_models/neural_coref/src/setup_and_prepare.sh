#!/bin/bash

# NOTE: Run this script from the project root: ./src/setup_and_prepare.sh
# This script sets up the environment for running src/run_all_experiments.sh
# Designed for a Unix server with pyenv (no conda), e.g., A100 machine

set -e

PYTHON_VERSION=3.8.18
VENV_NAME=coref_env

# Check for pyenv
if ! command -v pyenv &> /dev/null; then
  echo "pyenv not found. Please install pyenv first."
  exit 1
fi

# Install Python version if not present
if ! pyenv versions --bare | grep -q "$PYTHON_VERSION"; then
  echo "Installing Python $PYTHON_VERSION via pyenv..."
  pyenv install $PYTHON_VERSION
fi

# Create virtualenv if not present
if ! pyenv virtualenvs --bare | grep -q "$VENV_NAME"; then
  echo "Creating pyenv virtualenv $VENV_NAME..."
  pyenv virtualenv $PYTHON_VERSION $VENV_NAME
fi

# Activate virtualenv
export PYENV_VERSION=$VENV_NAME

echo "Using Python: $(python --version)"

# Ensure pip is installed
if ! command -v pip &> /dev/null; then
  echo "pip not found, installing..."
  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python get-pip.py
  rm get-pip.py
fi

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Download spacy English model
python -m spacy download en_core_web_sm

# Ensure tabulate is installed for summary table
pip install tabulate

# Print instructions for data and weights
cat <<EOM

========================================
Setup complete!

Next steps:
- Prepare your data and model weights as required by lingmess-coref and wl-coref.
- Place data and weights in the expected locations (see README and original repos).
- If using CUDA, ensure the correct CUDA toolkit is available for your PyTorch version.

To activate this environment in a new shell:
  export PYENV_VERSION=$VENV_NAME

You can now run:
  ./src/run_all_experiments.sh <base_model>

========================================
EOM
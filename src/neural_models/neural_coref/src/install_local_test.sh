#!/bin/bash

# Installation script for local testing environment on macOS M3
# This script sets up the minimal requirements for running the local test

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info "Setting up local test environment for macOS M3"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS. Current OS: $OSTYPE"
    exit 1
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    print_info "You can install it via Homebrew: brew install python3"
    exit 1
fi

print_info "Python 3 found: $(python3 --version)"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not available. Please install pip3 first."
    exit 1
fi

print_info "pip3 found: $(pip3 --version)"

# Use existing conda environment
print_info "Using existing conda environment: hebrew_coref"
if conda env list | grep -q "hebrew_coref"; then
    print_info "Activating conda environment: hebrew_coref"
    eval "$(conda shell.bash hook)"
    conda activate hebrew_coref
    print_info "Conda environment activated"
else
    print_error "Conda environment 'hebrew_coref' not found!"
    print_info "Available environments:"
    conda env list
    exit 1
fi

# Install requirements using conda
print_info "Installing requiremen
ts using conda..."
conda install -y pytorch torchvision torchaudio -c pytorch
conda install -y transformers numpy pandas tqdm -c conda-forge
pip install jsonlines colorama

# Test PyTorch MPS availability
print_info "Testing PyTorch MPS availability..."
python3 -c "
import torch
print(f'PyTorch version: {torch.__version__}')
if torch.backends.mps.is_available():
    print('✅ MPS is available - GPU acceleration will be used')
    device = torch.device('mps')
    # Test basic tensor operations
    x = torch.randn(3, 3, device=device)
    y = torch.randn(3, 3, device=device)
    z = torch.mm(x, y)
    print('✅ MPS tensor operations working correctly')
else:
    print('⚠️  MPS not available - will use CPU')
"

print_info "Installation completed successfully!"
print_info ""
print_info "To run the local test:"
print_info "  ./src/test_local.sh <model_path> <test_file>"
print_info ""
print_info "Example:"
print_info "  ./src/test_local.sh /Users/s0g0a87/studies/lingmess-coref/results/final_split/aleph data/lingmess/hebrew/test.hebrew.jsonlines" 
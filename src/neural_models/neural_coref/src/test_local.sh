#!/bin/bash

# Local test script for macOS M3
# Usage: ./test_local.sh <model_path> <test_file> [output_file]
dedkljnel
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script is designed for macOS. Current OS: $OSTYPE"
    exit 1
fi

# Check if we have the required arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <model_path> <test_file> [output_file]"
    echo ""
    echo "Arguments:"
    echo "  model_path    Path to the trained model directory"
    echo "  test_file     Path to test data file (JSONLines format)"
    echo "  output_file   (Optional) Output file for results (default: local_test_output.json)"
    echo ""
    echo "Example:"
    echo "  $0 /Users/s0g0a87/studies/lingmess-coref/results/final_split/aleph data/lingmess/hebrew/test.hebrew.jsonlines"
    exit 1
fi

MODEL_PATH="$1"
TEST_FILE="$2"
OUTPUT_FILE="${3:-local_test_output.json}"

print_info "Starting local test on macOS M3"
print_info "Model path: $MODEL_PATH"
print_info "Test file: $TEST_FILE"
print_info "Current directory: $(pwd)"
print_info "Checking if test file exists..."
if [ -f "$TEST_FILE" ]; then
    print_info "Test file exists at: $TEST_FILE"
    # Convert to absolute path since Python script runs from src/ directory
    TEST_FILE="$(pwd)/$TEST_FILE"
    print_info "Using absolute path: $TEST_FILE"
else
    print_warning "Test file not found at: $TEST_FILE"
    print_info "Looking for test file in data/lingmess/hebrew/..."
    if [ -f "data/lingmess/hebrew/test.hebrew.jsonlines" ]; then
        print_info "Found test file at: data/lingmess/hebrew/test.hebrew.jsonlines"
        # Convert to absolute path since Python script runs from src/ directory
        TEST_FILE="$(pwd)/data/lingmess/hebrew/test.hebrew.jsonlines"
        print_info "Using absolute path: $TEST_FILE"
    elif [ -f "../data/lingmess/hebrew/test.hebrew.jsonlines" ]; then
        print_info "Found test file at: ../data/lingmess/hebrew/test.hebrew.jsonlines"
        TEST_FILE="$(pwd)/../data/lingmess/hebrew/test.hebrew.jsonlines"
        print_info "Using absolute path: $TEST_FILE"
    else
        print_error "Test file not found in expected locations"
        print_info "Available files in data/lingmess/hebrew/:"
        if [ -d "data/lingmess/hebrew" ]; then
            ls -la data/lingmess/hebrew/
        elif [ -d "../data/lingmess/hebrew" ]; then
            ls -la ../data/lingmess/hebrew/
        fi
    fi
fi
print_info "Output file: $OUTPUT_FILE"

# Check if paths exist
if [ ! -d "$MODEL_PATH" ]; then
    print_error "Model path does not exist: $MODEL_PATH"
    exit 1
fi

if [ ! -f "$TEST_FILE" ]; then
    print_error "Test file does not exist: $TEST_FILE"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "src/lingmess-coref/run.py" ]; then
    print_error "Please run this script from the project root directory"
    print_error "Expected to find: src/lingmess-coref/run.py"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

print_info "Checking PyTorch availability..."
eval "$(conda shell.bash hook)"
conda activate lingmess


# Run the test with conda environment
print_info "Running local test with conda environment..."
cd src

# Activate conda environment
eval "$(conda shell.bash hook)"
conda activate lingmess

python test_local_simple.py \
    --model_path "$MODEL_PATH" \
    --test_file "$TEST_FILE" \
    --output_file "$OUTPUT_FILE"

if [ $? -eq 0 ]; then
    print_info "Test completed successfully!"
    print_info "Results saved to: $OUTPUT_FILE"
    
    # Check if output file was created
    if [ -f "$OUTPUT_FILE" ]; then
        print_info "Output file size: $(ls -lh "$OUTPUT_FILE" | awk '{print $5}')"
    fi
else
    print_error "Test failed!"
    exit 1
fi 
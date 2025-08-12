#!/usr/bin/env python3
"""
Debug script to check if model weights are corrupted during loading.
"""

import torch
from transformers import AutoConfig, AutoTokenizer
import sys
import os


def check_model_weights(model_name):
    """Check if model weights are corrupted during loading."""

    print(f"Checking model: {model_name}")

    try:
        # Load config from HuggingFace Hub
        config = AutoConfig.from_pretrained(model_name)
        print(f"✓ Config loaded successfully")

        # Add coref_head configuration
        config.coref_head = {
            "max_span_length": 30,
            "top_lambda": 0.4,
            "ffnn_size": 2048,
            "dropout_prob": 0.3,
            "max_segment_len": 512,
            "max_doc_len": 4096
        }
        print(f"✓ Added coref_head configuration")

        # Load tokenizer from HuggingFace Hub
        tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        print(f"✓ Tokenizer loaded successfully")

        # Try to load model weights from HuggingFace Hub
        print("Loading model weights from HuggingFace Hub...")

        # Import the model class
        sys.path.append('lingmess-coref')
        from modeling_lingmess import LingMessCoref

        # Load model from HuggingFace Hub
        model, loading_info = LingMessCoref.from_pretrained(
            model_name,
            output_loading_info=True,
            config=config
        )

        print(f"✓ Model loaded successfully")
        print(f"Loading info: {loading_info}")

        # Check if any parameters are NaN
        nan_params = []
        total_params = 0

        for name, param in model.named_parameters():
            total_params += 1
            if torch.isnan(param).any():
                nan_params.append(name)

        print(f"\nParameter check:")
        print(f"  Total parameters: {total_params}")
        print(f"  Parameters with NaN: {len(nan_params)}")

        if nan_params:
            print(f"  First 10 NaN parameters: {nan_params[:10]}")
            return False
        else:
            print(f"  ✓ All parameters are valid")
            return True

    except Exception as e:
        print(f"ERROR loading model: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_device_transfer(model_name):
    """Test if moving model to different devices causes NaN."""

    print(f"\nTesting device transfer for: {model_name}")

    try:
        # Load model from HuggingFace Hub
        sys.path.append('lingmess-coref')
        from modeling_lingmess import LingMessCoref
        from transformers import AutoConfig

        config = AutoConfig.from_pretrained(model_name)
        config.coref_head = {
            "max_span_length": 30,
            "top_lambda": 0.4,
            "ffnn_size": 2048,
            "dropout_prob": 0.3,
            "max_segment_len": 512,
            "max_doc_len": 4096
        }

        model = LingMessCoref.from_pretrained(model_name, config=config)

        # Test different devices
        devices = ['cpu']
        if torch.cuda.is_available():
            devices.append('cuda:0')

        for device_name in devices:
            print(f"\nTesting {device_name}:")
            device = torch.device(device_name)

            try:
                # Move model to device
                model.to(device)
                print(f"  ✓ Model moved to {device_name}")

                # Check for NaN parameters
                nan_count = 0
                for name, param in model.named_parameters():
                    if torch.isnan(param).any():
                        nan_count += 1
                        if nan_count <= 5:  # Show first 5
                            print(f"    NaN in {name}")

                if nan_count == 0:
                    print(f"  ✓ No NaN parameters on {device_name}")
                else:
                    print(f"  ✗ Found {nan_count} parameters with NaN on {device_name}")

            except Exception as e:
                print(f"  ✗ Error on {device_name}: {e}")

    except Exception as e:
        print(f"ERROR in device transfer test: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python debug_model_loading.py <model_name>")
        print("Example: python debug_model_loading.py dicta-il/dictabert-large")
        sys.exit(1)

    model_name = sys.argv[1]

    # Check if model weights are corrupted
    success = check_model_weights(model_name)

    if success:
        # Test device transfer
        test_device_transfer(model_name)
    else:
        print("\nModel loading failed - weights may be corrupted") 
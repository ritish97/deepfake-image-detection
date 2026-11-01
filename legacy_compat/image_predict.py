"""
DeepFake Sentinel - Standalone Image Prediction Script
Author references and hardcoded paths removed; supports CLI arguments.
"""

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.forensics import analyze_face_forensics
from core.models import load_checkpoint
from core.config import get_torch_device


def predict(image_path, model_path=None, arch="resnet34"):
    device = get_torch_device()
    print(f"Using compute device: {device}")

    model = None
    if model_path and os.path.isfile(model_path):
        model, arch, _ = load_checkpoint(model_path, device=device, fallback_arch=arch)
        print(f"Loaded model architecture: {arch}")

    res = analyze_face_forensics(image_path, model=model, device=device)

    print(f"\n==========================================")
    print(f" Prediction:         {res['prediction']}")
    print(f" Authenticity Score: {res['authenticity_score']}%")
    print(f" Fake Probability:   {res['fake_probability'] * 100:.2f}%")
    print(f" Risk Level:         {res['risk_level']}")
    print(f"==========================================\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeepFake Image Predictor")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--model", default=None, help="Path to .pth checkpoint")
    parser.add_argument("--arch", default="resnet34", help="Model architecture")
    args = parser.parse_args()

    predict(args.image, args.model, args.arch)

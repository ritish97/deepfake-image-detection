"""
DeepFake Sentinel - Global Configuration and Environment Management
"""

import os
import sys

# Project directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
REPORTS_DIR = os.path.join(OUTPUTS_DIR, "reports")
FACES_DIR = os.path.join(OUTPUTS_DIR, "extracted_faces")

for d in [MODELS_DIR, OUTPUTS_DIR, REPORTS_DIR, FACES_DIR]:
    os.makedirs(d, exist_ok=True)

# Architecture choices
SUPPORTED_ARCHITECTURES = [
    "resnet18",
    "resnet34",
    "resnet50",
    "resnext50_32x4d",
    "mobilenet_v2",
    "densenet121",
    "efficientnet_b0"
]

DEFAULT_ARCH = "resnet34"
DEFAULT_IMG_SIZE = (224, 224)
DEFAULT_BATCH_SIZE = 32
DEFAULT_EPOCHS = 10
DEFAULT_LR = 1e-4

# Detection thresholds
FAKE_PROBABILITY_THRESHOLD = 0.50
HIGH_CONFIDENCE_THRESHOLD = 0.80

# Class definition
CLASSES = ["Real", "Fake"]
CLASS_TO_IDX = {"Real": 0, "Fake": 1}
IDX_TO_CLASS = {0: "Real", 1: "Fake"}

def get_torch_device():
    """Detect and return torch device if torch is available, else 'cpu'."""
    try:
        import torch
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    except ImportError:
        return "cpu"

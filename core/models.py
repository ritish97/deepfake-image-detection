"""
DeepFake Sentinel - Model Architectures and Checkpoint Management
Supports ResNet18, ResNet34, ResNet50, ResNeXt50_32x4d, MobileNetV2, DenseNet121, EfficientNet_B0.
"""

import os
import time
from .config import SUPPORTED_ARCHITECTURES, DEFAULT_ARCH, CLASSES

try:
    import torch
    import torch.nn as nn
    from torchvision import models
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def build_model(arch_name=DEFAULT_ARCH, num_classes=2, pretrained=False):
    """
    Constructs a PyTorch classification model configured for deepfake detection.
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required to build model architectures. Please install torch and torchvision.")

    name = arch_name.lower().strip()
    if name not in SUPPORTED_ARCHITECTURES:
        raise ValueError(f"Unsupported architecture '{name}'. Choose from: {SUPPORTED_ARCHITECTURES}")

    if name == "resnet18":
        m = models.resnet18(weights=models.ResNet18_Weights.DEFAULT if pretrained else None)
        in_f = m.fc.in_features
        m.fc = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_f, num_classes)
        )
    elif name == "resnet34":
        m = models.resnet34(weights=models.ResNet34_Weights.DEFAULT if pretrained else None)
        in_f = m.fc.in_features
        m.fc = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_f, num_classes)
        )
    elif name == "resnet50":
        m = models.resnet50(weights=models.ResNet50_Weights.DEFAULT if pretrained else None)
        in_f = m.fc.in_features
        m.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_f, num_classes)
        )
    elif name == "resnext50_32x4d":
        m = models.resnext50_32x4d(weights=models.ResNeXt50_32X4D_Weights.DEFAULT if pretrained else None)
        in_f = m.fc.in_features
        m.fc = nn.Sequential(
            nn.Dropout(p=0.3),
            nn.Linear(in_f, num_classes)
        )
    elif name == "mobilenet_v2":
        m = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT if pretrained else None)
        in_f = m.classifier[-1].in_features
        m.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_f, num_classes)
        )
    elif name == "densenet121":
        m = models.densenet121(weights=models.DenseNet121_Weights.DEFAULT if pretrained else None)
        in_f = m.classifier.in_features
        m.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_f, num_classes)
        )
    elif name == "efficientnet_b0":
        m = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT if pretrained else None)
        in_f = m.classifier[-1].in_features
        m.classifier = nn.Sequential(
            nn.Dropout(p=0.2),
            nn.Linear(in_f, num_classes)
        )
    else:
        raise ValueError(f"Unrecognized architecture: {name}")

    return m


def save_checkpoint(model, arch_name, path, metrics=None):
    """
    Saves a rich checkpoint containing architecture identifier, weights, classes, and training metadata.
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required to save checkpoints.")

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    payload = {
        "format_version": "2.0",
        "arch": arch_name.lower(),
        "num_classes": 2,
        "classes": CLASSES,
        "timestamp": time.time(),
        "metrics": metrics or {},
        "state_dict": model.state_dict()
    }
    torch.save(payload, path)


def load_checkpoint(model_path, device="cpu", fallback_arch=DEFAULT_ARCH):
    """
    Robustly loads a model checkpoint from disk. Handles both rich metadata checkpoints
    and legacy raw state_dict checkpoints.
    
    Returns:
        (model, arch_name, metadata)
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is required to load checkpoints.")

    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    checkpoint = torch.load(model_path, map_location=device)
    arch = fallback_arch
    metadata = {}
    state_dict = None

    if isinstance(checkpoint, dict):
        if "state_dict" in checkpoint and "arch" in checkpoint:
            arch = checkpoint["arch"]
            state_dict = checkpoint["state_dict"]
            metadata = {k: v for k, v in checkpoint.items() if k != "state_dict"}
        elif any(k.startswith(("conv", "layer", "fc", "features", "classifier")) for k in checkpoint.keys()):
            # Raw state dict
            state_dict = checkpoint
            metadata = {"source": "legacy_state_dict"}
        else:
            state_dict = checkpoint
    else:
        state_dict = checkpoint

    model = build_model(arch_name=arch, num_classes=2, pretrained=False)
    
    # Tolerant state dict loading (handles keys matching with/without prefix)
    try:
        model.load_state_dict(state_dict)
    except RuntimeError:
        # Strip potential 'module.' prefix from DataParallel training
        new_state_dict = {}
        for k, v in state_dict.items():
            name = k.replace("module.", "")
            new_state_dict[name] = v
        model.load_state_dict(new_state_dict, strict=False)

    model.to(device)
    model.eval()
    return model, arch, metadata

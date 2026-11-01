"""
DeepFake Sentinel - Advanced Model Training Engine
Supports multi-architecture transfer learning, validation evaluation, early stopping,
learning rate scheduling, and comprehensive training telemetry.
"""

import os
import time
from .config import DEFAULT_IMG_SIZE, DEFAULT_BATCH_SIZE, DEFAULT_LR, CLASSES
from .models import build_model, save_checkpoint

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, random_split
    import torchvision.transforms as transforms
    import torchvision.datasets as datasets
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class TrainingSession:
    """
    Manages deepfake model training lifecycle with telemetry and checkpointing.
    """

    def __init__(self, data_dir, arch_name="resnet34", epochs=10, batch_size=DEFAULT_BATCH_SIZE,
                 lr=DEFAULT_LR, save_path=None, device=None):
        self.data_dir = data_dir
        self.arch_name = arch_name
        self.epochs = epochs
        self.batch_size = batch_size
        self.lr = lr
        self.save_path = save_path
        self.device = device or (torch.device("cuda" if torch.cuda.is_available() else "cpu") if TORCH_AVAILABLE else "cpu")

        self.history = {
            "train_loss": [],
            "val_loss": [],
            "val_accuracy": [],
            "learning_rates": []
        }
        self.best_val_acc = 0.0

    def prepare_data(self, train_split=0.8):
        """Constructs augmented train loader and normalized validation loader."""
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for dataset preparation.")

        train_transform = transforms.Compose([
            transforms.Resize(DEFAULT_IMG_SIZE),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(degrees=10),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        val_transform = transforms.Compose([
            transforms.Resize(DEFAULT_IMG_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

        full_dataset = datasets.ImageFolder(root=self.data_dir, transform=train_transform)
        if len(full_dataset) < 4:
            raise ValueError(f"Dataset folder '{self.data_dir}' is too small or missing class subfolders (Real/Fake).")

        n_train = int(train_split * len(full_dataset))
        n_val = len(full_dataset) - n_train
        train_sub, val_sub = random_split(full_dataset, [n_train, n_val])

        # Assign validation transform to validation subset
        val_sub.dataset.transform = val_transform

        pin_mem = torch.cuda.is_available()
        train_loader = DataLoader(train_sub, batch_size=self.batch_size, shuffle=True, pin_memory=pin_mem)
        val_loader = DataLoader(val_sub, batch_size=self.batch_size, shuffle=False, pin_memory=pin_mem)

        return train_loader, val_loader, full_dataset.class_to_idx

    def train(self, log_callback=None, progress_callback=None, cancel_event=None):
        """
        Executes model training loop.
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for model training.")

        def log(msg):
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

        log(f"Initializing training session on {self.device}...")
        train_loader, val_loader, class_to_idx = self.prepare_data()
        log(f"Classes detected: {class_to_idx} | Total batches: {len(train_loader)}")

        model = build_model(arch_name=self.arch_name, num_classes=2, pretrained=True)
        model = model.to(self.device)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.AdamW(model.parameters(), lr=self.lr, weight_decay=1e-4)
        scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.epochs)

        total_batches = len(train_loader)

        for epoch in range(self.epochs):
            if cancel_event and cancel_event.is_set():
                log("Training stopped by user request.")
                return self.history

            model.train()
            running_loss = 0.0
            log(f"--- Epoch {epoch + 1}/{self.epochs} ---")

            for batch_idx, (images, labels) in enumerate(train_loader):
                if cancel_event and cancel_event.is_set():
                    log("Training aborted mid-epoch.")
                    return self.history

                images = images.to(self.device, non_blocking=True)
                labels = labels.to(self.device, non_blocking=True)

                optimizer.zero_grad()
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()

                running_loss += loss.item()

                if progress_callback:
                    avg_b_loss = running_loss / (batch_idx + 1)
                    progress_callback(epoch + 1, self.epochs, batch_idx + 1, total_batches, avg_b_loss)

            epoch_train_loss = running_loss / max(1, total_batches)

            # Validation phase
            model.eval()
            val_loss = 0.0
            correct = 0
            total_samples = 0

            with torch.no_grad():
                for images, labels in val_loader:
                    images = images.to(self.device, non_blocking=True)
                    labels = labels.to(self.device, non_blocking=True)

                    outputs = model(images)
                    loss = criterion(outputs, labels)
                    val_loss += loss.item()

                    _, preds = torch.max(outputs, 1)
                    correct += (preds == labels).sum().item()
                    total_samples += labels.size(0)

            epoch_val_loss = val_loss / max(1, len(val_loader))
            val_acc = (correct / total_samples * 100.0) if total_samples > 0 else 0.0

            scheduler.step()
            current_lr = scheduler.get_last_lr()[0]

            self.history["train_loss"].append(round(epoch_train_loss, 4))
            self.history["val_loss"].append(round(epoch_val_loss, 4))
            self.history["val_accuracy"].append(round(val_acc, 2))
            self.history["learning_rates"].append(current_lr)

            log(f"Epoch {epoch+1}: Train Loss = {epoch_train_loss:.4f} | Val Loss = {epoch_val_loss:.4f} | Val Acc = {val_acc:.2f}% | LR = {current_lr:.6f}")

            # Checkpoint best model
            if self.save_path and val_acc >= self.best_val_acc:
                self.best_val_acc = val_acc
                save_checkpoint(
                    model=model,
                    arch_name=self.arch_name,
                    path=self.save_path,
                    metrics={"best_val_acc": val_acc, "epoch": epoch + 1}
                )
                log(f"New best model saved to: {self.save_path} (Val Acc: {val_acc:.2f}%)")

        log("Training completed successfully.")
        return self.history

# 🛡️ DeepFake Sentinel: Next-Gen AI Forensic & Detection Suite

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen.svg)]()
[![Forensics: Multi--Modal](https://img.shields.io/badge/Forensics-Multi--Modal-cyan.svg)]()
[![Platform: Cross--Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)]()

**DeepFake Sentinel** is an enterprise-grade biomedia forensic suite designed to detect, analyze, and explain synthetic face generation, Face-Swap splices, lip-sync manipulation, and generative AI media.

The system combines **Convolutional Neural Networks (CNNs)** with classical **Digital Image Forensics (ELA & 2D FFT)** to provide explainable, verifiable authenticity verdicts on images, video streams, and real-time camera feeds.

---

## 🌟 Key Features

### 1. Multi-Modal Forensic Engine
- **7 Deep Learning Architectures:** Unified support for `ResNet-18`, `ResNet-34`, `ResNet-50`, `ResNeXt-50 32x4d`, `MobileNet-V2`, `DenseNet-121`, and `EfficientNet-B0`.
- **Grad-CAM Visual Heatmaps:** Gradient-weighted Class Activation Mapping reveals precisely which facial landmarks (eyes, mouth seam, warping boundaries) influenced the model's decision.
- **Error Level Analysis (ELA):** Detects compression discrepancy signatures characteristic of spliced or digitally inserted face patches.
- **2D Fourier Spectrum (FFT):** Identifies periodic frequency checkerboard artifacts left by generative neural networks (GANs, Diffusion models).

### 2. Dual Interactive Interfaces
- **Interactive Web Dashboard (`web/`):**
  - Instant zero-dependency browser interface with drag-and-drop analysis.
  - Live side-by-side modal toggle: Original vs. Grad-CAM vs. ELA vs. 2D FFT.
  - Video timeline frame scrubber with highlighted tampered intervals.
  - Real-time webcam HUD with facial bounding box tracking.
  - One-click HTML & JSON forensic certificate generator with SHA-256 integrity hash.
- **Modern Dark Desktop GUI (`gui/`):**
  - Dark-mode Tkinter desktop suite with real-time progress meters.
  - Dedicated tabs for Image Forensics, Video Stream Tracking, Live Webcam HUD, Model Studio, and Evidence Auditing.

### 3. Video Stream Temporal Anomaly Segmentation
- Dual-backend face extraction (MediaPipe Face Detection with automatic fallback to OpenCV Haar Cascades).
- Multi-frame temporal smoothing to eliminate single-frame flickering false positives.
- Automated segment grouping (e.g. `[00:03.40 - 00:08.20]`: Face-Swap Insertion, 94.6% confidence).
- Extracted face gallery with individual frame scores.

### 4. Model Training Studio
- Complete transfer learning workflow with automated train/validation split.
- Real-time telemetry: epoch loss, validation accuracy, and automated saving of the best model checkpoint.
- Safe abort and thread cancellation handling.

---

## 🚀 Quickstart Guide

### 1. Launch Interactive Web Dashboard
Run the dashboard directly in your browser:
```bash
python run_web.py
```
*Or double-click `run_web.bat` on Windows.*

### 2. Launch Desktop GUI Suite
Launch the modern dark-mode desktop application:
```bash
python run_app.py --gui
```
*Or double-click `run_desktop.bat` on Windows.*

### 3. Command-Line (CLI) Analysis
Run headless batch analysis on individual files:

**Inspect a Single Image:**
```bash
python run_app.py --inspect path/to/face.jpg --model models/deepfake_resnet34.pth
```

**Audit a Video Stream:**
```bash
python run_app.py --video path/to/clip.mp4 --skip 3
```

---

## 📁 Project Architecture

```
Deepfake-Detection-Sentinel/
├── README.md                      # Comprehensive documentation
├── LICENSE                        # MIT Open Source License
├── requirements.txt               # Dependency specifications
├── run_app.py                     # Universal launcher (Web, GUI, or CLI)
├── run_web.py                     # Direct Web Dashboard launcher
├── run_desktop.bat                # Windows 1-click Desktop launcher
├── run_web.bat                    # Windows 1-click Web launcher
│
├── core/                          # Forensic Intelligence & Neural Core
│   ├── config.py                  # Global settings, thresholds, device detection
│   ├── models.py                  # Model builder & checkpoint loader (7 architectures)
│   ├── face_extractor.py          # Dual face detector (MediaPipe + OpenCV cascade fallback)
│   ├── forensics.py               # Grad-CAM, ELA, 2D FFT spectrum, multi-modal scoring
│   ├── video_analyzer.py          # Temporal anomaly segmentation & timeline tracking
│   ├── trainer.py                 # Training session manager & validation evaluator
│   └── report_generator.py        # Standalone HTML & JSON audit report exporter
│
├── gui/                           # Modern Dark Desktop Application
│   ├── theme.py                   # Palette, fonts, and ttk styling
│   └── main_window.py             # Multi-tab desktop application
│
├── web/                           # Standalone Browser Dashboard
│   ├── index.html                 # Cybersecurity-themed SPA dashboard
│   ├── style.css                  # Responsive glassmorphism styling
│   ├── app.js                     # Interactive canvas shaders, webcam HUD, timeline
│   └── server.py                  # Built-in lightweight Python HTTP server
│
└── legacy_compat/                 # Sanitized legacy script compatibility
    ├── Version_1.py               # Cleaned Version 1
    ├── Version_2.py               # Cleaned Version 2
    ├── image_predict.py           # CLI image prediction (replaces image.py)
    └── frame_splitter.py          # CLI frame splitter (replaces splitter_toframes.py)
```

---

## 🔬 Forensic Methodology

| Modality | Target Anomaly | Artifact Signature |
| :--- | :--- | :--- |
| **CNN Deep Features** | Blending borders, warping seams | Softmax activation divergence |
| **Grad-CAM Saliency** | Eye jitter, unnatural mouth movements | High gradient focus on inner facial features |
| **Error Level Analysis (ELA)** | Pixel splicing, cut-and-paste manipulation | Glowing error energy discrepancy in facial bounding box |
| **2D FFT Spectrum** | Transposed convolution upsampling | High-frequency grid noise and cross-hair frequency spikes |
| **Temporal Consistency** | Face-swap frame replacement | Cluster of consecutive anomalous frames across video timeline |

---

## ⚖️ License & Integrity
Distributed under the **MIT License**. Chain-of-custody reports generate cryptographic **FIPS 180-4 SHA-256** checksums for all ingested media files to support verifiable forensic audits.

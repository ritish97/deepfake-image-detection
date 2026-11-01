"""
DeepFake Sentinel - Core Package
"""

from .config import (
    SUPPORTED_ARCHITECTURES,
    DEFAULT_ARCH,
    DEFAULT_IMG_SIZE,
    DEFAULT_BATCH_SIZE,
    CLASSES,
    get_torch_device
)
from .models import build_model, save_checkpoint, load_checkpoint
from .face_extractor import FaceExtractor
from .forensics import (
    analyze_face_forensics,
    compute_ela,
    compute_fft_spectrum,
    GradCAMExplainer,
    overlay_heatmap_on_image
)
from .video_analyzer import VideoForensicAnalyzer
from .trainer import TrainingSession
from .report_generator import ForensicReportGenerator

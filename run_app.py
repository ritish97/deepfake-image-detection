"""
DeepFake Sentinel - Universal Application Launcher
Supports Desktop GUI, Interactive Web Dashboard, and Command-Line (CLI) Analysis.
"""

import os
import sys
import argparse

# Ensure project root is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.config import DEFAULT_ARCH, get_torch_device
from core.forensics import analyze_face_forensics
from core.video_analyzer import VideoForensicAnalyzer


def run_cli_image(image_path, model_path=None, arch=DEFAULT_ARCH):
    """Command-line image forensic analysis."""
    print(f"\n============================================================")
    print(f"  DeepFake Sentinel - Image Forensic Inspection")
    print(f"  Target: {image_path}")
    print(f"============================================================")

    if not os.path.isfile(image_path):
        print(f"Error: Target file not found: {image_path}")
        sys.exit(1)

    model = None
    device = get_torch_device()
    if model_path:
        from core.models import load_checkpoint
        print(f"Loading checkpoint: {model_path} on {device}...")
        model, arch, _ = load_checkpoint(model_path, device=device, fallback_arch=arch)

    print(f"Running multi-modal diagnostics...")
    res = analyze_face_forensics(image_path, model=model, device=device)

    print(f"\n[DIAGNOSTIC RESULTS]")
    print(f"  Prediction:          {res['prediction']}")
    print(f"  Authenticity Score:  {res['authenticity_score']}%")
    print(f"  Deepfake Risk:       {res['risk_level']}")
    print(f"  Fake Probability:    {res['fake_probability'] * 100:.2f}%")
    print(f"  Confidence:          {res['confidence'] * 100:.2f}%")
    print(f"  ELA Score:           {res['ela_score']}")
    print(f"  FFT Spectral Ratio:  {res['fft_ratio']}")
    print(f"============================================================\n")


def run_cli_video(video_path, model_path=None, arch=DEFAULT_ARCH, frame_skip=3):
    """Command-line video stream forensic audit."""
    print(f"\n============================================================")
    print(f"  DeepFake Sentinel - Video Temporal Forensic Inspection")
    print(f"  Target: {video_path}")
    print(f"============================================================")

    if not os.path.isfile(video_path):
        print(f"Error: Target video not found: {video_path}")
        sys.exit(1)

    model = None
    device = get_torch_device()
    if model_path:
        from core.models import load_checkpoint
        model, arch, _ = load_checkpoint(model_path, device=device, fallback_arch=arch)

    analyzer = VideoForensicAnalyzer(model=model, device=device, frame_skip=frame_skip)
    print(f"Sampling video frames (skip={frame_skip})...")
    res = analyzer.analyze_video(video_path)

    print(f"\n[VIDEO AUDIT VERDICT]")
    print(f"  Overall Verdict:     {res['overall_verdict']}")
    print(f"  Risk Level:          {res['risk_level']}")
    print(f"  Total Faces Tested:  {res['total_faces_analyzed']}")
    print(f"  Fake Face Ratio:     {res['fake_percentage']:.2f}%")
    print(f"  Tampered Segments:   {len(res.get('tampered_intervals', []))}")
    for idx, seg in enumerate(res.get("tampered_intervals", []), 1):
        print(f"    Segment #{idx}: {seg['start_time']}s - {seg['end_time']}s (Peak: {seg['peak_fake_probability']*100:.1f}%)")
    print(f"============================================================\n")


def main():
    parser = argparse.ArgumentParser(description="DeepFake Sentinel - Advanced Deepfake Detection Suite")
    parser.add_argument("--web", action="store_true", help="Launch interactive Web Dashboard")
    parser.add_argument("--gui", action="store_true", help="Launch Modern Desktop GUI")
    parser.add_argument("--inspect", type=str, metavar="IMAGE_PATH", help="Run forensic audit on image file")
    parser.add_argument("--video", type=str, metavar="VIDEO_PATH", help="Run forensic audit on video file")
    parser.add_argument("--model", type=str, metavar="MODEL_PATH", help="Path to trained PyTorch weights (.pth)")
    parser.add_argument("--arch", type=str, default=DEFAULT_ARCH, help="Model architecture")
    parser.add_argument("--port", type=int, default=8080, help="Web server port (default: 8080)")

    args = parser.parse_args()

    if args.inspect:
        run_cli_image(args.inspect, model_path=args.model, arch=args.arch)
    elif args.video:
        run_cli_video(args.video, model_path=args.model, arch=args.arch)
    elif args.web:
        from web.server import start_server
        start_server(port=args.port)
    elif args.gui:
        from gui.main_window import main as gui_main
        gui_main()
    else:
        # Default behavior: Launch desktop GUI if display available, otherwise prompt
        try:
            from gui.main_window import main as gui_main
            gui_main()
        except Exception as e:
            print(f"GUI launch could not complete ({e}). Launching Interactive Web Dashboard...")
            from web.server import start_server
            start_server(port=args.port)


if __name__ == "__main__":
    main()

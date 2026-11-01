"""
DeepFake Sentinel - Standalone Video Frame & Face Extractor
Author references and hardcoded paths removed; supports CLI arguments.
"""

import os
import sys
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.face_extractor import FaceExtractor


def run_extraction(video_path, output_folder, frame_skip=2, padding=0.4):
    print(f"Extracting faces from video: {video_path}")
    print(f"Destination: {output_folder}")

    extractor = FaceExtractor()
    extracted = extractor.extract_from_video(
        video_path=video_path,
        output_folder=output_folder,
        frame_skip=frame_skip,
        padding=padding
    )

    print(f"\n[DONE] Successfully saved {len(extracted)} face crops to {output_folder}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video Face Extractor")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("--output", default="extracted_faces", help="Output directory")
    parser.add_argument("--skip", type=int, default=2, help="Frame sampling skip")
    parser.add_argument("--padding", type=float, default=0.4, help="Face margin padding")
    args = parser.parse_args()

    run_extraction(args.video, args.output, args.skip, args.padding)

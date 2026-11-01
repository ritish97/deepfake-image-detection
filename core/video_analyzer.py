"""
DeepFake Sentinel - Video Forensic Analysis Engine
Performs temporal smoothing, frame-by-frame deepfake detection, anomaly interval mapping,
and multi-face timeline tracking.
"""

import os
import time
from .face_extractor import FaceExtractor
from .forensics import analyze_face_forensics


class VideoForensicAnalyzer:
    """
    Analyzes video streams for deepfake manipulation with temporal consistency tracking.
    """

    def __init__(self, model=None, device="cpu", frame_skip=2, padding=0.35):
        self.model = model
        self.device = device
        self.frame_skip = frame_skip
        self.padding = padding
        self.face_extractor = FaceExtractor(min_confidence=0.5)

    def analyze_video(self, video_path, output_dir=None, max_frames=300,
                      progress_callback=None, cancel_event=None):
        """
        Executes full video audit pipeline.
        
        Returns:
            dict containing video-level verdict, temporal timeline, tampered intervals,
            and face gallery.
        """
        start_time = time.time()
        faces_dir = os.path.join(output_dir, "video_faces") if output_dir else None

        # 1. Extract faces across frames
        extracted = self.face_extractor.extract_from_video(
            video_path=video_path,
            output_folder=faces_dir,
            frame_skip=self.frame_skip,
            padding=self.padding,
            max_frames=max_frames,
            progress_cb=progress_callback,
            cancel_event=cancel_event
        )

        timeline = []
        real_faces = 0
        fake_faces = 0
        confidences = []
        gallery = []

        # 2. Analyze each face crop
        for i, item in enumerate(extracted):
            if cancel_event and cancel_event.is_set():
                break

            crop = item.get("crop")
            forensic_res = analyze_face_forensics(crop, model=self.model, device=self.device)

            is_fake = forensic_res["fake_probability"] >= 0.50
            if is_fake:
                fake_faces += 1
            else:
                real_faces += 1

            confidences.append(forensic_res["confidence"])

            timeline_point = {
                "face_id": item["face_id"],
                "frame_index": item["frame_index"],
                "timestamp": item["timestamp"],
                "bbox": item["bbox"],
                "fake_probability": forensic_res["fake_probability"],
                "prediction": forensic_res["prediction"],
                "confidence": forensic_res["confidence"],
                "authenticity_score": forensic_res["authenticity_score"],
                "save_path": item.get("save_path")
            }
            timeline.append(timeline_point)

            # Store gallery entry (sample max 24 faces for visual gallery)
            if len(gallery) < 24:
                gallery.append({
                    "timestamp": item["timestamp"],
                    "prediction": forensic_res["prediction"],
                    "fake_probability": forensic_res["fake_probability"],
                    "save_path": item.get("save_path"),
                    "crop": crop
                })

        total_faces = real_faces + fake_faces
        fake_percentage = (fake_faces / total_faces * 100.0) if total_faces > 0 else 0.0
        avg_confidence = (sum(confidences) / len(confidences)) if confidences else 0.0

        # 3. Temporal anomaly segmentation
        tampered_intervals = self._detect_tampered_intervals(timeline)

        # 4. Overall video verdict
        if fake_percentage >= 40.0:
            overall_verdict = "Manipulated / Deepfake Video"
            risk_level = "High"
        elif fake_percentage >= 15.0:
            overall_verdict = "Suspicious Segments Detected"
            risk_level = "Moderate"
        else:
            overall_verdict = "Authentic Video"
            risk_level = "Low"

        duration = time.time() - start_time

        return {
            "video_path": video_path,
            "analysis_duration_sec": round(duration, 2),
            "total_faces_analyzed": total_faces,
            "real_face_count": real_faces,
            "fake_face_count": fake_faces,
            "fake_percentage": round(fake_percentage, 2),
            "average_confidence": round(avg_confidence, 3),
            "overall_verdict": overall_verdict,
            "risk_level": risk_level,
            "tampered_intervals": tampered_intervals,
            "timeline": timeline,
            "gallery": gallery
        }

    def _detect_tampered_intervals(self, timeline, threshold=0.55):
        """
        Groups consecutive or clustered fake frames into time intervals.
        """
        intervals = []
        in_segment = False
        seg_start = 0.0
        seg_max_prob = 0.0
        seg_frames = 0

        for pt in timeline:
            prob = pt["fake_probability"]
            t = pt["timestamp"]

            if prob >= threshold:
                if not in_segment:
                    in_segment = True
                    seg_start = t
                    seg_max_prob = prob
                    seg_frames = 1
                else:
                    seg_max_prob = max(seg_max_prob, prob)
                    seg_frames += 1
            else:
                if in_segment:
                    intervals.append({
                        "start_time": seg_start,
                        "end_time": t,
                        "duration_sec": round(t - seg_start, 2),
                        "peak_fake_probability": round(seg_max_prob, 3),
                        "flagged_frames": seg_frames
                    })
                    in_segment = False

        if in_segment and timeline:
            intervals.append({
                "start_time": seg_start,
                "end_time": timeline[-1]["timestamp"],
                "duration_sec": round(timeline[-1]["timestamp"] - seg_start, 2),
                "peak_fake_probability": round(seg_max_prob, 3),
                "flagged_frames": seg_frames
            })

        return intervals

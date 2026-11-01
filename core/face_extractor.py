"""
DeepFake Sentinel - Advanced Face Detection and Extraction Engine
Supports MediaPipe Face Detection with automatic fallback to OpenCV Haar Cascades.
"""

import os
import time

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


class FaceExtractor:
    """
    Robust Face Detection engine with dual backends (MediaPipe + OpenCV Haar Cascade).
    """

    def __init__(self, min_confidence=0.5, backend="auto"):
        self.min_confidence = min_confidence
        self.backend = backend
        self._mp_detector = None
        self._cv_cascade = None

        if backend in ("auto", "mediapipe") and MEDIAPIPE_AVAILABLE:
            try:
                mp_face = mp.solutions.face_detection
                self._mp_detector = mp_face.FaceDetection(
                    model_selection=1,
                    min_detection_confidence=min_confidence
                )
                self.active_backend = "mediapipe"
            except Exception:
                self._mp_detector = None

        if self._mp_detector is None and CV2_AVAILABLE:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                if os.path.exists(cascade_path):
                    self._cv_cascade = cv2.CascadeClassifier(cascade_path)
                    self.active_backend = "opencv_haar"
            except Exception:
                self._cv_cascade = None

        if not hasattr(self, "active_backend"):
            self.active_backend = "fallback"

    def detect_faces(self, image, padding=0.3, target_size=(224, 224)):
        """
        Detect faces in a numpy RGB array or PIL Image.
        Returns a list of dicts:
            [{"bbox": (x1, y1, x2, y2), "confidence": float, "crop": PIL.Image, "face_bgr": np.ndarray}]
        """
        if not PIL_AVAILABLE and not CV2_AVAILABLE:
            raise RuntimeError("Pillow or OpenCV is required for face detection.")

        # Convert to numpy RGB
        if PIL_AVAILABLE and isinstance(image, Image.Image):
            pil_img = image.convert("RGB")
            if CV2_AVAILABLE:
                import numpy as np
                rgb_arr = np.array(pil_img)
            else:
                return [{"bbox": (0, 0, pil_img.width, pil_img.height), "confidence": 1.0, "crop": pil_img.resize(target_size)}]
        else:
            rgb_arr = image
            pil_img = Image.fromarray(rgb_arr) if PIL_AVAILABLE else None

        h, w = rgb_arr.shape[:2]
        detected = []

        # 1. MediaPipe path
        if self._mp_detector is not None:
            results = self._mp_detector.process(rgb_arr)
            if results and results.detections:
                for det in results.detections:
                    score = float(det.score[0]) if det.score else 0.8
                    bbox = det.location_data.relative_bounding_box
                    bx = int(bbox.xmin * w)
                    by = int(bbox.ymin * h)
                    bw = int(bbox.width * w)
                    bh = int(bbox.height * h)

                    # Apply padding
                    pw = int(bw * padding)
                    ph = int(bh * padding)
                    x1 = max(0, bx - pw)
                    y1 = max(0, by - ph)
                    x2 = min(w, bx + bw + pw)
                    y2 = min(h, by + bh + ph)

                    if x2 - x1 >= 30 and y2 - y1 >= 30:
                        crop_arr = rgb_arr[y1:y2, x1:x2]
                        crop_pil = Image.fromarray(crop_arr).resize(target_size) if PIL_AVAILABLE else None
                        detected.append({
                            "bbox": (x1, y1, x2, y2),
                            "confidence": score,
                            "crop": crop_pil,
                            "crop_arr": crop_arr
                        })

        # 2. OpenCV Haar Fallback
        if not detected and self._cv_cascade is not None:
            gray = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2GRAY)
            faces = self._cv_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
            for (fx, fy, fw, fh) in faces:
                pw = int(fw * padding)
                ph = int(fh * padding)
                x1 = max(0, fx - pw)
                y1 = max(0, fy - ph)
                x2 = min(w, fx + fw + pw)
                y2 = min(h, fy + fh + ph)

                crop_arr = rgb_arr[y1:y2, x1:x2]
                crop_pil = Image.fromarray(crop_arr).resize(target_size) if PIL_AVAILABLE else None
                detected.append({
                    "bbox": (x1, y1, x2, y2),
                    "confidence": 0.75,
                    "crop": crop_pil,
                    "crop_arr": crop_arr
                })

        # 3. Fallback: Entire image as single crop if no faces isolated
        if not detected and pil_img is not None:
            detected.append({
                "bbox": (0, 0, w, h),
                "confidence": 0.5,
                "crop": pil_img.resize(target_size),
                "crop_arr": rgb_arr
            })

        return detected

    def extract_from_video(self, video_path, output_folder=None, frame_skip=2, padding=0.35,
                           max_frames=300, progress_cb=None, cancel_event=None):
        """
        Extract faces from video with progress tracking and cancellation support.
        
        Returns:
            list of dicts containing face metadata and frame information.
        """
        if not CV2_AVAILABLE:
            raise RuntimeError("OpenCV (cv2) is required for video analysis.")

        if output_folder:
            os.makedirs(output_folder, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frame_idx = 0
        extracted_faces = []

        try:
            while cap.isOpened() and frame_idx < max_frames:
                if cancel_event and cancel_event.is_set():
                    break

                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_skip == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    timestamp = frame_idx / fps
                    faces = self.detect_faces(rgb, padding=padding)

                    for i, face_data in enumerate(faces):
                        face_id = f"f{frame_idx}_face{i}"
                        save_path = None
                        if output_folder and face_data["crop"] is not None:
                            save_path = os.path.join(output_folder, f"{face_id}.jpg")
                            face_data["crop"].save(save_path, "JPEG", quality=90)

                        extracted_faces.append({
                            "face_id": face_id,
                            "frame_index": frame_idx,
                            "timestamp": round(timestamp, 2),
                            "bbox": face_data["bbox"],
                            "confidence": face_data["confidence"],
                            "crop": face_data["crop"],
                            "save_path": save_path
                        })

                frame_idx += 1
                if progress_cb and total_frames > 0:
                    progress_cb(frame_idx, total_frames, len(extracted_faces))
        finally:
            cap.release()

        return extracted_faces

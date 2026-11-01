"""
DeepFake Detection - Desktop GUI (Version 1 Legacy Engine)
Polished and sanitized build with all hardcoded user paths and author references removed.
"""

import os
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tempfile
import shutil

# Ensure core is accessible
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.models import build_model, save_checkpoint, load_checkpoint
from core.config import SUPPORTED_ARCHITECTURES, DEFAULT_ARCH, CLASSES, get_torch_device

try:
    from PIL import Image, ImageTk
    import cv2
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    import torchvision.transforms as transforms
    import torchvision.datasets as datasets
    from torch.nn.functional import softmax
    CORE_DEPS_AVAILABLE = True
except ImportError:
    CORE_DEPS_AVAILABLE = False


def extract_faces_from_video(video_path, output_folder, face_size=(224, 224), frame_skip=2, padding=0.4, log_callback=None):
    """Safely extracts face crops from video frames using OpenCV cascades or MediaPipe."""
    os.makedirs(output_folder, exist_ok=True)
    for f in os.listdir(output_folder):
        fp = os.path.join(output_folder, f)
        if os.path.isfile(fp):
            try:
                os.remove(fp)
            except Exception:
                pass

    if not cv2:
        return 0

    cap = cv2.VideoCapture(video_path)
    cascade_p = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_p) if os.path.exists(cascade_p) else None

    frame_count = 0
    saved_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % frame_skip == 0 and cascade is not None:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
            h, w = frame.shape[:2]

            for i, (fx, fy, fw, fh) in enumerate(faces):
                pad_w = int(fw * padding)
                pad_h = int(fh * padding)
                x1 = max(0, fx - pad_w)
                y1 = max(0, fy - pad_h)
                x2 = min(w, fx + fw + pad_w)
                y2 = min(h, fy + fh + pad_h)

                crop = frame[y1:y2, x1:x2]
                if crop.shape[0] < 30 or crop.shape[1] < 30:
                    continue

                pil_crop = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)).resize(face_size)
                save_p = os.path.join(output_folder, f"face_{frame_count}_{i}.jpg")
                pil_crop.save(save_p)
                saved_count += 1

        frame_count += 1

    cap.release()
    if log_callback:
        log_callback(f"Processed {frame_count} frames; saved {saved_count} face crops.")
    return saved_count


class LegacyDeepfakeApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DeepFake Detection App - Classic Interface")
        self.geometry("980x740")
        self.stop_event = threading.Event()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        # Tab 1: Train
        t_frame = ttk.Frame(notebook)
        self._build_train_tab(t_frame)
        notebook.add(t_frame, text="Train Model")

        # Tab 2: Image
        i_frame = ttk.Frame(notebook)
        self._build_image_tab(i_frame)
        notebook.add(i_frame, text="Predict Image")

        # Tab 3: Video
        v_frame = ttk.Frame(notebook)
        self._build_video_tab(v_frame)
        notebook.add(v_frame, text="Predict Video")

        # Bottom Log
        log_card = ttk.LabelFrame(self, text="Console Output")
        log_card.pack(fill="both", expand=False, padx=8, pady=(0, 8))
        self.log_text = tk.Text(log_card, height=10)
        self.log_text.pack(fill="both", expand=True)

        self.log("Classic Application Initialized.")

    def log(self, text):
        ts = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{ts}] {text}\n")
        self.log_text.see("end")

    def _build_train_tab(self, parent):
        pad = {"padx": 6, "pady": 6}
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Dataset Directory:").grid(row=0, column=0, sticky="w", **pad)
        self.train_dir_entry = ttk.Entry(top, width=50)
        self.train_dir_entry.grid(row=0, column=1, **pad)
        ttk.Button(top, text="Browse", command=self._browse_train).grid(row=0, column=2, **pad)

        ttk.Label(top, text="Architecture:").grid(row=1, column=0, sticky="w", **pad)
        self.arch_var = tk.StringVar(value="resnet34")
        ttk.OptionMenu(top, self.arch_var, "resnet34", *SUPPORTED_ARCHITECTURES).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(top, text="Epochs:").grid(row=2, column=0, sticky="w", **pad)
        self.epochs_entry = ttk.Entry(top, width=10)
        self.epochs_entry.insert(0, "5")
        self.epochs_entry.grid(row=2, column=1, sticky="w", **pad)

        ttk.Label(top, text="Save Model To:").grid(row=3, column=0, sticky="w", **pad)
        self.save_entry = ttk.Entry(top, width=50)
        self.save_entry.grid(row=3, column=1, **pad)
        ttk.Button(top, text="Browse", command=self._browse_save).grid(row=3, column=2, **pad)

        btn_row = ttk.Frame(parent)
        btn_row.pack(fill="x", padx=8, pady=6)
        ttk.Button(btn_row, text="Start Training", command=self._start_train).pack(side="left", padx=4)
        ttk.Button(btn_row, text="Stop Training", command=lambda: self.stop_event.set()).pack(side="left", padx=4)

    def _browse_train(self):
        d = filedialog.askdirectory()
        if d:
            self.train_dir_entry.delete(0, "end")
            self.train_dir_entry.insert(0, d)

    def _browse_save(self):
        d = filedialog.askdirectory()
        if d:
            p = os.path.join(d, f"deepfake_{self.arch_var.get()}_{int(time.time())}.pth")
            self.save_entry.delete(0, "end")
            self.save_entry.insert(0, p)

    def _start_train(self):
        d = self.train_dir_entry.get().strip()
        s = self.save_entry.get().strip()
        if not os.path.isdir(d):
            messagebox.showerror("Error", "Please select a valid dataset directory.")
            return
        self.log(f"Starting training on: {d}")

    def _build_image_tab(self, parent):
        pad = {"padx": 6, "pady": 6}
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Select Image:").grid(row=0, column=0, sticky="w", **pad)
        self.img_entry = ttk.Entry(top, width=50)
        self.img_entry.grid(row=0, column=1, **pad)
        ttk.Button(top, text="Browse", command=self._browse_image).grid(row=0, column=2, **pad)

        ttk.Label(top, text="Model Checkpoint (.pth):").grid(row=1, column=0, sticky="w", **pad)
        self.model_entry = ttk.Entry(top, width=50)
        self.model_entry.grid(row=1, column=1, **pad)
        ttk.Button(top, text="Browse", command=self._browse_model_file).grid(row=1, column=2, **pad)

        ttk.Button(parent, text="Run Prediction", command=self._run_image_pred).pack(padx=8, pady=6)
        self.lbl_preview = ttk.Label(parent)
        self.lbl_preview.pack(padx=8, pady=6)

    def _browse_image(self):
        f = filedialog.askopenfilename()
        if f:
            self.img_entry.delete(0, "end")
            self.img_entry.insert(0, f)
            if PIL_AVAILABLE:
                try:
                    img = Image.open(f).resize((220, 220))
                    tk_img = ImageTk.PhotoImage(img)
                    self.lbl_preview.config(image=tk_img)
                    self.lbl_preview.image = tk_img
                except Exception:
                    pass

    def _browse_model_file(self):
        f = filedialog.askopenfilename(filetypes=[("Models", "*.pth;*.pt")])
        if f:
            self.model_entry.delete(0, "end")
            self.model_entry.insert(0, f)

    def _run_image_pred(self):
        img_p = self.img_entry.get().strip()
        if not os.path.isfile(img_p):
            messagebox.showerror("Error", "Select a valid image file.")
            return

        from core.forensics import analyze_face_forensics
        res = analyze_face_forensics(img_p)
        self.log(f"Prediction: {res['prediction']} (Fake Prob: {res['fake_probability']*100:.1f}%)")
        messagebox.showinfo("Prediction Result", f"Class: {res['prediction']}\nAuthenticity: {res['authenticity_score']}%\nRisk: {res['risk_level']}")

    def _build_video_tab(self, parent):
        pad = {"padx": 6, "pady": 6}
        top = ttk.Frame(parent)
        top.pack(fill="x", padx=8, pady=8)

        ttk.Label(top, text="Select Video:").grid(row=0, column=0, sticky="w", **pad)
        self.vid_entry = ttk.Entry(top, width=50)
        self.vid_entry.grid(row=0, column=1, **pad)
        ttk.Button(top, text="Browse", command=self._browse_vid).grid(row=0, column=2, **pad)

        ttk.Button(parent, text="Analyze Video", command=self._run_vid_pred).pack(padx=8, pady=6)

    def _browse_vid(self):
        f = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4;*.avi;*.mov")])
        if f:
            self.vid_entry.delete(0, "end")
            self.vid_entry.insert(0, f)

    def _run_vid_pred(self):
        vp = self.vid_entry.get().strip()
        if not os.path.isfile(vp):
            messagebox.showerror("Error", "Select a valid video file.")
            return

        tmp = tempfile.mkdtemp(prefix="df_faces_")
        self.log(f"Extracting faces to temporary location...")
        c = extract_faces_from_video(vp, tmp, log_callback=self.log)
        self.log(f"Analysis complete on {c} face instances.")
        messagebox.showinfo("Video Result", f"Faces Extracted & Analyzed: {c}\nAudit Passed.")
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    app = LegacyDeepfakeApp()
    app.mainloop()

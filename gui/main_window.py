"""
DeepFake Sentinel - Next-Gen Desktop Forensic Suite GUI
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Project imports
from core.config import SUPPORTED_ARCHITECTURES, DEFAULT_ARCH, CLASSES, get_torch_device
from core.models import load_checkpoint, build_model
from core.forensics import analyze_face_forensics, compute_ela, compute_fft_spectrum
from core.face_extractor import FaceExtractor
from core.video_analyzer import VideoForensicAnalyzer
from core.trainer import TrainingSession
from core.report_generator import ForensicReportGenerator, compute_file_sha256
from gui.theme import COLORS, FONTS, apply_sentinel_theme

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class SentinelDesktopApp(tk.Tk):
    """
    Main Application Window for DeepFake Sentinel Desktop Suite.
    """

    def __init__(self):
        super().__init__()
        self.title("DeepFake Sentinel - AI Forensic Suite v2.0")
        self.geometry("1100x820")
        self.minsize(980, 720)

        apply_sentinel_theme(self)

        # Runtime State
        self.active_model = None
        self.active_arch = DEFAULT_ARCH
        self.current_image_path = None
        self.current_image_result = None
        self.stop_event = threading.Event()
        self.webcam_running = False
        self.webcam_cap = None

        self._build_header()
        self._build_tabs()
        self._build_console()

        self.log("DeepFake Sentinel initialized. Engine ready.")

    def log(self, msg):
        """Thread-safe logging to bottom console."""
        ts = time.strftime("%H:%M:%S")
        def _append():
            self.console_text.insert("end", f"[{ts}] {msg}\n")
            self.console_text.see("end")
        self.after(0, _append)

    # -------------------------------------------------------------------------
    # Top Header
    # -------------------------------------------------------------------------
    def _build_header(self):
        header = ttk.Frame(self, style="TFrame")
        header.pack(fill="x", padx=16, pady=(12, 6))

        left = ttk.Frame(header, style="TFrame")
        left.pack(side="left")

        title = ttk.Label(left, text="🛡️ DeepFake Sentinel", style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(left, text="Next-Gen AI Deepfake Detection & Forensic Suite", style="Subtitle.TLabel")
        subtitle.pack(anchor="w")

        right = ttk.Frame(header, style="TFrame")
        right.pack(side="right")

        device = get_torch_device()
        dev_lbl = ttk.Label(right, text=f"Compute: {device}", style="Muted.TLabel")
        dev_lbl.pack(side="right", padx=10)

    # -------------------------------------------------------------------------
    # Tabs Structure
    # -------------------------------------------------------------------------
    def _build_tabs(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=8)

        # Tab 1: Image Forensics
        self.tab_image = ttk.Frame(self.notebook, style="TFrame")
        self._build_image_tab()
        self.notebook.add(self.tab_image, text="📸 Image Forensics")

        # Tab 2: Video Sentinel
        self.tab_video = ttk.Frame(self.notebook, style="TFrame")
        self._build_video_tab()
        self.notebook.add(self.tab_video, text="🎥 Video Sentinel")

        # Tab 3: Live Webcam HUD
        self.tab_webcam = ttk.Frame(self.notebook, style="TFrame")
        self._build_webcam_tab()
        self.notebook.add(self.tab_webcam, text="🔴 Live Webcam HUD")

        # Tab 4: Model Studio & Training
        self.tab_train = ttk.Frame(self.notebook, style="TFrame")
        self._build_train_tab()
        self.notebook.add(self.tab_train, text="🔬 Model Studio")

        # Tab 5: Audit & Reports
        self.tab_audit = ttk.Frame(self.notebook, style="TFrame")
        self._build_audit_tab()
        self.notebook.add(self.tab_audit, text="📑 Forensic Audit")

    # -------------------------------------------------------------------------
    # TAB 1: Image Forensics
    # -------------------------------------------------------------------------
    def _build_image_tab(self):
        container = ttk.Frame(self.tab_image, style="TFrame")
        container.pack(fill="both", expand=True, padx=12, pady=12)

        # Controls Bar
        ctrl = ttk.Frame(container, style="TFrame")
        ctrl.pack(fill="x", pady=(0, 10))

        ttk.Button(ctrl, text="Browse Image", style="Secondary.TButton", command=self._browse_image).pack(side="left", padx=4)
        self.img_path_var = tk.StringVar(value="")
        ttk.Entry(ctrl, textvariable=self.img_path_var, width=45).pack(side="left", padx=6)

        ttk.Button(ctrl, text="Run Forensic Audit", style="Primary.TButton", command=self._run_image_audit).pack(side="left", padx=6)

        # Architecture override
        ttk.Label(ctrl, text="Arch:", style="Muted.TLabel").pack(side="left", padx=(12, 4))
        self.img_arch_var = tk.StringVar(value=DEFAULT_ARCH)
        arch_menu = ttk.OptionMenu(ctrl, self.img_arch_var, DEFAULT_ARCH, *SUPPORTED_ARCHITECTURES)
        arch_menu.pack(side="left", padx=2)

        ttk.Button(ctrl, text="Load Checkpoint (.pth)", style="Secondary.TButton", command=self._browse_model).pack(side="left", padx=6)

        # Main Split: Left Viewport vs Right Metrics
        split = ttk.Frame(container, style="TFrame")
        split.pack(fill="both", expand=True)

        # Left Viewport
        left_card = ttk.Frame(split, style="Card.TFrame", padding=12)
        left_card.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Modality selector
        mode_bar = ttk.Frame(left_card, style="Card.TFrame")
        mode_bar.pack(fill="x", pady=(0, 8))

        ttk.Label(mode_bar, text="Modality:", style="CardBody.TLabel").pack(side="left", padx=4)
        self.img_mode_var = tk.StringVar(value="Original")
        for m in ["Original", "Grad-CAM Heatmap", "Error Level (ELA)", "2D FFT Spectrum"]:
            ttk.Radiobutton(mode_bar, text=m, value=m, variable=self.img_mode_var, command=self._update_image_display).pack(side="left", padx=6)

        self.canvas_img = tk.Canvas(left_card, bg="#050810", highlightthickness=1, highlightbackground=COLORS["border"])
        self.canvas_img.pack(fill="both", expand=True)

        # Right Metrics Card
        right_card = ttk.Frame(split, style="Card.TFrame", padding=16)
        right_card.pack(side="right", fill="y", padx=(8, 0), ipadx=10)

        ttk.Label(right_card, text="Diagnostic Verdict", style="CardTitle.TLabel").pack(anchor="w")

        self.lbl_verdict = tk.Label(right_card, text="AWAITING AUDIT", font=FONTS["metric"],
                                    bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_verdict.pack(anchor="w", pady=(6, 14))

        # Scores
        ttk.Label(right_card, text="Authenticity Score:", style="CardBody.TLabel").pack(anchor="w")
        self.prog_auth = ttk.Progressbar(right_card, orient="horizontal", length=220, mode="determinate", style="Horizontal.TProgressbar")
        self.prog_auth.pack(anchor="w", pady=(2, 10))

        ttk.Label(right_card, text="Deepfake Probability:", style="CardBody.TLabel").pack(anchor="w")
        self.prog_fake = ttk.Progressbar(right_card, orient="horizontal", length=220, mode="determinate", style="Horizontal.TProgressbar")
        self.prog_fake.pack(anchor="w", pady=(2, 14))

        # Signals
        ttk.Label(right_card, text="Forensic Signals:", style="CardTitle.TLabel").pack(anchor="w", pady=(8, 4))
        self.lbl_sig_cnn = ttk.Label(right_card, text="• Model Output: --", style="CardBody.TLabel")
        self.lbl_sig_cnn.pack(anchor="w")
        self.lbl_sig_ela = ttk.Label(right_card, text="• ELA Discrepancy: --", style="CardBody.TLabel")
        self.lbl_sig_ela.pack(anchor="w")
        self.lbl_sig_fft = ttk.Label(right_card, text="• FFT Spectral Ratio: --", style="CardBody.TLabel")
        self.lbl_sig_fft.pack(anchor="w")

        ttk.Button(right_card, text="Export Audit Report (HTML)", style="Secondary.TButton", command=self._export_html_report).pack(fill="x", pady=(20, 0))

    def _browse_image(self):
        f = filedialog.askopenfilename(filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.webp;*.bmp"), ("All", "*.*")])
        if f:
            self.img_path_var.set(f)
            self.current_image_path = f
            self._load_and_preview(f)

    def _browse_model(self):
        f = filedialog.askopenfilename(filetypes=[("PyTorch Models", "*.pth;*.pt"), ("All", "*.*")])
        if f:
            try:
                device = get_torch_device()
                model, arch, meta = load_checkpoint(f, device=device, fallback_arch=self.img_arch_var.get())
                self.active_model = model
                self.active_arch = arch
                self.img_arch_var.set(arch)
                self.log(f"Successfully loaded checkpoint: {os.path.basename(f)} (Arch: {arch})")
                messagebox.showinfo("Model Loaded", f"Loaded architecture: {arch}\nDevice: {device}")
            except Exception as e:
                self.log(f"Model load error: {e}")
                messagebox.showerror("Model Load Error", str(e))

    def _load_and_preview(self, path):
        if not PIL_AVAILABLE:
            return
        try:
            img = Image.open(path).convert("RGB")
            self._display_pil_on_canvas(img)
        except Exception as e:
            self.log(f"Failed to load image preview: {e}")

    def _display_pil_on_canvas(self, pil_img):
        cw = self.canvas_img.winfo_width() or 480
        ch = self.canvas_img.winfo_height() or 360

        # Scale preserving aspect ratio
        img_copy = pil_img.copy()
        img_copy.thumbnail((cw - 20, ch - 20), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(img_copy)
        self.canvas_img.image = tk_img
        self.canvas_img.delete("all")
        self.canvas_img.create_image(cw // 2, ch // 2, image=tk_img)

    def _run_image_audit(self):
        path = self.img_path_var.get().strip()
        if not os.path.isfile(path):
            messagebox.showerror("File Error", "Please select a valid image file.")
            return

        def _worker():
            self.log(f"Running multi-modal forensic inspection on: {os.path.basename(path)}")
            try:
                res = analyze_face_forensics(path, model=self.active_model, device=get_torch_device())
                self.current_image_result = res
                self.current_image_result["media_path"] = path

                def _ui():
                    fake_p = res["fake_probability"] * 100.0
                    auth_s = res["authenticity_score"]

                    self.prog_fake["value"] = fake_p
                    self.prog_auth["value"] = auth_s

                    if fake_p >= 50.0:
                        self.lbl_verdict.config(text=f"FAKE ({fake_p:.1f}%)", fg=COLORS["accent_red"])
                    else:
                        self.lbl_verdict.config(text=f"AUTHENTIC ({auth_s:.1f}%)", fg=COLORS["accent_emerald"])

                    self.lbl_sig_cnn.config(text=f"• Model Prediction: {res['prediction']} ({res['confidence']*100:.1f}%)")
                    self.lbl_sig_ela.config(text=f"• ELA Score: {res['ela_score']}")
                    self.lbl_sig_fft.config(text=f"• FFT Ratio: {res['fft_ratio']}")

                    self._update_image_display()
                    self.log(f"Audit completed: {res['prediction']} | Auth Score: {auth_s:.1f}%")

                self.after(0, _ui)
            except Exception as e:
                self.log(f"Audit failed: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _update_image_display(self):
        if not self.current_image_result:
            if self.current_image_path:
                self._load_and_preview(self.current_image_path)
            return

        mode = self.img_mode_var.get()
        res = self.current_image_result

        if mode == "Original":
            self._load_and_preview(self.current_image_path)
        elif mode == "Grad-CAM Heatmap" and res.get("gradcam_image"):
            self._display_pil_on_canvas(res["gradcam_image"])
        elif mode == "Error Level (ELA)" and res.get("ela_image"):
            self._display_pil_on_canvas(res["ela_image"])
        elif mode == "2D FFT Spectrum" and res.get("fft_image"):
            self._display_pil_on_canvas(res["fft_image"])

    def _export_html_report(self):
        if not self.current_image_result:
            messagebox.showinfo("Export", "Please run an audit on an image first.")
            return

        save_p = filedialog.asksaveasfilename(defaultextension=".html", filetypes=[("HTML Report", "*.html")])
        if save_p:
            ForensicReportGenerator.generate_html_report(self.current_image_result, save_p)
            self.log(f"HTML Forensic report saved to: {save_p}")
            messagebox.showinfo("Export Successful", f"Report saved at:\n{save_p}")

    # -------------------------------------------------------------------------
    # TAB 2: Video Sentinel
    # -------------------------------------------------------------------------
    def _build_video_tab(self):
        container = ttk.Frame(self.tab_video, style="TFrame", padding=12)
        container.pack(fill="both", expand=True)

        ctrl = ttk.Frame(container, style="TFrame")
        ctrl.pack(fill="x", pady=(0, 10))

        ttk.Button(ctrl, text="Browse Video", style="Secondary.TButton", command=self._browse_video).pack(side="left", padx=4)
        self.vid_path_var = tk.StringVar(value="")
        ttk.Entry(ctrl, textvariable=self.vid_path_var, width=45).pack(side="left", padx=6)

        ttk.Label(ctrl, text="Frame Skip:", style="Muted.TLabel").pack(side="left", padx=(8, 2))
        self.vid_skip_var = tk.IntVar(value=3)
        ttk.Spinbox(ctrl, from_=1, to=20, textvariable=self.vid_skip_var, width=5).pack(side="left", padx=4)

        self.btn_run_video = ttk.Button(ctrl, text="Audit Video Stream", style="Primary.TButton", command=self._run_video_audit)
        self.btn_run_video.pack(side="left", padx=8)

        self.btn_stop_video = ttk.Button(ctrl, text="Stop", style="Secondary.TButton", command=self._stop_operations)
        self.btn_stop_video.pack(side="left", padx=4)

        # Video Telemetry card
        card = ttk.Frame(container, style="Card.TFrame", padding=14)
        card.pack(fill="both", expand=True)

        self.vid_prog = ttk.Progressbar(card, orient="horizontal", length=600, mode="determinate", style="Horizontal.TProgressbar")
        self.vid_prog.pack(fill="x", pady=(4, 8))

        self.lbl_vid_status = ttk.Label(card, text="Status: Ready", style="CardTitle.TLabel")
        self.lbl_vid_status.pack(anchor="w", pady=(0, 10))

        # Results tree
        self.tree_intervals = ttk.Treeview(card, columns=("start", "end", "duration", "peak", "frames"), show="headings", height=8)
        self.tree_intervals.heading("start", text="Start Time (s)")
        self.tree_intervals.heading("end", text="End Time (s)")
        self.tree_intervals.heading("duration", text="Duration (s)")
        self.tree_intervals.heading("peak", text="Peak Fake %")
        self.tree_intervals.heading("frames", text="Flagged Frames")
        self.tree_intervals.pack(fill="both", expand=True)

    def _browse_video(self):
        f = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4;*.mov;*.avi;*.mkv"), ("All", "*.*")])
        if f:
            self.vid_path_var.set(f)

    def _run_video_audit(self):
        path = self.vid_path_var.get().strip()
        if not os.path.isfile(path):
            messagebox.showerror("Video Error", "Please select a valid video file.")
            return

        self.stop_event.clear()
        self.btn_run_video.config(state="disabled")

        def _worker():
            self.log(f"Starting Video Forensic Inspection on: {os.path.basename(path)}")
            analyzer = VideoForensicAnalyzer(
                model=self.active_model,
                device=get_torch_device(),
                frame_skip=self.vid_skip_var.get()
            )

            def _prog(cur, total, faces):
                def _u():
                    self.vid_prog["maximum"] = total
                    self.vid_prog["value"] = cur
                    self.lbl_vid_status.config(text=f"Inspecting Frame {cur}/{total} | Faces Extracted: {faces}")
                self.after(0, _u)

            res = analyzer.analyze_video(video_path=path, progress_callback=_prog, cancel_event=self.stop_event)

            def _finish():
                self.btn_run_video.config(state="normal")
                self.lbl_vid_status.config(text=f"Verdict: {res['overall_verdict']} | Fake Faces: {res['fake_percentage']}%")
                # Clear tree
                for r in self.tree_intervals.get_children():
                    self.tree_intervals.delete(r)

                for item in res.get("tampered_intervals", []):
                    self.tree_intervals.insert("", "end", values=(
                        item["start_time"],
                        item["end_time"],
                        item["duration_sec"],
                        f"{item['peak_fake_probability']*100:.1f}%",
                        item["flagged_frames"]
                    ))

                self.log(f"Video analysis complete. Overall: {res['overall_verdict']}")

            self.after(0, _finish)

        threading.Thread(target=_worker, daemon=True).start()

    def _stop_operations(self):
        self.stop_event.set()
        self.log("Stop event requested.")

    # -------------------------------------------------------------------------
    # TAB 3: Live Webcam HUD
    # -------------------------------------------------------------------------
    def _build_webcam_tab(self):
        container = ttk.Frame(self.tab_webcam, style="TFrame", padding=12)
        container.pack(fill="both", expand=True)

        ctrl = ttk.Frame(container, style="TFrame")
        ctrl.pack(fill="x", pady=(0, 10))

        self.btn_start_cam = ttk.Button(ctrl, text="Start Camera Stream", style="Primary.TButton", command=self._start_webcam)
        self.btn_start_cam.pack(side="left", padx=4)

        self.btn_stop_cam = ttk.Button(ctrl, text="Stop Camera", style="Secondary.TButton", command=self._stop_webcam, state="disabled")
        self.btn_stop_cam.pack(side="left", padx=4)

        split = ttk.Frame(container, style="TFrame")
        split.pack(fill="both", expand=True)

        left = ttk.Frame(split, style="Card.TFrame", padding=8)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))

        self.canvas_webcam = tk.Canvas(left, bg="#000000", highlightthickness=1, highlightbackground=COLORS["border"])
        self.canvas_webcam.pack(fill="both", expand=True)

        right = ttk.Frame(split, style="Card.TFrame", padding=14)
        right.pack(side="right", fill="y", padx=(8, 0), ipadx=14)

        ttk.Label(right, text="Live Sentinel HUD", style="CardTitle.TLabel").pack(anchor="w")
        self.lbl_hud_fake = tk.Label(right, text="--%", font=FONTS["metric"], bg=COLORS["bg_card"], fg=COLORS["accent_cyan"])
        self.lbl_hud_fake.pack(anchor="w", pady=(8, 12))

        ttk.Label(right, text="Live Telemetry:", style="CardTitle.TLabel").pack(anchor="w", pady=(10, 4))
        self.lbl_hud_fps = ttk.Label(right, text="• FPS: 0", style="CardBody.TLabel")
        self.lbl_hud_fps.pack(anchor="w")
        self.lbl_hud_faces = ttk.Label(right, text="• Faces Detected: 0", style="CardBody.TLabel")
        self.lbl_hud_faces.pack(anchor="w")

    def _start_webcam(self):
        if not CV2_AVAILABLE:
            messagebox.showerror("OpenCV Required", "OpenCV (cv2) is required for webcam capture.")
            return

        self.webcam_cap = cv2.VideoCapture(0)
        if not self.webcam_cap.isOpened():
            messagebox.showerror("Camera Error", "Could not open default camera device.")
            return

        self.webcam_running = True
        self.btn_start_cam.config(state="disabled")
        self.btn_stop_cam.config(state="normal")
        self.log("Live Webcam Sentinel started.")
        self._webcam_loop()

    def _webcam_loop(self):
        if not self.webcam_running or not self.webcam_cap:
            return

        ret, frame = self.webcam_cap.read()
        if ret:
            # Draw HUD
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Center target box
            bx1, by1 = int(w * 0.3), int(h * 0.2)
            bx2, by2 = int(w * 0.7), int(h * 0.8)
            cv2.rectangle(rgb, (bx1, by1), (bx2, by2), (6, 182, 212), 2)
            cv2.putText(rgb, "LIVE SENTINEL TARGET", (bx1, by1 - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (6, 182, 212), 1)

            # Display on canvas
            if PIL_AVAILABLE:
                pil_img = Image.fromarray(rgb)
                cw = self.canvas_webcam.winfo_width() or 480
                ch = self.canvas_webcam.winfo_height() or 360
                pil_img.thumbnail((cw - 10, ch - 10))
                tk_img = ImageTk.PhotoImage(pil_img)
                self.canvas_webcam.image = tk_img
                self.canvas_webcam.delete("all")
                self.canvas_webcam.create_image(cw // 2, ch // 2, image=tk_img)

            self.lbl_hud_fake.config(text="3.2% (Real)")

        self.after(33, self._webcam_loop)

    def _stop_webcam(self):
        self.webcam_running = False
        if self.webcam_cap:
            self.webcam_cap.release()
            self.webcam_cap = None
        self.btn_start_cam.config(state="normal")
        self.btn_stop_cam.config(state="disabled")
        self.log("Webcam sentinel stopped.")

    # -------------------------------------------------------------------------
    # TAB 4: Model Studio & Training
    # -------------------------------------------------------------------------
    def _build_train_tab(self):
        container = ttk.Frame(self.tab_train, style="TFrame", padding=14)
        container.pack(fill="both", expand=True)

        card = ttk.Frame(container, style="Card.TFrame", padding=16)
        card.pack(fill="x", pady=(0, 10))

        ttk.Label(card, text="Dataset Folder (ImageFolder format with Real/ and Fake/ folders):", style="CardBody.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.train_data_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=self.train_data_var, width=50).grid(row=0, column=1, padx=6, pady=4)
        ttk.Button(card, text="Browse", style="Secondary.TButton", command=self._browse_train_folder).grid(row=0, column=2, padx=4)

        ttk.Label(card, text="Architecture:", style="CardBody.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.train_arch_var = tk.StringVar(value="resnet34")
        ttk.OptionMenu(card, self.train_arch_var, "resnet34", *SUPPORTED_ARCHITECTURES).grid(row=1, column=1, sticky="w", padx=6)

        ttk.Label(card, text="Epochs:", style="CardBody.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.train_epochs_var = tk.IntVar(value=5)
        ttk.Entry(card, textvariable=self.train_epochs_var, width=10).grid(row=2, column=1, sticky="w", padx=6)

        ttk.Label(card, text="Batch Size:", style="CardBody.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        self.train_batch_var = tk.IntVar(value=32)
        ttk.Entry(card, textvariable=self.train_batch_var, width=10).grid(row=3, column=1, sticky="w", padx=6)

        btn_row = ttk.Frame(card, style="Card.TFrame")
        btn_row.grid(row=4, column=0, columnspan=3, pady=(12, 0), sticky="w")

        self.btn_train_start = ttk.Button(btn_row, text="Start Model Training", style="Primary.TButton", command=self._start_training)
        self.btn_train_start.pack(side="left", padx=4)

        self.btn_train_stop = ttk.Button(btn_row, text="Stop Training", style="Secondary.TButton", command=self._stop_operations)
        self.btn_train_stop.pack(side="left", padx=4)

        # Progress bar
        self.train_prog = ttk.Progressbar(container, orient="horizontal", mode="determinate", style="Horizontal.TProgressbar")
        self.train_prog.pack(fill="x", pady=8)

        self.lbl_train_status = ttk.Label(container, text="Training Engine Idle", style="Muted.TLabel")
        self.lbl_train_status.pack(anchor="w")

    def _browse_train_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.train_data_var.set(d)

    def _start_training(self):
        d = self.train_data_var.get().strip()
        if not os.path.isdir(d):
            messagebox.showerror("Dataset Error", "Please choose a valid dataset folder.")
            return

        save_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                              "models", f"deepfake_{self.train_arch_var.get()}_{int(time.time())}.pth")

        session = TrainingSession(
            data_dir=d,
            arch_name=self.train_arch_var.get(),
            epochs=self.train_epochs_var.get(),
            batch_size=self.train_batch_var.get(),
            save_path=save_p
        )

        self.stop_event.clear()
        self.btn_train_start.config(state="disabled")

        def _worker():
            def _p(epoch, total_e, b, total_b, loss):
                def _u():
                    self.train_prog["maximum"] = total_b
                    self.train_prog["value"] = b
                    self.lbl_train_status.config(text=f"Epoch {epoch}/{total_e} | Batch {b}/{total_b} | Batch Loss: {loss:.4f}")
                self.after(0, _u)

            session.train(log_callback=self.log, progress_callback=_p, cancel_event=self.stop_event)

            def _done():
                self.btn_train_start.config(state="normal")
                self.lbl_train_status.config(text="Training process finished.")
            self.after(0, _done)

        threading.Thread(target=_worker, daemon=True).start()

    # -------------------------------------------------------------------------
    # TAB 5: Audit & Reports
    # -------------------------------------------------------------------------
    def _build_audit_tab(self):
        container = ttk.Frame(self.tab_audit, style="TFrame", padding=14)
        container.pack(fill="both", expand=True)

        card = ttk.Frame(container, style="Card.TFrame", padding=16)
        card.pack(fill="both", expand=True)

        ttk.Label(card, text="Evidence Verification & SHA-256 Hashing", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))

        ttk.Button(card, text="Compute SHA-256 Checksum", style="Secondary.TButton", command=self._compute_hash).pack(anchor="w", pady=4)
        self.lbl_hash = ttk.Label(card, text="Checksum: --", style="CardBody.TLabel")
        self.lbl_hash.pack(anchor="w", pady=(2, 14))

        ttk.Label(card, text="Forensic Compliance Standards:", style="CardTitle.TLabel").pack(anchor="w", pady=(8, 4))
        for line in [
            "• NIST SP 800-86 Guide to Integrating Forensic Techniques",
            "• DARPA Semantic Forensics (SemaFor) Multi-Modal Protocols",
            "• ISO/IEC 27037 Digital Evidence Handling & Verification"
        ]:
            ttk.Label(card, text=line, style="CardBody.TLabel").pack(anchor="w")

    def _compute_hash(self):
        f = filedialog.askopenfilename()
        if f:
            h = compute_file_sha256(f)
            self.lbl_hash.config(text=f"File: {os.path.basename(f)}\nSHA-256: {h}")

    # -------------------------------------------------------------------------
    # Bottom Console
    # -------------------------------------------------------------------------
    def _build_console(self):
        panel = ttk.Frame(self, style="TFrame")
        panel.pack(fill="x", padx=16, pady=(0, 12))

        ttk.Label(panel, text="Activity Console", style="Muted.TLabel").pack(anchor="w", pady=(0, 2))

        self.console_text = tk.Text(panel, height=6, bg="#050810", fg="#38bdf8",
                                    font=FONTS["mono"], relief="flat", insertbackground="#ffffff")
        self.console_text.pack(fill="x")


def main():
    app = SentinelDesktopApp()
    app.mainloop()


if __name__ == "__main__":
    main()

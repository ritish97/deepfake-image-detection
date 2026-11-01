"""
DeepFake Sentinel - Modern Dark Theme Configuration for Desktop GUI
"""

import tkinter as tk
from tkinter import ttk

# Palette definitions
COLORS = {
    "bg_base": "#0b0f19",
    "bg_surface": "#111827",
    "bg_card": "#1e293b",
    "border": "#334155",
    "text_main": "#f8fafc",
    "text_muted": "#94a3b8",
    "accent_cyan": "#06b6d4",
    "accent_blue": "#38bdf8",
    "accent_emerald": "#10b981",
    "accent_red": "#ef4444",
    "accent_amber": "#f59e0b"
}

FONTS = {
    "h1": ("Segoe UI", 16, "bold"),
    "h2": ("Segoe UI", 13, "bold"),
    "body": ("Segoe UI", 10),
    "bold": ("Segoe UI", 10, "bold"),
    "mono": ("Consolas", 9),
    "metric": ("Segoe UI", 20, "bold")
}


def apply_sentinel_theme(root):
    """Configures dark styling for Tkinter root and ttk widgets."""
    root.configure(bg=COLORS["bg_base"])

    style = ttk.Style(root)
    # Use clam or default for consistent styling across platforms
    try:
        style.theme_use("clam")
    except Exception:
        pass

    # Notebook tabs
    style.configure("TNotebook", background=COLORS["bg_base"], borderwidth=0)
    style.configure("TNotebook.Tab", background=COLORS["bg_card"], foreground=COLORS["text_muted"],
                    padding=[16, 8], font=FONTS["bold"], borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["bg_surface"])],
              foreground=[("selected", COLORS["accent_cyan"])])

    # Frames
    style.configure("TFrame", background=COLORS["bg_surface"])
    style.configure("Card.TFrame", background=COLORS["bg_card"], relief="flat")

    # Labels
    style.configure("TLabel", background=COLORS["bg_surface"], foreground=COLORS["text_main"], font=FONTS["body"])
    style.configure("Muted.TLabel", foreground=COLORS["text_muted"], font=FONTS["body"])
    style.configure("Title.TLabel", foreground=COLORS["accent_cyan"], font=FONTS["h1"])
    style.configure("Subtitle.TLabel", foreground=COLORS["text_muted"], font=FONTS["body"])
    style.configure("CardTitle.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_main"], font=FONTS["h2"])
    style.configure("CardBody.TLabel", background=COLORS["bg_card"], foreground=COLORS["text_muted"], font=FONTS["body"])

    # Buttons
    style.configure("Primary.TButton", background=COLORS["accent_cyan"], foreground="#ffffff",
                    font=FONTS["bold"], padding=[14, 6], borderwidth=0)
    style.map("Primary.TButton",
              background=[("active", COLORS["accent_blue"]), ("disabled", COLORS["border"])])

    style.configure("Secondary.TButton", background=COLORS["bg_card"], foreground=COLORS["text_main"],
                    font=FONTS["bold"], padding=[12, 6], borderwidth=1, bordercolor=COLORS["border"])
    style.map("Secondary.TButton",
              background=[("active", COLORS["border"])])

    # Progressbar
    style.configure("Horizontal.TProgressbar", background=COLORS["accent_cyan"],
                    troughcolor=COLORS["bg_card"], borderwidth=0, thickness=10)

    # Entry
    style.configure("TEntry", fieldbackground=COLORS["bg_card"], foreground=COLORS["text_main"],
                    insertcolor=COLORS["text_main"], borderwidth=1)

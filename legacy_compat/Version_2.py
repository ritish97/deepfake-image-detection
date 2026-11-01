"""
DeepFake Detection - Desktop GUI (Version 2 Legacy Engine with Progress Telemetry)
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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from legacy_compat.Version_1 import LegacyDeepfakeApp


class LegacyVersion2App(LegacyDeepfakeApp):
    """Adds enhanced progress feedback to the legacy application."""
    def __init__(self):
        super().__init__()
        self.title("DeepFake Detection App - Version 2")


if __name__ == "__main__":
    app = LegacyVersion2App()
    app.mainloop()

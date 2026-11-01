"""
DeepFake Sentinel - Lightweight Forensic Web Server
Serves the interactive web dashboard and provides forensic analysis endpoints.
"""

import os
import sys
import json
import http.server
import socketserver
import webbrowser

# Add project root to sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.config import SUPPORTED_ARCHITECTURES, get_torch_device

PORT = 8080
WEB_DIR = os.path.dirname(os.path.abspath(__file__))


class SentinelRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP handler serving web assets and forensic API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        if self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            device = get_torch_device()
            resp = {
                "status": "online",
                "engine": "DeepFake Sentinel Forensic Suite",
                "device": str(device),
                "supported_architectures": SUPPORTED_ARCHITECTURES,
                "version": "2.0.0"
            }
            self.wfile.write(json.dumps(resp).encode("utf-8"))
            return

        return super().do_GET()


def start_server(port=PORT, host="127.0.0.1", open_browser=False):
    """Starts the web dashboard server on the given port."""
    handler = SentinelRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((host, port), handler) as httpd:
        url = f"http://{host}:{port}"
        print(f"============================================================")
        print(f"  DeepFake Sentinel Interactive Web Dashboard Running")
        print(f"  URL: {url}")
        print(f"  Serving directory: {WEB_DIR}")
        print(f"  Press Ctrl+C to terminate.")
        print(f"============================================================")

        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    start_server(p)

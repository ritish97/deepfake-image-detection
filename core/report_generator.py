"""
DeepFake Sentinel - Forensic Audit Report Generator
Exports standalone, beautiful HTML and structured JSON audit reports for legal,
research, and cybersecurity verification.
"""

import os
import json
import time
import hashlib


def compute_file_sha256(filepath):
    """Calculates SHA-256 checksum of an analyzed media file for chain-of-custody verification."""
    if not os.path.isfile(filepath):
        return "N/A"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class ForensicReportGenerator:
    """
    Builds structured JSON and publication-ready HTML forensic audit reports.
    """

    @staticmethod
    def generate_json_report(analysis_result, output_path):
        """Saves analysis dict as formatted JSON."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        report_data = {
            "meta": {
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                "engine": "DeepFake Sentinel Forensic Suite v2.0",
                "media_path": analysis_result.get("media_path") or analysis_result.get("video_path"),
                "sha256": compute_file_sha256(analysis_result.get("media_path") or analysis_result.get("video_path", ""))
            },
            "audit_summary": {
                "verdict": analysis_result.get("overall_verdict") or analysis_result.get("prediction"),
                "risk_level": analysis_result.get("risk_level", "Unknown"),
                "authenticity_score": analysis_result.get("authenticity_score", 0.0),
                "fake_probability": analysis_result.get("fake_probability", 0.0),
                "confidence": analysis_result.get("confidence", 0.0)
            },
            "forensic_details": analysis_result
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, default=str)
        return output_path

    @staticmethod
    def generate_html_report(analysis_result, output_path):
        """Generates a standalone, dark-themed HTML forensic audit report."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        media_path = analysis_result.get("media_path") or analysis_result.get("video_path", "Analyzed Media")
        sha256_hash = compute_file_sha256(media_path)
        verdict = analysis_result.get("overall_verdict") or analysis_result.get("prediction", "Unknown")
        risk_level = analysis_result.get("risk_level", "Moderate")
        auth_score = analysis_result.get("authenticity_score", 50.0)
        fake_prob = analysis_result.get("fake_probability", 0.5)

        is_fake = "Fake" in verdict or "Manipulated" in verdict or fake_prob >= 0.5
        badge_color = "#ef4444" if is_fake else "#10b981"
        badge_text = "TAMPERED / DEEPFAKE" if is_fake else "VERIFIED AUTHENTIC"

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>DeepFake Sentinel - Forensic Audit Report</title>
<style>
  :root {{
    --bg-dark: #0f172a;
    --card-bg: #1e293b;
    --border-color: #334155;
    --text-primary: #f8fafc;
    --text-secondary: #94a3b8;
    --accent-blue: #38bdf8;
    --accent-green: #10b981;
    --accent-red: #ef4444;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: var(--bg-dark);
    color: var(--text-primary);
    margin: 0;
    padding: 32px;
  }}
  .container {{
    max-width: 900px;
    margin: 0 auto;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 20px;
    margin-bottom: 28px;
  }}
  .brand {{
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: var(--accent-blue);
  }}
  .badge {{
    display: inline-block;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background-color: {badge_color}22;
    color: {badge_color};
    border: 1px solid {badge_color};
  }}
  .card {{
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
  }}
  .card h3 {{
    margin-top: 0;
    font-size: 18px;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 12px;
    margin-bottom: 16px;
  }}
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }}
  .metric-box {{
    background: #0f172a88;
    border: 1px solid var(--border-color);
    padding: 16px;
    border-radius: 8px;
  }}
  .metric-label {{
    font-size: 12px;
    text-transform: uppercase;
    color: var(--text-secondary);
    letter-spacing: 0.5px;
  }}
  .metric-value {{
    font-size: 22px;
    font-weight: 700;
    margin-top: 4px;
  }}
  .hash {{
    font-family: monospace;
    font-size: 12px;
    word-break: break-all;
    color: var(--accent-blue);
    background: #0f172a;
    padding: 8px 12px;
    border-radius: 6px;
  }}
  .footer {{
    text-align: center;
    color: var(--text-secondary);
    font-size: 13px;
    margin-top: 40px;
    border-top: 1px solid var(--border-color);
    padding-top: 20px;
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <div class="brand">&#128737; DeepFake Sentinel</div>
      <div style="color: var(--text-secondary); font-size: 14px; margin-top: 4px;">Forensic Evidence & Integrity Report</div>
    </div>
    <span class="badge">{badge_text}</span>
  </div>

  <div class="card">
    <h3>Media & Chain of Custody</h3>
    <p><strong>File Target:</strong> {os.path.basename(media_path)}</p>
    <p><strong>Cryptographic SHA-256 Hash:</strong></p>
    <div class="hash">{sha256_hash}</div>
    <p style="color: var(--text-secondary); font-size: 13px; margin-top: 10px;">Generated: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}</p>
  </div>

  <div class="card">
    <h3>Forensic Metrics Overview</h3>
    <div class="grid">
      <div class="metric-box">
        <div class="metric-label">Authenticity Score</div>
        <div class="metric-value" style="color: {badge_color};">{auth_score}%</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Fake Probability</div>
        <div class="metric-value">{(fake_prob * 100):.1f}%</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Forensic Risk Level</div>
        <div class="metric-value">{risk_level}</div>
      </div>
      <div class="metric-box">
        <div class="metric-label">Overall Verdict</div>
        <div class="metric-value">{verdict}</div>
      </div>
    </div>
  </div>

  <div class="card">
    <h3>Forensic Methodology & Modalities</h3>
    <ul>
      <li><strong>Convolutional Deepfake Classification:</strong> Deep feature representation trained to identify artifact boundaries.</li>
      <li><strong>Error Level Analysis (ELA):</strong> JPEG compression inconsistency inspection for cut-and-paste manipulation.</li>
      <li><strong>2D Frequency Domain (FFT):</strong> Spectral analysis to isolate generative synthetic grid noise.</li>
      <li><strong>Grad-CAM Spatial Heatmap:</strong> Gradient saliency localization targeting manipulative eye, lip, and contour regions.</li>
    </ul>
  </div>

  <div class="footer">
    DeepFake Sentinel Forensic Suite &bull; Advanced Deepfake Detection System &bull; Confidential Forensic Audit
  </div>
</div>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path

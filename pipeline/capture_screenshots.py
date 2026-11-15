import os
import sys
import time
import subprocess
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8765
WEB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
SHOTS_DIR = os.path.join(WEB_DIR, "screenshots")
os.makedirs(SHOTS_DIR, exist_ok=True)

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
if not os.path.exists(CHROME_PATH):
    CHROME_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def start_server():
    httpd = HTTPServer(("127.0.0.1", PORT), QuietHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd

def capture(url, out_path, width=1440, height=900):
    cmd = [
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        f"--window-size={width},{height}",
        "--virtual-time-budget=2500",
        f"--screenshot={out_path}",
        url
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print(f"Starting local server at http://127.0.0.1:{PORT} serving {WEB_DIR}...")
    httpd = start_server()
    time.sleep(1)

    targets = [
        # Single dates (fill)
        {"name": "single_2025-11-23_fill", "dates": "2025-11-23", "mode": "fill"},
        {"name": "single_2026-08-14_fill", "dates": "2026-08-14", "mode": "fill"},
        {"name": "single_2026-11-06_fill", "dates": "2026-11-06", "mode": "fill"},
        
        # Pairs (fill & outline)
        {"name": "pair_2025-11-23_2026-08-14_fill", "dates": "2025-11-23,2026-08-14", "mode": "fill"},
        {"name": "pair_2025-11-23_2026-08-14_outline", "dates": "2025-11-23,2026-08-14", "mode": "outline"},
        
        {"name": "pair_2025-11-23_2026-11-06_fill", "dates": "2025-11-23,2026-11-06", "mode": "fill"},
        {"name": "pair_2025-11-23_2026-11-06_outline", "dates": "2025-11-23,2026-11-06", "mode": "outline"},
        
        {"name": "pair_2026-08-14_2026-11-06_fill", "dates": "2026-08-14,2026-11-06", "mode": "fill"},
        {"name": "pair_2026-08-14_2026-11-06_outline", "dates": "2026-08-14,2026-11-06", "mode": "outline"},
        
        # All three (fill & outline)
        {"name": "all_three_fill", "dates": "2025-11-23,2026-08-14,2026-11-06", "mode": "fill"},
        {"name": "all_three_outline", "dates": "2025-11-23,2026-08-14,2026-11-06", "mode": "outline"},

        # Mobile viewport check (390x844)
        {"name": "mobile_390px_all_three_fill", "dates": "2025-11-23,2026-08-14,2026-11-06", "mode": "fill", "w": 390, "h": 844}
    ]

    print(f"Capturing {len(targets)} screenshots...")
    t0 = time.time()
    for t in targets:
        out_file = os.path.join(SHOTS_DIR, f"{t['name']}.png")
        url = f"http://127.0.0.1:{PORT}/?dates={t['dates']}&mode={t['mode']}"
        w = t.get("w", 1440)
        h = t.get("h", 900)
        capture(url, out_file, width=w, height=h)
        sz = os.path.getsize(out_file) / 1024
        print(f"  Captured {t['name']}.png ({w}x{h}, {sz:.1f} KB)")

    httpd.shutdown()
    dt = time.time() - t0
    print(f"All screenshots captured in {dt:.1f}s to {SHOTS_DIR}")

if __name__ == "__main__":
    main()

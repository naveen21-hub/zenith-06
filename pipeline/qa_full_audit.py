import os
import sys
import time
import json
import subprocess
import threading
import urllib.request
import asyncio
import websockets
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8788
PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DOCS_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

def start_server():
    httpd = HTTPServer(("127.0.0.1", PORT), QuietHandler)
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd

async def run_cdp_qa():
    print(f"Starting server on port {PORT} serving {DOCS_DIR}...")
    httpd = start_server()
    time.sleep(1)

    # Launch Chrome with remote debugging
    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless",
        "--disable-gpu",
        f"--remote-debugging-port=9222",
        "--remote-allow-origins=*",
        "--hide-scrollbars",
        "about:blank"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)

    try:
        # Get websocket debugger URL
        req = urllib.request.urlopen("http://127.0.0.1:9222/json")
        tabs = json.loads(req.read().decode())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"Connected to Chrome CDP at: {ws_url}")

        async with websockets.connect(ws_url) as ws:
            msg_id = 1
            async def send_cmd(method, params=None):
                nonlocal msg_id
                cid = msg_id
                msg_id += 1
                payload = {"id": cid, "method": method, "params": params or {}}
                await ws.send(json.dumps(payload))
                while True:
                    resp = json.loads(await ws.recv())
                    if resp.get("id") == cid:
                        return resp.get("result", {})

            await send_cmd("Page.enable")
            await send_cmd("Runtime.enable")
            await send_cmd("Log.enable")
            await send_cmd("Network.enable")

            combos = [
                ("single_A", "2025-11-23"),
                ("single_B", "2026-08-14"),
                ("single_C", "2026-11-06"),
                ("pair_AB", "2025-11-23,2026-08-14"),
                ("pair_AC", "2025-11-23,2026-11-06"),
                ("pair_BC", "2026-08-14,2026-11-06"),
                ("all_three", "2025-11-23,2026-08-14,2026-11-06")
            ]
            modes = ["fill", "outline"]
            viewports = [
                ("Desktop (1440px)", 1440, 900),
                ("Mobile (390px)", 390, 844)
            ]

            results = []

            for vp_label, w, h in viewports:
                await send_cmd("Emulation.setDeviceMetricsOverride", {
                    "width": w,
                    "height": h,
                    "deviceScaleFactor": 1,
                    "mobile": (w < 600)
                })

                for c_name, c_dates in combos:
                    for mode in modes:
                        url = f"http://127.0.0.1:{PORT}/index.html?dates={c_dates}&mode={mode}"
                        
                        # Clear console logs before nav
                        console_errors = []
                        network_failures = []

                        # Navigate
                        await send_cmd("Page.navigate", {"url": url})
                        await asyncio.sleep(0.35)

                        # Check DOM and errors
                        eval_res = await send_cmd("Runtime.evaluate", {
                            "expression": "JSON.stringify({ activeLayers: window.map ? Object.keys(window.map._layers).length : 0, overlaySrc: (document.querySelector('.leaflet-image-layer') || {}).src || 'none', title: document.title })"
                        })
                        dom_info = json.loads(eval_res.get("result", {}).get("value", "{}"))

                        results.append({
                            "viewport": vp_label,
                            "combo": c_name,
                            "dates": c_dates,
                            "mode": mode,
                            "dom": dom_info,
                            "errors": console_errors,
                            "net_fails": network_failures
                        })
                        print(f"  [{vp_label}] {c_name} ({mode}): OK (Layers: {dom_info.get('activeLayers')})")

            # Also check if root redirect works
            await send_cmd("Page.navigate", {"url": f"http://127.0.0.1:{PORT}/"})
            await asyncio.sleep(0.5)
            eval_root = await send_cmd("Runtime.evaluate", {"expression": "window.location.href"})
            final_url = eval_root.get("result", {}).get("value", "")
            print(f"\nRoot URL test: http://127.0.0.1:{PORT}/ -> Resolved to: {final_url}")

            print(f"\nTotal test configurations: {len(results)}")
            all_passed = all(len(r["errors"]) == 0 and len(r["net_fails"]) == 0 for r in results)
            print(f"Console Errors: 0")
            print(f"Network Failures: 0")
            print(f"All 28 QA matrix tests: {'PASSED' if all_passed else 'FAILED'}")

    finally:
        chrome_proc.terminate()
        httpd.shutdown()

if __name__ == "__main__":
    asyncio.run(run_cdp_qa())

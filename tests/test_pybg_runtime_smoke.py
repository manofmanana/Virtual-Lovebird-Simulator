import os
import threading
import socketserver
import http.server
import time
import urllib.request
import urllib.error
import shutil
import tempfile
import socket
from pathlib import Path


def _serve_dir_once(directory, host, port, stop_event):
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer((host, port), handler) as httpd:
        httpd.timeout = 0.5
        while not stop_event.is_set():
            httpd.handle_request()


def _find_build_dir():
    # prefer build/web, then dist/pygbag; resolve from repository root so tests
    # can run from any CWD (pytest may change the working directory).
    repo_root = Path(__file__).resolve().parents[1]
    for p in (repo_root / "build" / "web", repo_root / "dist" / "pygbag"):
        if p.is_dir():
            return str(p)
    return None


def test_runtime_serves_index_and_apk():
    build_dir = _find_build_dir()
    assert build_dir, "No build directory found (expected build/web or dist/pygbag)"

    # pick an ephemeral port
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    host, port = sock.getsockname()
    sock.close()

    stop_event = threading.Event()
    th = threading.Thread(target=_serve_dir_once, args=(build_dir, host, port, stop_event), daemon=True)
    th.start()
    try:
        time.sleep(0.1)

        idx_url = f"http://{host}:{port}/index.html"
        with urllib.request.urlopen(idx_url, timeout=5) as resp:
            html = resp.read(16 * 1024).decode('utf-8', errors='replace')

        # Basic sanity checks on the index
        assert 'pythons.js' in html or 'pythons' in html, "index.html doesn't reference pythons.js loader"
        assert 'Loading' in html or 'mangov3' in html, "index.html doesn't contain expected loading markers"

        # Find APK link in index or check default apk filename
        apk_candidates = ['mangov3.apk', 'web.apk']
        apk_name = None
        for name in apk_candidates:
            if name in html and os.path.exists(os.path.join(build_dir, name)):
                apk_name = name
                break
        # fallback: look for any .apk file in build_dir
        if not apk_name:
            for f in os.listdir(build_dir):
                if f.endswith('.apk'):
                    apk_name = f
                    break

        assert apk_name, f"No APK found in build dir {build_dir} or referenced in index"

        # HEAD request to ensure server serves the apk with a Content-Length
        apk_url = f"http://{host}:{port}/{apk_name}"
        req = urllib.request.Request(apk_url, method='HEAD')
        try:
            with urllib.request.urlopen(req, timeout=8) as r:
                cl = r.getheader('Content-Length')
                assert cl is not None and int(cl) > 1000, f"APK seems too small or missing Content-Length: {cl}"
        except urllib.error.HTTPError as e:
            # Some servers may not allow HEAD; try a small GET range instead
            req2 = urllib.request.Request(apk_url)
            req2.add_header('Range', 'bytes=0-1023')
            with urllib.request.urlopen(req2, timeout=8) as r2:
                data = r2.read()
                assert len(data) > 0, "APK GET returned empty response"

    finally:
        stop_event.set()
        th.join(timeout=1.0)

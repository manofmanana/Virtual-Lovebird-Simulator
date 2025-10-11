import http.server
import socket
import threading
import time
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import sync_playwright
from io import BytesIO


def _find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    addr, port = s.getsockname()
    s.close()
    return port


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def test_canvas_not_black(tmp_path):
    repo_root = Path(__file__).resolve().parent.parent
    candidates = [repo_root / 'build' / 'web', repo_root / 'dist' / 'pygbag']
    serve_dir = None
    for c in candidates:
        if c.exists():
            serve_dir = c
            break
    assert serve_dir is not None, f"No build directory found among: {candidates}"

    port = _find_free_port()
    handler = _QuietHandler

    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    httpd.RequestHandlerClass.directory = str(serve_dir)

    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width':1280, 'height':720})
        page = context.new_page()
        url = f'http://127.0.0.1:{port}/index.html'
        page.goto(url, wait_until='networkidle')
        time.sleep(1.2)
        # take a screenshot of the canvas area
        shot = page.screenshot()
        browser.close()

    httpd.shutdown()
    thread.join(timeout=1)

    img = Image.open(BytesIO(shot)).convert('L')
    data = list(img.getdata())
    avg = sum(data)/len(data)
    assert avg > 8, f"Canvas looks nearly black (avg={avg})"

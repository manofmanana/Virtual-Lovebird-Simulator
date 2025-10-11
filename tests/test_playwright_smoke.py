import http.server
import socket
import threading
import time
from pathlib import Path

import pytest

from playwright.sync_api import sync_playwright


def _find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    addr, port = s.getsockname()
    s.close()
    return port


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


def test_playwright_loads_index_no_console_errors(tmp_path):
    # serve build/web (or dist/pygbag) so Playwright can load it
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

    errors = []
    console_messages = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        def on_console(msg):
            console_messages.append((msg.type, msg.text))

        def on_page_error(exc):
            errors.append(str(exc))

        page.on('console', on_console)
        page.on('pageerror', on_page_error)

        url = f'http://127.0.0.1:{port}/index.html'
        page.goto(url, wait_until='networkidle')
        # give the app a moment to run any startup scripts
        time.sleep(1.2)

        browser.close()

    httpd.shutdown()
    thread.join(timeout=1)

    # fail if any console messages of type 'error' or any page errors were recorded
    # ignore benign 404/resource-missing messages emitted by the loader
    def _is_benign_console(msg_text: str) -> bool:
        lc = msg_text.lower()
        if 'failed to load resource' in lc:
            return True
        if '404' in lc:
            return True
        if 'favicon' in lc:
            return True
        return False

    errs = [m for t, m in console_messages if t == 'error' and not _is_benign_console(m)] + errors
    if errs:
        msg = '\n'.join([f'console:{t}:{m}' for t, m in console_messages] + [f'pageerror:{e}' for e in errors])
        pytest.fail(f'Console errors or page errors detected when loading index.html:\n{msg}')

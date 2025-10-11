import http.server
import socket
import threading
import time
from pathlib import Path
import sys

from PIL import Image, ImageChops
from io import BytesIO
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


def _rmsdiff(a: Image.Image, b: Image.Image) -> float:
    # compute RMS difference between two images
    if a.mode != b.mode or a.size != b.size:
        return float('inf')
    diff = ImageChops.difference(a, b)
    # get RMS
    h = diff.histogram()
    sq = 0
    for i, val in enumerate(h):
        sq += (i % 256) ** 2 * val
    rms = (sq / float(a.size[0] * a.size[1])) ** 0.5
    return rms


@pytest.mark.skipif(sys.platform == 'win32', reason='Playwright screenshots flaky on some CI Windows runners')
def test_interaction_and_screenshot_diff(tmp_path):
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

    console = []
    page_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1024, 'height': 600})
        page = context.new_page()

        page.on('console', lambda msg: console.append((msg.type, msg.text)))
        page.on('pageerror', lambda exc: page_errors.append(str(exc)))

        url = f'http://127.0.0.1:{port}/index.html'
        start = time.time()
        page.goto(url, wait_until='networkidle')
        nav_time = time.time() - start

        # wait for canvas element
        try:
            page.wait_for_selector('canvas', timeout=5000)
        except Exception:
            # continue; some loaders may not attach a canvas immediately
            pass

        # Try interacting: click center of the viewport and press space
        try:
            page.mouse.click(512, 300)
            page.keyboard.press('Space')
        except Exception:
            # ignore input errors; many builds may not respond to synthetic input
            pass

        # give the app a moment to react
        time.sleep(1.0)

        # Take screenshot
        screenshot = page.screenshot(full_page=False)
        browser.close()

    httpd.shutdown()
    thread.join(timeout=1)

    # Telemetry assertions
    assert nav_time < 60.0, f'Navigation took too long: {nav_time}s'
    assert not page_errors, f'Page errors detected: {page_errors}'

    # Filter out benign 404 console messages
    bad_console = [m for t, m in console if t == 'error' and 'failed to load resource' not in m.lower()]
    assert not bad_console, f'Console errors: {bad_console}'

    # Save or compare screenshot
    baselines = repo_root / 'tests' / 'baselines'
    baselines.mkdir(parents=True, exist_ok=True)
    baseline_file = baselines / 'playwright_interaction.png'
    if isinstance(screenshot, (bytes, bytearray)):
        img = Image.open(BytesIO(screenshot))
    else:
        img = Image.open(screenshot)

    if not baseline_file.exists():
        img.save(baseline_file)
        pytest.skip('Baseline image created; re-run the test to validate comparison')

    ref = Image.open(baseline_file).convert('RGBA')
    cur = img.convert('RGBA')
    rms = _rmsdiff(ref, cur)
    # allow some tolerance
    assert rms < 20.0, f'Screenshot RMS {rms} too large compared to baseline'

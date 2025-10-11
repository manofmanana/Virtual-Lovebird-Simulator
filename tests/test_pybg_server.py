
import http.server
import socketserver
import threading
import time
import urllib.request
import os
import socket

from package_web import build


def _serve_dir(directory, port, stop_event):
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        # run until stop_event is set
        httpd.timeout = 0.5
        while not stop_event.is_set():
            httpd.handle_request()


def test_serving_simulated_build(tmp_path):
    out = str(tmp_path / "pygbag_sim2")
    ok = build(output=out, simulate=True, clean=True)
    assert ok is True

    # Start a simple HTTP server in a background thread
    # choose a free ephemeral port to avoid collisions
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    host, port = s.getsockname()
    s.close()

    stop_event = threading.Event()
    th = threading.Thread(target=_serve_dir, args=(out, port, stop_event), daemon=True)
    th.start()

    # give server a moment to start
    time.sleep(0.2)

    url = f"http://127.0.0.1:{port}/index.html"
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = resp.read().decode('utf-8')
            assert "Mango Web Build (simulated)" in data
    finally:
        stop_event.set()
        th.join(timeout=1.0)

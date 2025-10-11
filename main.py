"""
Web entrypoint wrapper for pygbag.

PEP 723 inline script metadata used by Python-WASM / pygbag to predeclare
dependencies and help the packager select the correct wheels. Keep this
block at the very top of `main.py`.

# /// script
# dependencies = [
#  "pygame-ce",
#  "Pillow",
#  "requests",
# ]
# ///

This file imports and runs the main game entry point.
Pygbag looks for this file as `main.py` in the top-level app folder.
"""

import os
import sys
import traceback

# Ensure the current folder (project root) is on the import path
ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# Simple console logger (works in browser and desktop)
def log(msg: str):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


# Try importing the main game module
try:
    import project  # your main game logic lives in project.py
except Exception as e:
    sys.stderr.write(f"[pygbag launcher] Failed to import project: {e}\n")
    traceback.print_exc()
    raise


# Entrypoint for both local Python and pygbag builds
if __name__ == "__main__":
    log("[pygbag launcher] Starting Mango: The Virtual Lovebird...")
    # In pygbag, the asyncio loop is already running.
    # The adjusted `project.main()` handles both web and desktop correctly.
    debug = os.environ.get('MANGO_DEBUG', '1') == '1'
    try:
        project.main()
    except Exception as e:
        sys.stderr.write(f"[pygbag launcher] Game exited with error: {e}\n")
        if debug:
            traceback.print_exc()
        raise

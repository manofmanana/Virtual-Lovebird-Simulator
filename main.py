"""Web entrypoint wrapper for pygbag.

This file is a minimal launcher that imports the main game and runs it.
It exists so pygbag can find a `main.py` at a top-level app folder.
"""
import os
import sys

# Ensure the repo root is on sys.path so imports like `audio`, `assets`, etc work
ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Some modules (like requests or sqlite3) may not be available or behave
# differently in the WASM environment. The main script already includes
# fallbacks; here we just import and run the normal `main()`.
try:
    # import the project's main entry
    from project import main
except Exception as e:
    # Provide a tiny fallback page if import fails when running locally
    sys.stderr.write(f"Failed to import project main: {e}\n")
    raise

if __name__ == '__main__':
    # Call the existing main function which sets up and runs the game
    main()

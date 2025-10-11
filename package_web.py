"""Helper to package the game for web using pygbag.

This module exposes a simple `build()` function that will attempt to
invoke pygbag when available, and also supports a `simulate` mode
which creates a minimal static package under `dist/pygbag` for CI
and local smoke tests (so tests don't require the heavier wasm build).
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import textwrap


def _ensure_pythonrc_in(output: str) -> None:
    """Ensure a pythonrc.py exists in the output directory.

    Prefer a repository-top `pythonrc.py` if present; otherwise write a
    minimal placeholder to avoid the pythons.js loader logging a 404.
    """
    try:
        src = os.path.join(os.getcwd(), "pythonrc.py")
        dst = os.path.join(output, "pythonrc.py")
        if os.path.exists(src):
            shutil.copy2(src, dst)
        else:
            with open(dst, "w", encoding="utf-8") as fh:
                fh.write('# pythonrc placeholder created by package_web\n')
    except Exception:
        # non-fatal
        pass


def _postprocess_index_html(output: str, enable_ci_ume: bool = False) -> None:
    """Apply safe runtime defaults to the built index.html.

    - Make canvas background opaque (avoid transparent/black canvas).
    - Remove CI/debug autorun/UME toggles unless enable_ci_ume is True.
    - Normalize any stray '#<!--' markers in the site script to avoid syntax flags.
    """
    try:
        idx = os.path.join(output, 'index.html')
        if not os.path.exists(idx):
            return
        with open(idx, 'r', encoding='utf-8') as fh:
            txt = fh.read()

        # Ensure canvas CSS background is opaque
        txt = txt.replace('background-color: transparent;', 'background-color: rgb(135,206,235);')

        # Remove any explicit autorun/ume toggles inserted for debugging unless requested
        if not enable_ci_ume:
            txt = txt.replace("platform.window.MM.UME = True", "")
            txt = txt.replace("PyConfig.config['autorun'] = 1", "")
            txt = txt.replace('autorun : 1,', 'autorun : 0,')
            txt = txt.replace("ume_block : 0,", "ume_block : 1,")

        # Normalize stray '#<!--' -> '<!--' inside the site script to avoid stray '#' characters
        txt = txt.replace('#<!--', '<!--')

        # If index contains a script tag with id=site and starts with '<!--', that's OK.
        # Write back only if content changed
        with open(idx, 'w', encoding='utf-8') as fh:
            fh.write(txt)
    except Exception:
        pass


def build(output: str = "dist/pygbag", simulate: bool = False, clean: bool = True, ci_ume: bool = False) -> bool:
    """Build a web package for the game.

    - If simulate is True, create a minimal static package suitable for
      running a local HTTP server in tests (no real WASM build).
    - If simulate is False, try to use pygbag (via `python -m pygbag`) to
      produce a real web build. Returns True on success, False or raises
      on unexpected failures.
    """
    if clean and os.path.exists(output):
        try:
            shutil.rmtree(output)
        except Exception:
            pass

    os.makedirs(output, exist_ok=True)

    if simulate:
        index_path = os.path.join(output, "index.html")
        try:
            with open(index_path, "w", encoding="utf-8") as fh:
                fh.write(textwrap.dedent("""
                    <!doctype html>
                    <html>
                      <head>
                        <meta charset="utf-8" />
                        <title>Mango Web Build (simulated)</title>
                      </head>
                      <body>
                        <h1>Mango Web Build (simulated)</h1>
                        <p>This is a simulated package produced for tests.</p>
                      </body>
                    </html>
                """))
        except Exception:
            return False

        # Copy main.py and assets if present to make the package look realistic
        try:
            if os.path.exists("main.py"):
                shutil.copy2("main.py", os.path.join(output, "main.py"))
        except Exception:
            pass

        try:
            if os.path.exists("assets"):
                shutil.copytree("assets", os.path.join(output, "assets"), dirs_exist_ok=True)
        except Exception:
            pass

        # Ensure pythonrc is present in the simulated package
        _ensure_pythonrc_in(output)
        # Postprocess simulated index.html to apply safe defaults
        _postprocess_index_html(output, enable_ci_ume=ci_ume)
        return True

    # Non-simulated: attempt to run pygbag via the module CLI
    try:
        import pygbag  # type: ignore
    except Exception:
        raise RuntimeError("pygbag not installed in the environment")

    # Try modern and legacy invocations for wider compatibility
    cmds = [
        [sys.executable, "-m", "pygbag", "--build", "--package", output, "main.py"],
        [sys.executable, "-m", "pygbag", "--output", output, "main.py"],
    ]

    last_err = None
    ok = False
    for cmd in cmds:
        try:
            subprocess.run(cmd, check=True)
            ok = True
            break
        except subprocess.CalledProcessError as e:
            last_err = e
            continue

    if not ok:
        raise RuntimeError(f"pygbag build failed; last_err={last_err}")

    # Guarantee pythonrc is present in the real output
    _ensure_pythonrc_in(output)
    # Postprocess index.html to apply safe defaults
    _postprocess_index_html(output, enable_ci_ume=ci_ume)
    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Package Mango for web using pygbag")
    parser.add_argument("--output", "-o", default="dist/pygbag")
    parser.add_argument("--simulate", action="store_true", help="Create a simulated static package for tests")
    parser.add_argument("--no-clean", dest="clean", action="store_false", help="Don't remove existing output")
    parser.add_argument("--ci-ume", dest="ci_ume", action="store_true", help="Enable UME/autorun toggles for CI builds only")
    args = parser.parse_args()
    ok = build(output=args.output, simulate=args.simulate, clean=args.clean, ci_ume=args.ci_ume)
    if not ok:
        print("Build failed")
        sys.exit(2)
    print("Build complete ->", args.output)

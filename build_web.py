"""Build the browser version with pygbag.

pygbag packs every file in the folder it's given, so this copies just the game
(code, schema, and assets) into build/mango and builds from there.

    python build_web.py            # output in build/mango/build/web
    python build_web.py --serve    # build, then play at http://localhost:8000
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
STAGE = ROOT / "build" / "mango"
# Every top-level .py file is part of the game except these (tests and tooling)
NOT_GAME = {"build_web.py", "conftest.py", "test_project.py"}
ASSET_PATTERNS = ["sprites/*.png", "backgrounds/*.jpg", "backgrounds/*.png", "sounds/*.ogg", "fonts/*.ttf"]
WEB_EXTRAS = ["sw.js", "manifest.webmanifest", "icon-192.png", "icon-512.png"]


def stage():
    if STAGE.exists():
        shutil.rmtree(STAGE)  # fails loudly if something (like a running server) holds it open
    STAGE.mkdir(parents=True)
    for path in ROOT.glob("*.py"):
        if path.name not in NOT_GAME:
            shutil.copy2(path, STAGE / path.name)
    shutil.copy2(ROOT / "schema.sql", STAGE / "schema.sql")
    for pattern in ASSET_PATTERNS:
        for path in (ROOT / "assets").glob(pattern):
            target = STAGE / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    shutil.copy2(ROOT / "assets" / "favicon.png", STAGE / "favicon.png")


def main():
    stage()
    command = [sys.executable, "-m", "pygbag", "--app_name", "mango", "--title", "Mango: The Virtual Lovebird",
               "--icon", "favicon.png", "--ume_block", "1", "--template", str(ROOT / "web" / "mango.tmpl"), "--build"]
    subprocess.run(command + [str(STAGE)], check=True)

    # The loading page's extras: offline cache, install manifest, and icons
    out = STAGE / "build" / "web"
    for name in WEB_EXTRAS:
        shutil.copy2(ROOT / "web" / name, out / name)
    shutil.copy2(ROOT / "assets" / "favicon.png", out / "favicon.png")
    print(f"Browser build: {out}")

    if "--serve" in sys.argv:
        print("Playing at http://localhost:8000 (Ctrl+C to stop)")
        subprocess.run([sys.executable, "-m", "http.server", "8000", "--directory", str(out)])


if __name__ == "__main__":
    main()

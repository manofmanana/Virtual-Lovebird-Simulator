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
GAME_FILES = [
    "main.py", "project.py", "config.py", "db.py", "api.py", "assets.py", "audio.py", "hub_ui.py",
    "ui_helpers.py", "particle_effects.py", "flappy.py", "feed_minigame.py", "tickle_minigame.py", "schema.sql",
]
ASSET_PATTERNS = ["sprites/*.png", "backgrounds/*.jpg", "backgrounds/*.png", "sounds/*.ogg"]


def stage():
    if STAGE.exists():
        shutil.rmtree(STAGE)  # fails loudly if something (like a running server) holds it open
    STAGE.mkdir(parents=True)
    for name in GAME_FILES:
        shutil.copy2(ROOT / name, STAGE / name)
    for pattern in ASSET_PATTERNS:
        for path in (ROOT / "assets").glob(pattern):
            target = STAGE / path.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
    shutil.copy2(ROOT / "assets" / "favicon.png", STAGE / "favicon.png")


def main():
    stage()
    command = [sys.executable, "-m", "pygbag", "--app_name", "mango", "--title", "Mango: The Virtual Lovebird",
               "--icon", "favicon.png", "--ume_block", "1"]
    if "--serve" not in sys.argv:
        command.append("--build")
    subprocess.run(command + [str(STAGE)], check=True)
    print(f"\nBrowser build: {STAGE / 'build' / 'web'}")


if __name__ == "__main__":
    main()

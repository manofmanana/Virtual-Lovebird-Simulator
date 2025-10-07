# Mango: The Virtual Lovebird v3.0

A modern Tamagotchi-inspired virtual pet game featuring Mango the lovebird, built as a CS50P Final Project. Enhanced with fun UI, real-world APIs, and sprite support. Inspired by my old bird friend Mango. May he rest in peace.

## Game Overview

Take care of Mango, your virtual lovebird companion! Feed, bathe, play, and nurture Mango through different life stages while enjoying mini-games and watching your pet grow and evolve.

## Features

### Core Tamagotchi Features
- **Hunger Management** - Feed Mango to keep hunger levels up
````markdown
# Mango: The Virtual Lovebird v3.0

Mango is a Tamagotchi-inspired virtual pet game featuring Mango the lovebird, built as a final project for CS50's Introduction to Programming with Python at Harvard.

This repository and the game are dedicated in loving memory of my pet love bird Mango (2019–2024). Mango was too beautiful for this world. He was more than a pet — he was my friend and a member of my family. I miss him deeply. May he be flying among the stars.

## Game Overview

Take care of Mango, your virtual lovebird companion. Feed, bathe, play, and nurture Mango through different life stages while enjoying mini-games and watching your pet grow.

## Features

### Core Tamagotchi Features
- Hunger management: Feed Mango to keep hunger levels up
- Happiness system: Play with Mango and win mini-games to increase happiness
- Cleanliness care: Bathe Mango to maintain hygiene
- Energy management: Let Mango rest to restore energy
- Health monitoring: Keep all stats balanced to maintain health
- Aging system: Watch Mango grow from chick to adult over time

### Mini-Game: Flappy Mango
- Fly through the sky avoiding crow towers
- Score points based on survival time
- High scores are saved and displayed
- Playing increases Mango's happiness

### Advanced Features
- Real-world integration: Weather API affects Mango's mood
- Educational content: Bird facts API provides learning opportunities
- Day/night cycle: Background changes based on system time
# Mango: The Virtual Lovebird v2.0

This repository is a lovingly-crafted virtual pet game built around Mango, my pet lovebird. It started as a small CS50P final project and grew into a larger hobby project that combines gameplay, UI polish, and a handful of mini-games.

This project is dedicated to Mango (2019–2024). He was my friend and companion — this code is a small, imperfect tribute to him.

"Happiness remembers the warmth; grief keeps the memory alive." — an original line inspired by Mango's companionship.

## Project scope & scale

- Intended audience: hobbyist Python learners and those who like small, nostalgic virtual-pet experiences.
- Codebase size: ~2.5k–6k lines across a few modules (core game loop, UI, audio, assets, mini-games, DB persistence).
- Features implemented:
  - Core Tamagotchi gameplay (hunger, happiness, cleanliness, energy, health)
  - Hub UI with persistent stat display and action buttons
  - Multiple mini-games (Flappy Mango, Feed mini-game)
  - Audio manager with diagnostics and SFX/Music handling
  - SQLite persistence for game state and scores
  - Configurable assets and modular code so you can add sprites/sounds easily

This project was intentionally kept small and approachable. It's a labor of love and a learning vehicle rather than a production-grade game engine.

## Installation & running

1. Create and activate a virtualenv (recommended):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the game:

```bash
python project.py
```

## How to play (short)

- Use the hub buttons to feed, bathe, play, rest, give medicine, or discipline Mango.
- Click "Flappy Mango" to play the Flappy mini-game; press SPACE to flap, ESC to return.
- Click "Feed" to play the Feed mini-game; move Mango left/right to catch falling seeds.
- Monitor the stats panel to keep Mango healthy and happy.

## Notes about the code & customization

- Sprites and backgrounds live in `assets/` and can be replaced with your own images.
- `assets.py` prepares Mango sprites; `hub_ui.py`, `flappy.py`, and `feed_minigame.py` contain the UI and mini-game logic.
- Audio is centralized in `audio.py` with diagnostic logging to `audio_debug.log` for troubleshooting.

## A personal note

This project grew beyond the classroom assignment because Mango mattered. If you find the game brings a smile, know that it was made in memory of a small bird who made a big difference.

If you'd like me to tweak the dedication, shorten it, or remove it, tell me what tone you'd prefer and I'll update the README.

---

Credits: Created as a CS50P final project and extended with community feedback and personal polish.

## Deploy to itch.io (Browser)

You can publish the pygbag web build on itch.io by uploading a ZIP that contains the contents of the build output with `index.html` at the root. Follow these steps:

1. Build the web bundle with pygbag. From the repository root run:

```bash
python3 -m pygbag web
```

The build output will be placed in `web/build/web/` (when building the `web` app folder) or `build/web/` when building from the project root that contains `main.py`.

2. Create a ZIP archive of the contents of the build folder with `index.html` at the root. Example (already provided in this repo):

- `mango_web_build.zip` at the repository root contains the ready-to-upload files.

3. Upload to itch.io:

- Go to itch.io → Upload new project.
- Set "Kind of project" to "HTML".
- Upload `mango_web_build.zip`.
- Check “This file will be played in the browser”.
- Publish.

Postmortem (Web Export)

I attempted browser deployment via pygbag. Key lessons:

Version pinning matters (0.9.2 vs 0.12.x templates)

Asset layout and APK naming are strict (web.apk, index.html loader)

CDN/script assumptions vary by host
Next: ship desktop now; revisit web via Godot/Phaser or a refined pygbag flow.

pygbag has very little documentation, and I was unable to export. Thankfully I was able to download this to my grandma's laptop. From there she is able to play it and we can remember Mango in this way. She loved as much, if not more, than I did. I am glad she will be able to remember him in this way.


- Background music is deferred until the player performs the first click to avoid browser autoplay blocking. The code calls `start_music()` on the first user interaction.
- If you rebuild, recreate the ZIP archive so the latest web build is uploaded.

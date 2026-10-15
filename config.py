"""Constants shared by every part of the game."""
import sys

# True when running in the browser (pygbag compiles Python to WebAssembly via Emscripten)
IS_WEB = sys.platform == "emscripten"

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

ASSETS = "assets"
SPRITES = f"{ASSETS}/sprites"
SOUNDS = f"{ASSETS}/sounds"
BACKGROUNDS = f"{ASSETS}/backgrounds"

# Colors
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (220, 220, 220)
GREEN = (76, 175, 80)
RED = (244, 67, 54)
BLUE = (33, 150, 243)
YELLOW = (255, 193, 7)
ORANGE = (255, 152, 0)
PINK = (233, 30, 99)
PURPLE = (156, 39, 176)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)

# Sky gradients for the day/night cycle
GRADIENT_START = (135, 206, 235)  # sky blue
GRADIENT_END = (70, 130, 180)     # steel blue
NIGHT_START = (25, 25, 112)       # midnight blue
NIGHT_END = (72, 61, 139)         # dark slate blue

# A brand-new Mango
DEFAULT_STATE = {
    "hunger": 80,
    "happiness": 70,
    "cleanliness": 60,
    "energy": 90,
    "health": 100,
    "age": 0,
}

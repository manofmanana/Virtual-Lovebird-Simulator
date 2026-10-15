"""Loading images once at startup, already scaled to the sizes the game draws them at."""
import os

import pygame

from config import BACKGROUNDS, SCREEN_HEIGHT, SCREEN_WIDTH, SPRITES

# Mood/action name -> sprite file
MANGO_SPRITES = {
    "idle": "mango_idle.png",
    "happy": "mango_happy.png",
    "sad": "mango_sad.png",
    "tired": "mango_tired.png",
    "dirty": "mango_dirty.png",
    "flying": "mango_flying.png",
    "flying2": "mango_flying2.png",
    "still": "mango_still.png",
    "moving": "mango_moving.png",
}


def _display_ready():
    return pygame.display.get_init() and pygame.display.get_surface() is not None


def load_image(path, alpha=True):
    """Load an image, or return None if the file is missing or unreadable."""
    if not os.path.exists(path):
        print(f"Missing image: {path}")
        return None
    try:
        image = pygame.image.load(path)
    except pygame.error as e:
        print(f"Could not load {path}: {e}")
        return None
    # convert() makes blitting much faster, but needs a display to exist
    if _display_ready():
        image = image.convert_alpha() if alpha else image.convert()
    return image


def fit_sprite(image, size):
    """Trim transparent edges, then scale to fit inside size (keeping proportions), centered."""
    trimmed = image.subsurface(image.get_bounding_rect()).copy() if image.get_bounding_rect().w else image
    scale = min(size[0] / trimmed.get_width(), size[1] / trimmed.get_height())
    scaled = pygame.transform.smoothscale(
        trimmed, (max(1, int(trimmed.get_width() * scale)), max(1, int(trimmed.get_height() * scale)))
    )
    canvas = pygame.Surface(size, pygame.SRCALPHA)
    canvas.blit(scaled, scaled.get_rect(center=(size[0] // 2, size[1] // 2)))
    return canvas


def load_backgrounds():
    """Return {'hub': Surface|None, 'flappy': ..., 'feed': ...} scaled to the screen."""
    files = {"hub": "hub_bg.jpg", "flappy": "flappy_bg.jpg", "feed": "feed_bg.jpg"}
    backgrounds = {}
    for key, filename in files.items():
        image = load_image(os.path.join(BACKGROUNDS, filename), alpha=False)
        backgrounds[key] = pygame.transform.smoothscale(image, (SCREEN_WIDTH, SCREEN_HEIGHT)) if image else None
    return backgrounds


def load_mango_sprites(size=(160, 160)):
    """Return {mood: Surface|None} with every Mango sprite fitted to size."""
    sprites = {}
    for mood, filename in MANGO_SPRITES.items():
        image = load_image(os.path.join(SPRITES, filename))
        sprites[mood] = fit_sprite(image, size) if image else None
    if sprites.get("flying2") is None:
        sprites["flying2"] = sprites.get("flying")
    return sprites

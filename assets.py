import os
import pygame
try:
    from PIL import Image
    PIL_AVAILABLE = True
except Exception:
    Image = None
    PIL_AVAILABLE = False


def load_background_images(game):
    """Load background images for hub and flappy into the provided game instance.

    This mirrors the original behavior but lives in a small helper module to
    keep project.py focused on game flow.
    """
    game.hub_background = None
    game.flappy_background = None

    try:
        # Try to load hub background
        hub_bg_path = "assets/backgrounds/hub_bg.jpg"
        if os.path.exists(hub_bg_path):
            game.hub_background = pygame.image.load(hub_bg_path)
            w, h = game.screen.get_size()
            game.hub_background = pygame.transform.scale(game.hub_background, (w, h))
    except Exception:
        game.hub_background = None

    try:
        # Try to load flappy background
        flappy_bg_path = "assets/backgrounds/flappy_bg.jpg"
        if os.path.exists(flappy_bg_path):
            game.flappy_background = pygame.image.load(flappy_bg_path)
            w, h = game.screen.get_size()
            game.flappy_background = pygame.transform.scale(game.flappy_background, (w, h))
    except Exception:
        game.flappy_background = None


def load_mango_sprites(game):
    """Load Mango sprite images into the game instance.

    This is a near-copy of the original helper but adjusted to reference the
    passed-in `game` object. It leaves the same fallbacks and printing so the
    runtime behavior is unchanged.
    """
    game.mango_sprites = {}

    sprite_files = {
        'idle': 'mango_idle.png',
        'happy': 'mango_happy.png',
        'sad': 'mango_sad.png',
        'tired': 'mango_tired.png',
        'dirty': 'mango_dirty.png',
        'flying': 'mango_flying.png',
    }

    def load_and_prepare(path, size=(100, 100)):
        # Prefer PIL if available for better resizing/alpha handling, otherwise use pygame directly
        if PIL_AVAILABLE and Image is not None:
            try:
                img = Image.open(path).convert('RGBA')

                # Trim fully-transparent borders if present
                bbox = img.split()[-1].getbbox()
                if bbox:
                    img = img.crop(bbox)

                # Resize preserving aspect into a square canvas
                img.thumbnail(size, Image.LANCZOS)
                canvas = Image.new('RGBA', size, (0, 0, 0, 0))
                x = (size[0] - img.width) // 2
                y = (size[1] - img.height) // 2
                canvas.paste(img, (x, y), img)

                # Boost alpha if the sprite is accidentally faint
                try:
                    alpha = canvas.split()[-1]
                    avg = sum(alpha.getdata()) / (size[0] * size[1])
                    if avg < 60:
                        def boost(a):
                            return min(255, int(a * 1.6))
                        alpha = alpha.point(boost)
                        canvas.putalpha(alpha)
                except Exception:
                    pass

                data = canvas.tobytes()
                surf = pygame.image.fromstring(data, size, 'RGBA')
                return surf.convert_alpha()
            except Exception:
                # Fall through to pygame loader
                pass

        # PIL not available or failed; use pygame loader
        try:
            s = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(s, size)
        except Exception:
            return None

    for mood, filename in sprite_files.items():
        try:
            sprite_path = f"assets/sprites/{filename}"
            if os.path.exists(sprite_path):
                game.mango_sprites[mood] = load_and_prepare(sprite_path, (100, 100))
                print(f"Loaded sprite: {filename}")
            else:
                game.mango_sprites[mood] = None
                print(f"Sprite not found: {filename}")
        except Exception as e:
            game.mango_sprites[mood] = None
            print(f"Error loading sprite {filename}: {e}")

    # Process alternate flying sprite specially for flappy game
    flying2_path = "assets/sprites/mango_flying2.png"
    try:
        if os.path.exists(flying2_path):
            s2 = load_and_prepare(flying2_path, (100, 100))
            if s2:
                game.mango_sprites['flying2'] = s2
                print("Loaded sprite: mango_flying2.png (processed)")
            else:
                game.mango_sprites['flying2'] = game.mango_sprites.get('flying')
        else:
            game.mango_sprites['flying2'] = game.mango_sprites.get('flying')
    except Exception as e:
        game.mango_sprites['flying2'] = game.mango_sprites.get('flying')
        print(f"Error loading flying2 sprite: {e}")

    # Ensure keys exist even if None
    if 'flying' not in game.mango_sprites:
        game.mango_sprites['flying'] = None
    if 'flying2' not in game.mango_sprites:
        game.mango_sprites['flying2'] = None

    # Load tree texture for flappy obstacles if available
    game.tree_texture = None
    tree_path = "assets/sprites/tree.png"
    try:
        if os.path.exists(tree_path):
            try:
                img = pygame.image.load(tree_path).convert_alpha()
                game.tree_texture = img
                print("Loaded tree texture for obstacles: tree.png")
            except Exception as e:
                print(f"Error loading tree texture: {e}")
    except Exception:
        pass

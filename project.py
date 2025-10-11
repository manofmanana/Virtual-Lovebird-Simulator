"""
Mango: The Virtual Lovebird - CS50P Final Project v2.0
A modern Tamagotchi-inspired virtual pet game featuring Mango the lovebird.
Enhanced with real-world APIs and beautiful UI.
"""

import pygame
# Some modules may not be available in the WASM/pygbag environment; import defensively
try:
    import sqlite3
    SQLITE_AVAILABLE = True
except Exception:
    sqlite3 = None
    SQLITE_AVAILABLE = False

import random
import time
try:
    import requests
    REQUESTS_AVAILABLE = True
except Exception:
    requests = None
    REQUESTS_AVAILABLE = False

import json
from datetime import datetime, timedelta
import sys
import os
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except Exception:
    Image = None
    ImageDraw = None
    PIL_AVAILABLE = False

import math
import wave
import struct

# Pre-initialize the mixer for more reliable audio behavior on different platforms
# Use common settings: 44100 Hz, 16-bit signed, stereo, small buffer
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
except Exception:
    pass

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60

# If running under pygbag / web, prefer the actual display surface size to
# avoid letterboxing / horizontal bars caused by mismatched canvas sizes.
try:
    import sys
    if hasattr(sys, '_emscripten_info'):
        try:
            # pygame.display.Info() should report the real canvas size in web builds
            info = pygame.display.Info()
            if info.current_w and info.current_h:
                SCREEN_WIDTH = info.current_w
                SCREEN_HEIGHT = info.current_h
        except Exception:
            # ignore and keep defaults
            pass
except Exception:
    pass

# Modern Color Palette
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
TEAL = (0, 150, 136)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (25, 25, 112)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
LIGHT_ORANGE = (255, 223, 190)

# Gradient Colors
GRADIENT_START = (135, 206, 235)  # Sky blue
GRADIENT_END = (70, 130, 180)     # Steel blue
NIGHT_START = (25, 25, 112)       # Midnight blue
NIGHT_END = (72, 61, 139)         # Dark slate blue

# Game states
class GameState:
    MAIN_MENU = "main_menu"
    TAMAGOTCHI_HUB = "tamagotchi_hub"
    FLAPPY_MANGO = "flappy_mango"
    GAME_OVER = "game_over"

try:
    from api import APIHandler
except Exception:
    # Fallback to minimal inline implementation if the module isn't available
    class APIHandler:
        def __init__(self):
            self.weather_data = None
            self.bird_fact = None
            self.last_weather_update = 0
            self.last_bird_fact_update = 0
            self.weather_update_interval = 1800
            self.bird_fact_update_interval = 3600
        def get_weather(self):
            return {'temperature': 20, 'condition': 'sunny', 'description': 'Sunny weather, 20°C'}
        def get_bird_fact(self):
            return 'Birds are amazing creatures!'
        def get_weather_mood_effect(self):
            return 0

class MangoTamagotchi:
    def __init__(self):
        # Create the real display surface and a fixed-size logical surface
        # Use browser-friendly display flags when available (pygame.SCALED)
        try:
            flags = pygame.SCALED if hasattr(pygame, 'SCALED') else 0
        except Exception:
            flags = 0
        self._display_screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Mango: The Virtual Lovebird v2.0")
        
        # For pygbag/web, use the display surface directly as the screen
        # For desktop, keep the separate logical surface for better scaling
        try:
            # Check if we're running in a web environment (pygbag)
            import sys
            if hasattr(sys, '_emscripten_info') or 'pygbag' in str(type(self._display_screen)):
                # In pygbag, draw directly to the display surface
                self.screen = self._display_screen
            else:
                # Desktop: use separate logical surface
                self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception:
            # Fallback: use separate surface
            self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            
        self.clock = pygame.time.Clock()
        # Fullscreen tracking: starts windowed, can be toggled at runtime
        self.fullscreen = False
        self._windowed_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Modern fonts
        try:
            self.title_font = pygame.font.Font(None, 48)
            self.large_font = pygame.font.Font(None, 32)
            self.font = pygame.font.Font(None, 28)
            self.small_font = pygame.font.Font(None, 20)
            self.tiny_font = pygame.font.Font(None, 16)
        except:
            self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
            self.large_font = pygame.font.SysFont('Arial', 32)
            self.font = pygame.font.SysFont('Arial', 28)
            self.small_font = pygame.font.SysFont('Arial', 20)
            self.tiny_font = pygame.font.SysFont('Arial', 16)
        
        self.state = GameState.TAMAGOTCHI_HUB
        self.db_path = "db/mango.db"
        
        # Initialize API handler
        self.api_handler = APIHandler()
        
        # UI animation variables
        self.animation_time = 0
        self.button_hover = {}
        self.pulse_animation = 0
        # Particle system for UI feedback (optional)
        try:
            from particle_effects import ParticleSystem
            self.particle_system = ParticleSystem()
        except Exception:
            self.particle_system = None
        # Audio volume controls (raised so sounds are audible by default)
        self.master_volume = 0.9
        self.sfx_volume = 0.9
        self.music_volume = 0.6
        # Do not start Flappy audio here during construction; defaults only
        self._force_short_flap_in_flappy = False
        # SFX visual indicator (last played SFX event)
        self._last_sfx_event = None
        
        # Game variables
        self.last_stat_update = time.time()
        self.last_random_event = time.time()
        self.is_sick = False
        self.misbehavior_count = 0
        self.high_score = self.get_high_score()
        
        # Day/night cycle
        self.current_hour = datetime.now().hour
        self.is_night = self.current_hour < 6 or self.current_hour > 18

        # Initialize database and load or create Mango's state
        try:
            self.init_database()
        except Exception:
            pass

        try:
            self.mango_state = self.load_state()
            if not self.mango_state:
                # create default state
                self.mango_state = {
                    'hunger': 80,
                    'happiness': 70,
                    'cleanliness': 60,
                    'energy': 90,
                    'health': 100,
                    'age': 0,
                    'last_updated': datetime.now().isoformat()
                }
                try:
                    self.save_state()
                except Exception:
                    pass
        except Exception:
            # ensure attribute exists even on failure
            self.mango_state = {
                'hunger': 80,
                'happiness': 70,
                'cleanliness': 60,
                'energy': 90,
                'health': 100,
                'age': 0,
                'last_updated': datetime.now().isoformat()
            }

        # Load background images and sprites
        try:
            self.load_background_images()
        except Exception:
            pass
        try:
            self.load_mango_sprites()
        except Exception:
            pass

        # Audio manager: encapsulate mixer, sounds, channels and helpers
        try:
            from audio import AudioManager
            self.audio = AudioManager(self)
            # mirror sounds dict for compatibility with rest of code
            self.sounds = self.audio.sounds
            # load/create sounds and channels
            try:
                self.audio.load_sounds()
            except Exception:
                pass
        except Exception:
            # fallback: keep old loader present but empty
            self.sounds = {}
        # Track whether music has been started by a real user action (browsers block autoplay)
        self._music_started = False

        # music start flag: set when user has interacted (browsers block autoplay)
        self._music_started = False

        # HUD messages and screen flash timer
        self.hud_messages = []  # list of (text, expiry_timestamp)
        self.flash_until = 0.0

        # Fade configuration (smaller/faster defaults for snappier transitions)
        # You can tune these at runtime via game.fade_steps / game.fade_delay_ms
        self.fade_steps = 8
        self.fade_delay_ms = 10
        
    def init_database(self):
        """Initialize the SQLite database with schema."""
        try:
            # Delegate to db helper for clarity
            from db import init_database as _init_db
            _init_db(self.db_path, schema_path='schema.sql')
        except Exception:
            # fallback to original inline behavior if helper unavailable
            try:
                os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                with open('schema.sql', 'r') as f:
                    schema = f.read()
                    cursor.executescript(schema)
                conn.commit()
                conn.close()
            except Exception:
                pass
    
    def save_state(self):
        """Save Mango's current state to database."""
        try:
            from db import save_state as _save_state
            _save_state(self.db_path, self.mango_state)
        except Exception:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM mango_state")
                cursor.execute(
                    """
                    INSERT INTO mango_state 
                    (hunger, happiness, cleanliness, energy, health, age, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.mango_state['hunger'],
                        self.mango_state['happiness'],
                        self.mango_state['cleanliness'],
                        self.mango_state['energy'],
                        self.mango_state['health'],
                        self.mango_state['age'],
                        datetime.now().isoformat(),
                    ),
                )
                conn.commit()
                conn.close()
            except Exception:
                pass
    
    def load_state(self):
        """Load Mango's state from database."""
        try:
            from db import load_state as _load_state
            return _load_state(self.db_path)
        except Exception:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM mango_state ORDER BY id DESC LIMIT 1")
                result = cursor.fetchone()
                conn.close()
                if result:
                    return {
                        'hunger': result[1],
                        'happiness': result[2],
                        'cleanliness': result[3],
                        'energy': result[4],
                        'health': result[5],
                        'age': result[6],
                        'last_updated': result[7]
                    }
            except Exception:
                pass
        return None
    
    def feed_mango(self):
        """Feed Mango to increase hunger."""
        if self.mango_state['hunger'] < 100:
            self.mango_state['hunger'] = min(100, self.mango_state['hunger'] + 25)
            self.mango_state['happiness'] = min(100, self.mango_state['happiness'] + 5)
            self.save_state()
            return True
        return False
    
    def bathe_mango(self):
        """Bathe Mango to increase cleanliness."""
        if self.mango_state['cleanliness'] < 100:
            self.mango_state['cleanliness'] = min(100, self.mango_state['cleanliness'] + 30)
            self.mango_state['happiness'] = min(100, self.mango_state['happiness'] + 10)
            self.save_state()
            return True
        return False
    
    def play_with_mango(self):
        """Play with Mango to increase happiness."""
        if self.mango_state['energy'] > 10:
            self.mango_state['happiness'] = min(100, self.mango_state['happiness'] + 20)
            self.mango_state['energy'] = max(0, self.mango_state['energy'] - 15)
            self.save_state()
            return True
        return False
    
    def rest_mango(self):
        """Let Mango rest to restore energy."""
        if self.mango_state['energy'] < 100:
            self.mango_state['energy'] = min(100, self.mango_state['energy'] + 30)
            self.save_state()
            return True
        return False
    
    def give_medicine(self):
        """Give medicine to heal Mango."""
        # Give medicine and fully restore health to 100
        # Medicine can now be given regardless of sickness state
        self.mango_state['health'] = 100
        self.is_sick = False

        for k in ('hunger', 'cleanliness', 'energy'):
            if self.mango_state[k] < 25:
                self.mango_state[k] = 25

        self.last_stat_update = time.time()

        # Play medicine sound if available (non-fatal)
        try:
            # delegate to AudioManager for consistent behavior
            try:
                self._play_sfx('medicine')
            except Exception:
                if 'medicine' in self.sounds:
                    try:
                        self.sounds['medicine'].play()
                    except Exception:
                        pass
        except Exception:
            pass

        # HUD message and soft flash for feedback
        self.hud_messages.append(("Medicine used!", time.time() + 2.0))
        self.flash_until = time.time() + 0.25

        self.save_state()
        return True

    def discipline(self):
        """Start the tickle minigame (replaces old discipline action)."""
        try:
            from tickle_minigame import play_tickle_minigame as _play
            return _play(self, GameState.TAMAGOTCHI_HUB, GameState.TAMAGOTCHI_HUB)
        except Exception:
            # Fallback to legacy discipline behavior
            try:
                if self.misbehavior_count > 0:
                    self.misbehavior_count = max(0, self.misbehavior_count - 1)
                    self.mango_state['happiness'] = max(0, self.mango_state['happiness'] - 5)
                    self.save_state()
                    return True
            except Exception:
                pass
        return False
    
    def age_mango(self):
        """Age Mango based on time passed."""
        current_time = datetime.now()
        last_updated = datetime.fromisoformat(self.mango_state['last_updated'])
        hours_passed = (current_time - last_updated).total_seconds() / 3600
        
        # Age Mango every 24 hours
        if hours_passed >= 24:
            self.mango_state['age'] += 1
            self.mango_state['last_updated'] = current_time.isoformat()
            self.save_state()
    
    def update_stats(self):
        """Update Mango's stats over time."""
        current_time = time.time()
        time_diff = current_time - self.last_stat_update
        
        # Update stats every 30 seconds (tests use ~35s) for quicker decay in game/testing
        if time_diff >= 30:
            # Natural decay (much slower)
            self.mango_state['hunger'] = max(0, self.mango_state['hunger'] - 1)
            self.mango_state['happiness'] = max(0, self.mango_state['happiness'] - 1)
            self.mango_state['cleanliness'] = max(0, self.mango_state['cleanliness'] - 1)
            self.mango_state['energy'] = max(0, self.mango_state['energy'] - 1)
            
            # Weather effects on mood (apply only negative effects here so
            # natural decay always results in same-or-lower happiness; positive
            # weather bonuses are omitted to keep auto-decay deterministic.)
            weather_mood = self.api_handler.get_weather_mood_effect() or 0
            if weather_mood < 0:
                self.mango_state['happiness'] = max(0, min(100,
                    self.mango_state['happiness'] + weather_mood))
            
            # Health decreases if other stats are too low
            if (self.mango_state['hunger'] <= 10 or 
                self.mango_state['cleanliness'] <= 10 or 
                self.mango_state['energy'] <= 10):
                self.mango_state['health'] = max(0, self.mango_state['health'] - 3)
            # 👉 New: if health gets critically low, Mango becomes sick
            if self.mango_state['health'] <= 30 and not self.is_sick:
                self.is_sick = True
            
            # Check for random events
            self.check_random_events()
            
            self.last_stat_update = current_time
            self.save_state()

    def _apply_volume_settings(self):
        """Apply current master/music/sfx volume settings to mixer and loaded sounds."""
        try:
            if pygame.mixer.get_init():
                try:
                    pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
                except Exception:
                    pass
            # apply to loaded sounds
            for s in list(self.sounds.keys()):
                try:
                    if self.sounds.get(s):
                        self.sounds[s].set_volume(self.sfx_volume * self.master_volume)
                except Exception:
                    pass

            # Also apply to any dedicated channels we created
            try:
                for k, ch in getattr(self, '_sfx_channels', {}).items():
                    if ch:
                        try:
                            ch.set_volume(self.sfx_volume * self.master_volume)
                        except Exception:
                            pass
            except Exception:
                pass
        except Exception:
            pass


    def _ensure_audio_ready(self):
        """Delegates to AudioManager.ensure_audio_ready if available."""
        try:
            if getattr(self, 'audio', None):
                return self.audio.ensure_audio_ready()
        except Exception:
            pass
        return False

    def _write_short_tone(self, path, freq=1500, duration_ms=160, volume=1.0):
        try:
            if getattr(self, 'audio', None):
                return self.audio.write_short_tone(path, freq=freq, duration_ms=duration_ms, volume=volume)
        except Exception:
            pass
        return False

    def _write_thump(self, path, duration_ms=220, volume=0.9):
        try:
            if getattr(self, 'audio', None):
                return self.audio.write_thump(path, duration_ms=duration_ms, volume=volume)
        except Exception:
            pass
        return False
    
    def load_background_images(self):
        """Load background images for hub and flappy mango."""
        try:
            from assets import load_background_images as _load_bg
            _load_bg(self)
        except Exception:
            # fallback to inline loader
            self.hub_background = None
            self.flappy_background = None
            try:
                hub_bg_path = "assets/backgrounds/hub_bg.jpg"
                if os.path.exists(hub_bg_path):
                    self.hub_background = pygame.image.load(hub_bg_path)
                    self.hub_background = pygame.transform.scale(self.hub_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception:
                self.hub_background = None
            try:
                flappy_bg_path = "assets/backgrounds/flappy_bg.jpg"
                if os.path.exists(flappy_bg_path):
                    self.flappy_background = pygame.image.load(flappy_bg_path)
                    self.flappy_background = pygame.transform.scale(self.flappy_background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except Exception:
                self.flappy_background = None
    
    def load_mango_sprites(self):
        """Load Mango sprite images."""
        try:
            from assets import load_mango_sprites as _load_sprites
            _load_sprites(self)
        except Exception:
            # fallback to original inline loader if helper unavailable
            self.mango_sprites = {}
            sprite_files = {
                'idle': 'mango_idle.png',
                'happy': 'mango_happy.png',
                'sad': 'mango_sad.png',
                'tired': 'mango_tired.png',
                'dirty': 'mango_dirty.png',
                'flying': 'mango_flying.png',
            }

            def load_and_prepare(path, size=(100, 100)):
                try:
                    img = Image.open(path).convert('RGBA')
                    bbox = img.split()[-1].getbbox()
                    if bbox:
                        img = img.crop(bbox)
                    img.thumbnail(size, Image.LANCZOS)
                    canvas = Image.new('RGBA', size, (0, 0, 0, 0))
                    x = (size[0] - img.width) // 2
                    y = (size[1] - img.height) // 2
                    canvas.paste(img, (x, y), img)
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
                    try:
                        s = pygame.image.load(path).convert_alpha()
                        return pygame.transform.smoothscale(s, size)
                    except Exception:
                        return None

            for mood, filename in sprite_files.items():
                try:
                    sprite_path = f"assets/sprites/{filename}"
                    if os.path.exists(sprite_path):
                        self.mango_sprites[mood] = load_and_prepare(sprite_path, (100, 100))
                        print(f"Loaded sprite: {filename}")
                    else:
                        self.mango_sprites[mood] = None
                        print(f"Sprite not found: {filename}")
                except Exception as e:
                    self.mango_sprites[mood] = None
                    print(f"Error loading sprite {filename}: {e}")

            flying2_path = "assets/sprites/mango_flying2.png"
            try:
                if os.path.exists(flying2_path):
                    s2 = load_and_prepare(flying2_path, (100, 100))
                    if s2:
                        self.mango_sprites['flying2'] = s2
                        print("Loaded sprite: mango_flying2.png (processed)")
                    else:
                        self.mango_sprites['flying2'] = self.mango_sprites.get('flying')
                else:
                    self.mango_sprites['flying2'] = self.mango_sprites.get('flying')
            except Exception as e:
                self.mango_sprites['flying2'] = self.mango_sprites.get('flying')
                print(f"Error loading flying2 sprite: {e}")

            if 'flying' not in self.mango_sprites:
                self.mango_sprites['flying'] = None
            if 'flying2' not in self.mango_sprites:
                self.mango_sprites['flying2'] = None

            self.tree_texture = None
            tree_path = "assets/sprites/tree.png"
            try:
                if os.path.exists(tree_path):
                    try:
                        img = pygame.image.load(tree_path).convert_alpha()
                        self.tree_texture = img
                        print("Loaded tree texture for obstacles: tree.png")
                    except Exception as e:
                        print(f"Error loading tree texture: {e}")
            except Exception:
                pass

    def load_mango_sounds(self):
        """Load optional Mango sounds (non-fatal if missing).

        Looks for assets/sounds/flap.wav and assets/sounds/medicine.wav.
        If loading fails (no mixer or missing files), stores nothing but
        keeps code paths safe.
        """
        # Delegated to AudioManager; kept for backward compatibility.
        try:
            if getattr(self, 'audio', None):
                return self.audio.load_sounds()
        except Exception:
            pass
        return None
    def _play_music(self, key):
        try:
            if getattr(self, 'audio', None):
                return self.audio.play_music(key)
        except Exception:
            pass
        return None

    def _stop_music(self):
        try:
            if getattr(self, 'audio', None):
                return self.audio.stop_music()
        except Exception:
            pass
        return None

    def _play_sfx(self, key, maxtime=None):
        """Safely play a short sound effect by key from self.sounds. Optionally limit duration (ms)."""
        try:
            if getattr(self, 'audio', None):
                return self.audio.play_sfx(key, maxtime=maxtime)
        except Exception:
            pass
        return None

    def start_music(self, key='home'):
        """Start background music in a user-initiated way.

        Browsers block autoplay; call this from the first user click to allow audio.
        """
        try:
            if getattr(self, '_music_started', False):
                return
            # Try to play the requested music key; fallbacks handled by AudioManager
            try:
                self._play_music(key)
            except Exception:
                pass
            try:
                self._music_started = True
            except Exception:
                pass
        except Exception:
            pass

    def start_music(self):
        """Mark that the user interacted and allow music to start.

        Call this from the first user input (mouse click) so browsers
        don't block audio autoplay. If we're in the hub, start the
        hub music immediately.
        """
        try:
            if getattr(self, '_music_started', False):
                return
            self._music_started = True
            # If any music was queued by a mini-game while waiting for user input,
            # play that instead; otherwise start hub/home music if we're in the hub.
            try:
                queued = getattr(self, '_queued_music', None)
                if queued:
                    try:
                        self._play_music(queued)
                    except Exception:
                        pass
                    # start watchdog if supported (forest uses watchdog)
                    try:
                        if getattr(self, 'audio', None) and queued:
                            try:
                                self.audio.start_watchdog(queued)
                            except Exception:
                                pass
                    except Exception:
                        pass
                    # clear queued music
                    try:
                        del self._queued_music
                    except Exception:
                        pass
                else:
                    try:
                        if self.state == GameState.TAMAGOTCHI_HUB:
                            try:
                                self._play_music('home')
                            except Exception:
                                pass
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass

    def _play_debug_tone(self, freq=800, duration_ms=300, volume=1.0):
        """Play a short loud debug tone via mixer to test output path immediately."""
        try:
            if getattr(self, 'audio', None):
                return self.audio.play_debug_tone(freq=freq, duration_ms=duration_ms, volume=volume)
        except Exception:
            pass
        return None
    
    
    def draw_gradient_background(self):
        """Draw a beautiful gradient background."""
        if self.is_night:
            start_color = NIGHT_START
            end_color = NIGHT_END
        else:
            start_color = GRADIENT_START
            end_color = GRADIENT_END
        
        for y in range(SCREEN_HEIGHT):
            ratio = y / SCREEN_HEIGHT
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    def draw_hub_background(self):
        """Draw the hub background (image or gradient)."""
        if self.hub_background:
            self.screen.blit(self.hub_background, (0, 0))
            # Add a slight overlay for better text readability
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(30)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
        else:
            self.draw_gradient_background()
    
    def draw_flappy_background(self):
        """Draw the flappy mango background (image or gradient)."""
        if self.flappy_background:
            self.screen.blit(self.flappy_background, (0, 0))
        else:
            self.draw_gradient_background()
    
    def draw_modern_button(self, rect, text, color, hover_color, text_color=WHITE, hover=False):
        try:
            from ui_helpers import draw_modern_button as _dmb
            return _dmb(self, rect, text, color, hover_color, text_color, hover)
        except Exception:
            # Keep a lightweight fallback to avoid breaking runtime during transition
            try:
                shadow_rect = rect.copy()
                shadow_rect.x += 3
                shadow_rect.y += 3
                pygame.draw.rect(self.screen, (0, 0, 0, 50), shadow_rect, border_radius=8)
            except Exception:
                pass
            button_color = hover_color if hover else color
            try:
                pygame.draw.rect(self.screen, button_color, rect, border_radius=8)
            except Exception:
                pass
            try:
                border_color = WHITE if hover else LIGHT_GRAY
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=8)
            except Exception:
                pass
            try:
                text_surface = self.small_font.render(text, True, text_color)
                text_rect = text_surface.get_rect(center=rect.center)
                self.screen.blit(text_surface, text_rect)
            except Exception:
                pass
            return rect
    
    def draw_modern_progress_bar(self, x, y, width, height, value, max_value, color, bg_color=DARK_GRAY):
        try:
            from ui_helpers import draw_modern_progress_bar as _dmpb
            return _dmpb(self, x, y, width, height, value, max_value, color, bg_color)
        except Exception:
            # Lightweight fallback for transition
            try:
                bg_rect = pygame.Rect(x, y, width, height)
                pygame.draw.rect(self.screen, bg_color, bg_rect, border_radius=max(1, height//2))
                progress_width = int((value / float(max_value)) * width) if max_value else 0
                if progress_width > 0:
                    progress_rect = pygame.Rect(x, y, progress_width, height)
                    pygame.draw.rect(self.screen, color, progress_rect, border_radius=max(1, height//2))
                pygame.draw.rect(self.screen, WHITE, bg_rect, 2, border_radius=max(1, height//2))
            except Exception:
                pass
    
    def check_random_events(self):
        """Check for random events like sickness or misbehavior."""
        current_time = time.time()
        time_diff = current_time - self.last_random_event
        
        # Random events every 2 minutes
        if time_diff >= 120:
            if random.random() < 0.3:  # 30% chance
                event = random.choice(['sick', 'misbehavior'])
                if event == 'sick' and not self.is_sick:
                    self.is_sick = True
                    self.mango_state['health'] = max(0, self.mango_state['health'] - 20)
                elif event == 'misbehavior':
                    self.misbehavior_count += 1
                    self.mango_state['happiness'] = max(0, self.mango_state['happiness'] - 10)
            
            self.last_random_event = current_time
    
    def get_mango_mood(self):
        """Determine Mango's current mood based on stats."""
        if self.is_sick:
            return "sick"
        elif self.mango_state['cleanliness'] < 30:
            return "dirty"
        elif self.mango_state['energy'] < 20:
            return "tired"
        elif self.mango_state['happiness'] > 70:
            return "happy"
        elif self.mango_state['happiness'] < 30:
            return "sad"
        else:
            return "neutral"
    
    def is_game_over(self):
        """Check if game is over (health = 0)."""
        return self.mango_state['health'] <= 0
    
    def restart_game(self):
        """Restart the game with a new Mango."""
        self.mango_state = {
            'hunger': 80,
            'happiness': 70,
            'cleanliness': 60,
            'energy': 90,
            'health': 100,
            'age': 0,
            'last_updated': datetime.now().isoformat()
        }
        self.is_sick = False
        self.misbehavior_count = 0
        self.save_state()
    
    def save_score(self, score):
        """Save Flappy Mango score to database."""
        try:
            from db import save_score as _save_score
            try:
                _save_score(self.db_path, score)
            except Exception:
                pass
        except Exception:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO scores (score) VALUES (?)", (score,))
                conn.commit()
                conn.close()
            except Exception:
                pass
        # Update high score
        try:
            if score > self.high_score:
                self.high_score = score
        except Exception:
            pass
    
    def get_high_score(self):
        """Get the highest score from database."""
        try:
            from db import get_high_score as _get_high
            try:
                return int(_get_high(self.db_path) or 0)
            except Exception:
                return 0
        except Exception:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(score) FROM scores")
                result = cursor.fetchone()
                conn.close()
                return result[0] if result and result[0] else 0
            except Exception:
                return 0
    
    def play_flappy_mango(self):
        """Delegate to the Flappy mini-game implementation in flappy.py.

        The full Flappy logic was moved to a separate module to keep project.py small.
        We pass `self` so the flappy module can call back into game helpers.
        """
        # Directly delegate to the flappy module. Let exceptions surface so
        # they are easier to diagnose during development rather than silently
        # falling back to legacy behavior.
        from flappy import play_flappy_mango as _play
        return _play(self, GameState.FLAPPY_MANGO, GameState.TAMAGOTCHI_HUB)

    def play_feed_minigame(self):
        """Delegate to feed_minigame.play_feed_minigame."""
        from feed_minigame import play_feed_minigame as _play
        return _play(self, GameState.TAMAGOTCHI_HUB, GameState.TAMAGOTCHI_HUB)
    
    def draw_home_screen(self):
        # Delegate fully to the hub_ui module which owns hub rendering.
        from hub_ui import draw_home_screen as _dh
        return _dh(self)
    
    def handle_click(self, pos):
        """Delegate hub click handling to hub_ui.handle_click."""
        from hub_ui import handle_click as _hc
        return _hc(self, pos)
    
    async def run(self):
        """Main game loop."""
        running = True
        
        while running:
            # Compute logical mouse position from display coords for scaled rendering
            try:
                disp = getattr(self, '_display_screen', None)
                disp_w, disp_h = disp.get_size() if disp else (self.screen.get_width(), self.screen.get_height())
            except Exception:
                disp_w, disp_h = (self.screen.get_width(), self.screen.get_height())
            try:
                logical_w, logical_h = self.screen.get_size()
            except Exception:
                logical_w, logical_h = (SCREEN_WIDTH, SCREEN_HEIGHT)

            # store logical mouse pos on the game instance for UI modules to use
            try:
                mx_disp, my_disp = pygame.mouse.get_pos()
                if disp_w and disp_h:
                    mx_log = int(mx_disp * logical_w / float(disp_w))
                    my_log = int(my_disp * logical_h / float(disp_h))
                else:
                    mx_log, my_log = mx_disp, my_disp
                self._mouse_pos_logical = (mx_log, my_log)
            except Exception:
                self._mouse_pos_logical = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        # map display coords to logical coords before handling
                        try:
                            px, py = event.pos
                            if disp_w and disp_h:
                                lx = int(px * logical_w / float(disp_w))
                                ly = int(py * logical_h / float(disp_h))
                            else:
                                lx, ly = px, py
                            self.handle_click((lx, ly))
                        except Exception:
                            self.handle_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    try:
                        mx, my = event.pos
                        # convert to logical coords for slider dragging
                        try:
                            if disp_w and disp_h:
                                mx = int(mx * logical_w / float(disp_w))
                                my = int(my * logical_h / float(disp_h))
                        except Exception:
                            pass
                        for key, meta in self._audio_sliders.items():
                            if meta.get('dragging') and meta.get('rect'):
                                r = meta['rect']
                                rel = (mx - r.x) / float(r.w)
                                val = max(0.0, min(1.0, rel))
                                if key == 'master':
                                    self.master_volume = val
                                elif key == 'music':
                                    self.music_volume = val
                                elif key == 'sfx':
                                    self.sfx_volume = val
                                # apply volumes live
                                try:
                                    pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
                                except Exception:
                                    pass
                                try:
                                    for s in ['flap', 'medicine', 'button', 'chirp', 'thump']:
                                        if s in self.sounds and self.sounds[s]:
                                            try:
                                                self.sounds[s].set_volume(self.sfx_volume * self.master_volume)
                                            except Exception:
                                                pass
                                except Exception:
                                    pass
                    except Exception:
                        pass
                elif event.type == pygame.MOUSEBUTTONUP:
                    try:
                        if event.button == 1:
                            # stop any dragging and persist settings
                            changed = False
                            for key, meta in self._audio_sliders.items():
                                if meta.get('dragging'):
                                    meta['dragging'] = False
                                    changed = True
                            if changed:
                                import json as _json
                                with open(self._settings_path, 'w') as _f:
                                    _json.dump({'master_volume': self.master_volume, 'music_volume': self.music_volume, 'sfx_volume': self.sfx_volume}, _f)
                    except Exception:
                        pass
                elif event.type == pygame.KEYDOWN:
                    # Fullscreen toggles: F11 or Alt+Enter
                    try:
                        if event.key == pygame.K_F11:
                            self.toggle_fullscreen()
                            continue
                        if event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT):
                            self.toggle_fullscreen()
                            continue
                    except Exception:
                        pass
                    # Developer audio self-test: press T in the hub to play all SFX/music
                    if event.key == pygame.K_t and self.state == GameState.TAMAGOTCHI_HUB:
                        try:
                            print("Audio self-test: playing flap, button, medicine, chirp, starting/stopping music...")
                            if 'flap' in self.sounds:
                                self._play_sfx('flap')
                                pygame.time.delay(300)
                            if 'button' in self.sounds:
                                self._play_sfx('button')
                                pygame.time.delay(300)
                            if 'medicine' in self.sounds:
                                self._play_sfx('medicine')
                                pygame.time.delay(400)
                            if 'chirp' in self.sounds:
                                self._play_sfx('chirp')
                                pygame.time.delay(300)
                            # Play home music briefly then switch to forest
                            self._play_music('home')
                            pygame.time.delay(800)
                            self._play_music('forest')
                            pygame.time.delay(800)
                            self._stop_music()
                            print("Audio self-test complete.")
                        except Exception as e:
                            print(f"Audio self-test failed: {e}")
                        continue
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # Update game state
            self.update_stats()
            self.age_mango()
            
            # Force sickness if health is low (real-time check)
            if self.mango_state['health'] <= 30 and not self.is_sick:
                self.is_sick = True
            
            # Update day/night cycle
            current_hour = datetime.now().hour
            if current_hour != self.current_hour:
                self.current_hour = current_hour
                self.is_night = current_hour < 6 or current_hour > 18
            
            # Check game over
            if self.is_game_over():
                self.state = GameState.GAME_OVER

            # Update particle system
            try:
                if getattr(self, 'particle_system', None):
                    self.particle_system.update(1.0 / float(FPS))
            except Exception:
                pass

            # Advance a simple animation timer used by UI modules
            try:
                self.animation_time += 1.0 / float(FPS)
            except Exception:
                pass

            # Draw current state
            if self.state == GameState.TAMAGOTCHI_HUB:
                self.draw_home_screen()
                # Draw particle overlays on top of hub UI
                try:
                    if getattr(self, 'particle_system', None):
                        self.particle_system.draw(self.screen)
                except Exception:
                    pass
            elif self.state == GameState.GAME_OVER:
                self.draw_game_over_screen()
            
            # Update display - simplified for pygbag compatibility
            try:
                # Check if we're using the display surface directly (pygbag)
                if self.screen is self._display_screen:
                    # Already drawing to display surface, just flip
                    pygame.display.flip()
                else:
                    # Desktop: scale logical surface to display
                    disp = getattr(self, '_display_screen', None)
                    if disp is not None:
                        # Smooth scale for nicer visuals when stretching
                        try:
                            scaled = pygame.transform.smoothscale(self.screen, disp.get_size())
                        except Exception:
                            scaled = pygame.transform.scale(self.screen, disp.get_size())
                        disp.blit(scaled, (0, 0))
                        pygame.display.flip()
                    else:
                        pygame.display.flip()
            except Exception:
                try:
                    pygame.display.flip()
                except Exception:
                    pass
            self.clock.tick(FPS)
            # Essential for pygbag - yield control to browser
            import asyncio
            try:
                await asyncio.sleep(0)
            except:
                pass
        
        try:
            pygame.quit()
        except Exception:
            pass
        # In embedded environments (pygbag) avoid calling sys.exit() which
        # can terminate the module import/execution unexpectedly. Return from
        # main instead and let the embedder handle process lifecycle.
            try:
                pygame.quit()
            except Exception:
                pass
            # Do not call sys.exit() here - returning lets the caller (or pygbag) cleanly
            # finish without forcibly exiting the process which can cause issues in WASM.
            return
    
    def draw_game_over_screen(self):
        """Delegate the game-over screen drawing to hub_ui.draw_game_over_screen."""
        from hub_ui import draw_game_over_screen as _dg
        return _dg(self)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode. Uses the display's current resolution for fullscreen.

        We reset the display surface and keep `self.screen` referencing the new surface
        so the rest of the code continues to use the correct size via `screen.get_width()`.
        """
        # Implement toggling with multiple fallbacks; return True on success
        try:
            # Smooth fade transition: fade out, change mode, fade in
            disp = getattr(self, '_display_screen', None)
            try:
                start_size = disp.get_size() if disp else (self._windowed_size[0], self._windowed_size[1])
            except Exception:
                start_size = (self._windowed_size[0], self._windowed_size[1])

            enter_fs = not getattr(self, 'fullscreen', False)

            steps = 10
            delay_ms = 16

            # fade out (best-effort)
            try:
                for i in range(steps):
                    alpha = int(255 * (i + 1) / float(steps))
                    try:
                        if disp is not None:
                            try:
                                scaled = pygame.transform.smoothscale(self.screen, disp.get_size())
                            except Exception:
                                scaled = pygame.transform.scale(self.screen, disp.get_size())
                            disp.blit(scaled, (0, 0))
                        overlay = pygame.Surface(start_size, pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, alpha))
                        if disp is not None:
                            try:
                                disp.blit(overlay, (0, 0))
                            except Exception:
                                pass
                            pygame.display.flip()
                        else:
                            try:
                                pygame.display.flip()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        pygame.time.delay(delay_ms)
                    except Exception:
                        pass
            except Exception:
                pass

            result = False
            if enter_fs:
                info = pygame.display.Info()
                w, h = info.current_w or self._windowed_size[0], info.current_h or self._windowed_size[1]
                try:
                    scaled_flag = getattr(pygame, 'SCALED', 0)
                except Exception:
                    scaled_flag = 0
                try:
                    fs_flag = getattr(pygame, 'FULLSCREEN', 0)
                except Exception:
                    fs_flag = 0
                # try the straightforward fullscreen first
                try:
                    self.hud_messages.append(("Entering fullscreen...", time.time() + 1.5))
                except Exception:
                    pass
                tried = False
                try:
                    self._display_screen = pygame.display.set_mode((w, h), fs_flag)
                    tried = True
                except Exception:
                    tried = False
                if not tried:
                    try:
                        hwflags = fs_flag
                        try:
                            hwflags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
                        except Exception:
                            hwflags = fs_flag
                        self._display_screen = pygame.display.set_mode((w, h), hwflags)
                        tried = True
                    except Exception:
                        tried = False
                if not tried:
                    try:
                        self._display_screen = pygame.display.set_mode((w, h))
                        tried = True
                    except Exception:
                        tried = False
                if not tried:
                    try:
                        pygame.display.toggle_fullscreen()
                        tried = True
                    except Exception:
                        tried = False
                self.fullscreen = True if tried else getattr(self, 'fullscreen', False)
                try:
                    if tried:
                        self.hud_messages.append(("Entered fullscreen", time.time() + 1.5))
                    else:
                        self.hud_messages.append(("Failed to enter fullscreen", time.time() + 1.5))
                except Exception:
                    pass
                result = bool(tried)
            else:
                # leaving fullscreen: try restoring windowed size
                try:
                    window_flags = getattr(pygame, 'SCALED', 0)
                except Exception:
                    window_flags = 0
                left_ok = False
                try:
                    self._display_screen = pygame.display.set_mode(tuple(self._windowed_size), window_flags)
                    left_ok = True
                except Exception:
                    try:
                        pygame.display.toggle_fullscreen()
                        left_ok = True
                    except Exception:
                        left_ok = False
                self.fullscreen = False if left_ok else getattr(self, 'fullscreen', True)
                try:
                    if left_ok:
                        self.hud_messages.append(("Exited fullscreen", time.time() + 1.5))
                    else:
                        self.hud_messages.append(("Failed to exit fullscreen", time.time() + 1.5))
                except Exception:
                    pass
                result = bool(left_ok)

            # fade in (best-effort)
            try:
                disp = getattr(self, '_display_screen', None)
                end_size = disp.get_size() if disp else start_size
            except Exception:
                end_size = start_size
            try:
                for i in range(steps):
                    alpha = int(255 * (1.0 - (i + 1) / float(steps)))
                    try:
                        if disp is not None:
                            try:
                                scaled = pygame.transform.smoothscale(self.screen, disp.get_size())
                            except Exception:
                                scaled = pygame.transform.scale(self.screen, disp.get_size())
                            disp.blit(scaled, (0, 0))
                        overlay = pygame.Surface(end_size, pygame.SRCALPHA)
                        overlay.fill((0, 0, 0, alpha))
                        if disp is not None:
                            try:
                                disp.blit(overlay, (0, 0))
                            except Exception:
                                pass
                            pygame.display.flip()
                        else:
                            try:
                                pygame.display.flip()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        pygame.time.delay(delay_ms)
                    except Exception:
                        pass
            except Exception:
                pass

            return result

        except Exception:
            try:
                pygame.display.toggle_fullscreen()
                self.fullscreen = not getattr(self, 'fullscreen', False)
            except Exception:
                pass
            return getattr(self, 'fullscreen', False)

    def fade_out(self, steps=None, delay_ms=None):
        """Fade the current logical screen out to black on the display."""
        if steps is None:
            steps = getattr(self, 'fade_steps', 12)
        if delay_ms is None:
            delay_ms = getattr(self, 'fade_delay_ms', 16)
        try:
            disp = getattr(self, '_display_screen', None)
            try:
                size = disp.get_size() if disp else (self.screen.get_width(), self.screen.get_height())
            except Exception:
                size = (self.screen.get_width(), self.screen.get_height())

            # Render the current logical screen once to the display, then overlay
            try:
                if disp is not None:
                    try:
                        scaled = pygame.transform.smoothscale(self.screen, disp.get_size())
                    except Exception:
                        scaled = pygame.transform.scale(self.screen, disp.get_size())
                    disp.blit(scaled, (0, 0))
                else:
                    # attempt to update display from logical surface as best-effort
                    try:
                        scaled = pygame.transform.smoothscale(self.screen, size)
                        pygame.display.get_surface().blit(scaled, (0, 0))
                    except Exception:
                        pass
                pygame.display.flip()
            except Exception:
                pass

            for i in range(steps):
                alpha = int(255 * (i + 1) / float(steps))
                try:
                    overlay = pygame.Surface(size, pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, alpha))
                    if disp is not None:
                        try:
                            disp.blit(overlay, (0, 0))
                        except Exception:
                            pass
                        pygame.display.flip()
                    else:
                        try:
                            pygame.display.flip()
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    pygame.time.delay(delay_ms)
                except Exception:
                    pass
        except Exception:
            pass

    def fade_in(self, steps=None, delay_ms=None):
        """Fade from black into the current logical screen on the display."""
        if steps is None:
            steps = getattr(self, 'fade_steps', 12)
        if delay_ms is None:
            delay_ms = getattr(self, 'fade_delay_ms', 16)
        try:
            disp = getattr(self, '_display_screen', None)
            try:
                size = disp.get_size() if disp else (self.screen.get_width(), self.screen.get_height())
            except Exception:
                size = (self.screen.get_width(), self.screen.get_height())

            # Start from a full-black screen then reveal the logical screen
            try:
                if disp is not None:
                    disp.fill((0, 0, 0))
                else:
                    try:
                        pygame.display.get_surface().fill((0, 0, 0))
                    except Exception:
                        pass
                pygame.display.flip()
            except Exception:
                pass

            # Pre-render scaled content once
            try:
                if disp is not None:
                    try:
                        scaled = pygame.transform.smoothscale(self.screen, disp.get_size())
                    except Exception:
                        scaled = pygame.transform.scale(self.screen, disp.get_size())
                else:
                    try:
                        scaled = pygame.transform.smoothscale(self.screen, size)
                    except Exception:
                        scaled = None
            except Exception:
                scaled = None

            for i in range(steps):
                alpha = int(255 * (1.0 - (i + 1) / float(steps)))
                try:
                    if disp is not None and scaled is not None:
                        disp.blit(scaled, (0, 0))
                    elif scaled is not None:
                        try:
                            pygame.display.get_surface().blit(scaled, (0, 0))
                        except Exception:
                            pass
                    overlay = pygame.Surface(size, pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, alpha))
                    if disp is not None:
                        try:
                            disp.blit(overlay, (0, 0))
                        except Exception:
                            pass
                        pygame.display.flip()
                    else:
                        try:
                            pygame.display.flip()
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    pygame.time.delay(delay_ms)
                except Exception:
                    pass
        except Exception:
            pass

    def present(self):
        """Scale the logical surface to the display and flip the buffer.

        Mini-games should call this instead of pygame.display.flip() so
        presentation is consistent whether windowed or fullscreen.
        """
        try:
            disp = getattr(self, '_display_screen', None)
            if disp is not None:
                try:
                    scaled = pygame.transform.smoothscale(self.screen, disp.get_size())
                except Exception:
                    scaled = pygame.transform.scale(self.screen, disp.get_size())
                disp.blit(scaled, (0, 0))
                pygame.display.flip()
                return
        except Exception:
            pass
        try:
            pygame.display.flip()
        except Exception:
            pass

    def safe_delay_ms(self, ms: int):
        """Delay for approximately ms milliseconds without blocking the
        Emscripten/WASM main thread.

        On web/pygbag builds we avoid calling blocking backends like
        pygame.time.delay() directly since that can stall the single-threaded
        event loop. Instead we pump events and tick the local clock in short
        chunks. On desktop builds we fall back to pygame.time.delay.
        """
        try:
            # Best-effort detection of web/pygbag environment
            import sys as _sys
            is_web = bool(getattr(_sys, '_emscripten_info', False) or 'pygbag' in _sys.modules or 'emscripten' in getattr(_sys, 'platform', ''))
        except Exception:
            is_web = False

        # If running on web, break the delay into small ticks so the
        # browser main loop can continue to service events and rendering.
        if is_web:
            # choose a safe chunk size (16ms ~= 60fps)
            chunk = 16
            remaining = int(ms)
            try:
                while remaining > 0:
                    try:
                        pygame.event.pump()
                    except Exception:
                        pass
                    try:
                        # tick a single frame to yield control and update timing
                        self.clock.tick(FPS)
                    except Exception:
                        pass
                    remaining -= chunk
            except Exception:
                # swallow failures and fall back to a blocking delay as last resort
                try:
                    pygame.time.delay(ms)
                except Exception:
                    pass
        else:
            try:
                pygame.time.delay(ms)
            except Exception:
                # ignore failures
                pass

def main():
    """Main function to run the game.

    If an asyncio event loop is already running (as in pygbag/web builds),
    schedule the main game coroutine on that loop. Otherwise, use
    asyncio.run() for a normal desktop run.
    """
    import asyncio
    game = MangoTamagotchi()

    # Use a straightforward run strategy: always invoke asyncio.run() so
    # the runtime controls the event loop lifecycle in the usual way.
    asyncio.run(game.run())

if __name__ == "__main__":
    main()
